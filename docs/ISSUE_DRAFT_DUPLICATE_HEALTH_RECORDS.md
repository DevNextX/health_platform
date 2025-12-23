---
title: "fix: Prevent duplicate health records for same member at same timestamp"
labels: "bug, data-integrity, health-records"
assignees: ""
---

## 问题描述 (Issue Description)

当前系统允许同一个成员在同一时间点（分钟级别）创建多条健康记录。这会导致数据重复，特别是在批量导入功能中，同一个Excel文件可以被重复上传多次，造成数据冗余。

**复现步骤**：
1. 手动创建一条健康记录（成员：Self，时间：2025-12-22 10:30:00）
2. 再次创建相同成员、相同时间的记录
3. 系统允许创建，数据库中出现重复记录

或者：
1. 使用批量导入功能上传Excel模板
2. 重复上传同一个Excel文件
3. 系统允许重复导入，造成数据重复

**预期行为**：
- 同一个成员在同一时间点（精确到分钟）应该只允许存在一条健康记录
- 尝试创建重复记录时，系统应该返回友好的错误提示

**影响范围**：
- 手动创建健康记录（单条）
- 批量导入健康记录（Excel/CSV）
- 数据完整性和统计准确性

## 解决方案 (Solution)

### 1. 数据库层面
在 `health_records` 表中添加复合唯一索引：
- 约束字段：`user_id` + `timestamp`（截断到分钟）
- 注意：需要通过 RecordSubject 表确定实际成员，因此需要考虑 member_id

**修正方案**：
由于系统使用了 RecordSubject 关联表来标识记录属于哪个成员（可能是本人或家人），唯一性约束应该是：
- **member_id（通过RecordSubject） + timestamp（到分钟）**

由于 RecordSubject 是独立表，需要在应用层实现检查。

### 2. 应用层面
在 `HealthManager.create()` 和 `HealthManager.bulk_create()` 中：
- 在插入前检查是否存在相同 member_id + timestamp（分钟级别）的记录
- 如果存在，抛出 `ValueError` 或自定义异常（如 `DuplicateRecordError`）

### 3. API响应
- 单条创建：返回 400 Bad Request + 友好错误消息
- 批量导入：
  - **选项A（推荐）**：跳过重复记录，继续处理其他记录，返回摘要
  - **选项B**：检测到重复时终止整个批次，返回错误详情

## 实施任务 (Implementation Tasks)

### Phase 1: 数据模型与迁移
- [ ] **Task 1.1**: 修改 `HealthRecord` 模型，添加注释说明唯一性约束逻辑
- [ ] **Task 1.2**: 创建 Alembic 迁移脚本
  - 为现有重复数据创建清理策略（保留最早的 created_at）
  - 添加索引优化查询性能：`(user_id, timestamp)`

### Phase 2: Manager层逻辑
- [ ] **Task 2.1**: 在 `HealthManager` 中添加 `check_duplicate()` 方法
  - 输入：member_id, timestamp
  - 逻辑：查询 RecordSubject + HealthRecord，比较时间戳（截断到分钟）
  - 返回：True（重复）/ False（不重复）

- [ ] **Task 2.2**: 修改 `create()` 方法
  - 调用 `check_duplicate()` 检查
  - 如果重复，抛出 `ValueError("该成员在此时间点已有健康记录")`

- [ ] **Task 2.3**: 修改 `bulk_create()` 方法
  - 实现"跳过重复"策略（推荐）
  - 返回摘要：成功数、跳过数、跳过原因列表

### Phase 3: Service层适配
- [ ] **Task 3.1**: 修改 `health_service.create_health_record()`
  - 捕获 `ValueError`，返回 400 + 友好消息

- [ ] **Task 3.2**: 修改 `health_service.batch_import_records()`
  - 处理 bulk_create 返回的摘要
  - 在响应中包含跳过的记录信息

### Phase 4: 测试
- [ ] **Task 4.1**: 单元测试 `test_duplicate_record_prevention`
  - 测试单条创建重复记录被拒绝
  - 测试批量导入跳过重复记录

- [ ] **Task 4.2**: E2E 测试
  - 手动创建重复记录验证错误提示
  - 批量导入相同文件两次验证去重逻辑

## 技术细节

### 时间戳比较逻辑
```python
def truncate_to_minute(dt: datetime) -> datetime:
    """Truncate datetime to minute precision (set seconds and microseconds to 0)"""
    return dt.replace(second=0, microsecond=0)
```

### 唯一性检查伪代码
```python
def check_duplicate(self, member_id: int, timestamp: datetime) -> bool:
    """Check if a record exists for given member at the same minute"""
    truncated_ts = truncate_to_minute(timestamp)
    
    # Query RecordSubject to get record_ids for this member
    record_ids = db.session.query(RecordSubject.record_id)\
        .filter_by(member_id=member_id).all()
    
    # Query HealthRecord with timestamp range (same minute)
    start_of_minute = truncated_ts
    end_of_minute = truncated_ts + timedelta(seconds=59, microseconds=999999)
    
    exists = db.session.query(HealthRecord.id)\
        .filter(HealthRecord.id.in_(record_ids))\
        .filter(HealthRecord.timestamp >= start_of_minute)\
        .filter(HealthRecord.timestamp <= end_of_minute)\
        .first()
    
    return exists is not None
```

## 用户体验

### 单条创建
**错误提示（中文）**：
> ⚠️ 该成员在 2025-12-22 10:30 已有健康记录，请选择不同的时间或编辑现有记录。

**错误提示（英文）**：
> ⚠️ A health record already exists for this member at 2025-12-22 10:30. Please choose a different time or edit the existing record.

### 批量导入
**成功摘要**：
> ✅ 导入完成：成功 15 条，跳过重复 3 条。
> 
> **跳过的记录**：
> - Self, 2025-12-19 08:30 (已存在)
> - 张三, 2025-12-18 20:00 (已存在)
> - Self, 2025-12-17 09:00 (已存在)

## 实施进度 (Implementation Status)

### ✅ 已完成 (Completed)
- ✅ **Task 1.1**: 实现 `check_duplicate()` 方法 - 检查 member_id + timestamp（分钟级）
- ✅ **Task 1.2**: 修改 `bulk_create()` 方法 - 返回详细结果（created/skipped）

**Phase 2: Service层适配** - 2025-12-22
  - 支持 `--dry-run` 预览模式
  - 保留最早创建的记录（by created_at）
  - 检测到5组重复数据，共9条重复记录

### 关键修复说明

**问题根因**：
- 初始实现在 Manager.create() 中检查重复，但此时 RecordSubject 尚未创建
- check_duplicate() 依赖 RecordSubject 表来关联成员和记录
- 导致检查总是失败（查不到关联），重复记录可以被创建

**修复方案**：
- 将重复检查前移到 Service 层
- 在创建 HealthRecord **之前**先调用 `check_duplicate()`
- 此时已有的 RecordSubject 记录可以被正确查询
- 新记录创建和 RecordSubject 关联在同一事务中完成

## 验收标准 (Acceptance Criteria)

- [x] 同一个成员在同一分钟内无法创建多条记录（手动创建）
- [x] 批量导入时重复记录被自动跳过
- [x] 错误提示信息清晰友好（中文）
- [x] 导入摘要准确显示成功/跳过数量
- [x] 提供数据清理工具处理历史重复数据
- [ ] 单元测试覆盖率 > 90%（待补充）
- [ ] E2E 测试验证（待补充）

## 剩余工作
- [x] 单元测试补充（新增重复拦截与批量导入跳过测试）
- [ ] E2E自动化测试
- [ ] 生产环境清理历史重复数据

## 数据清理指南

### 检查现有重复数据
```bash
cd c:\Zhuang\Source\health_platform
.venv\Scripts\python.exe scripts\clean_duplicate_records.py --dry-run
```

### 清理重复数据（生产环境前必须备份！）
```bash
# 1. 备份数据库
python -m flask db-backup  # 或使用数据库工具手动备份

# 2. 执行清理（交互式确认）
.venv\Scripts\python.exe scripts\clean_duplicate_records.py

# 3. 验证结果
.venv\Scripts\python.exe scripts\clean_duplicate_records.py --dry-run
```

**清理规则**：
- 对于每组重复记录（相同成员+相同时间到分钟），保留 `created_at` 最早的记录
- 自动删除对应的 RecordSubject 关联
- 交互式确认，避免误删

## 相关文件

- `src/models.py` - HealthRecord 模型
- `src/manager/health_manager.py` - 业务逻辑层
- `src/service/health_service.py` - API 层
- `tests/test_health.py` - 单元测试
- `migrations/versions/` - 数据库迁移脚本
