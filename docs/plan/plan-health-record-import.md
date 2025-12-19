# 实施计划：健康记录批量导入功能 (Health Record Batch Import)

**基于文档**：
- [需求文档](/docs/requirements/req-health-record-import.md)
- 现有代码：CSV 导出功能（`src/service/health_service.py`）
- 现有代码：成员管理（`src/manager/member_manager.py`）

---

## 1. 概述

本计划实现用户批量导入健康记录功能（Excel/CSV 格式），支持标准模板导入，包含成员匹配、时区处理、数据验证、错误处理等完整流程。

**核心目标**：
1. 降低用户迁移成本，支持历史数据批量录入
2. 提供标准模板和清晰的导入流程
3. 严格的数据验证和友好的错误提示
4. 支持自己和家庭成员数据区分导入

**技术约束**：
- 单次导入最多 1000 条记录
- 文件大小限制 5MB
- 默认时区：北京时区（UTC+8）
- 批量插入使用事务保证原子性
- 权限控制：仅能导入自己家庭的成员数据

---

## 2. 阶段划分

| 阶段 | 名称 | 重点 | 预计周期 |
|:-----|:-----|:-----|:---------|
| **Phase 1** | **后端核心 - 数据解析与验证** | 文件解析、数据验证逻辑、批量插入、API 接口 | 3 天 |
| **Phase 2** | **后端扩展 - 模板与日志** | 模板生成、错误日志导出、导入审计 | 2 天 |
| **Phase 3** | **前端 UI - 导入流程** | 文件上传、预览、结果展示、错误下载 | 3 天 |
| **Phase 4** | **测试与文档** | 单元测试、E2E 测试、用户文档 | 2 天 |

**总预计周期**：10 个工作日（2 周）

---

## 3. 详细任务分解

### Phase 1: 后端核心 - 数据解析与验证

#### 1.1 数据库 Schema 扩展
- [ ] **Task 1.1.1**: 创建 `ImportLog` 模型（可选，用于审计）
  - **文件**: `src/models.py`
  - **字段**:
    - `id` (PK)
    - `user_id` (FK to users)
    - `filename` (导入文件名)
    - `total_rows` (总行数)
    - `success_rows` (成功行数)
    - `failed_rows` (失败行数)
    - `status` (success/partial/failed)
    - `error_summary` (JSON 格式错误摘要)
    - `created_at` (UTC 时间)
  - **验证**: 模型可导入，无语法错误

- [ ] **Task 1.1.2**: 生成数据库迁移脚本
  - **命令**: `flask db migrate -m "add import log table"`
  - **验证**: 迁移脚本生成在 `migrations/versions/` 目录

- [ ] **Task 1.1.3**: 运行迁移
  - **命令**: `flask db upgrade`
  - **验证**: 数据库中存在 `import_logs` 表

#### 1.2 文件解析与数据验证（Manager 层）
- [ ] **Task 1.2.1**: 创建 `ImportManager` 类
  - **文件**: `src/manager/import_manager.py` (新建)
  - **职责**: 文件解析、数据验证、批量插入逻辑
  - **依赖**: `pandas`, `openpyxl` (需添加到 `requirements.txt`)

- [ ] **Task 1.2.2**: 实现 `parse_file(file_stream, file_extension)` 方法
  - **功能**: 解析 Excel (.xlsx) 或 CSV (.csv) 文件
  - **返回**: DataFrame 或 List of Dicts
  - **处理**:
    - Excel: 使用 `pandas.read_excel()`, 仅读取第一个工作表
    - CSV: 使用 `pandas.read_csv(encoding='utf-8-sig')` (支持 BOM)
    - 自动跳过表头说明行（如前 3 行）
  - **验证**: 单元测试覆盖 Excel 和 CSV 两种格式

- [ ] **Task 1.2.3**: 实现 `validate_row(row, user_id, member_manager)` 方法
  - **功能**: 验证单行数据的合法性
  - **验证规则**:
    1. **成员名称** (必填):
       - 匹配用户家庭成员（通过 `member_manager.get_member_by_name()`）
       - 支持 "Self/自己/本人" 特殊匹配
       - 大小写不敏感，去除前后空格
       - 不存在则返回错误: `"成员名称 '{name}' 不存在"`
    2. **测量时间** (必填):
       - 支持格式: ISO 8601, `YYYY-MM-DD HH:MM:SS`, `YYYY/MM/DD HH:MM`
       - 使用 `dateutil.parser.parse()` 解析
       - 无时区信息则添加北京时区 (`Asia/Shanghai`)
       - 转换为 UTC 存储
       - 无效格式返回错误: `"测量时间格式无效"`
    3. **收缩压** (必填): 30-250 mmHg, 必须 > 舒张压
    4. **舒张压** (必填): 30-250 mmHg, 必须 < 收缩压
    5. **心率** (可选): 30-150 bpm, 空值允许
    6. **标签** (可选): 分号分隔, 自动去除空格
    7. **备注** (可选): 文本, 最大 500 字符
  - **返回**: `(is_valid, cleaned_data, error_message)`
  - **验证**: 单元测试覆盖所有验证规则

- [ ] **Task 1.2.4**: 实现 `batch_import(user_id, rows, skip_errors=True)` 方法
  - **功能**: 批量导入健康记录
  - **流程**:
    1. 逐行验证，收集成功行和错误行
    2. 成功行批量插入 (使用事务):
       - 创建 `HealthRecord` 记录
       - 创建对应的 `RecordSubject` 关联
    3. 返回结果摘要:
       ```python
       {
         "total": 100,
         "success": 95,
         "failed": 5,
         "errors": [
           {"row": 10, "data": {...}, "reason": "成员名称不存在"},
           {"row": 25, "data": {...}, "reason": "收缩压必须大于舒张压"}
         ]
       }
       ```
  - **验证**: 单元测试验证事务回滚（失败时不影响已有数据）

- [ ] **Task 1.2.5**: 实现 `save_import_log(user_id, result)` 方法
  - **功能**: 保存导入操作审计日志
  - **存储**: `ImportLog` 表
  - **验证**: 单元测试验证日志正确保存

#### 1.3 API 服务层（Service Layer）
- [ ] **Task 1.3.1**: 创建 `import_bp` Blueprint
  - **文件**: `src/service/import_service.py` (新建)
  - **路径**: `/api/v1/import`
  - **注册**: 在 `src/app.py` 中注册 Blueprint

- [ ] **Task 1.3.2**: 实现 `POST /api/v1/import/upload` 接口
  - **功能**: 上传并导入文件
  - **请求**:
    - Content-Type: `multipart/form-data`
    - 参数:
      - `file` (File, 必填): Excel 或 CSV 文件
      - `skip_errors` (Boolean, 可选, 默认 true): 是否跳过错误行
  - **响应 200**:
    ```json
    {
      "message": "导入完成",
      "total": 100,
      "success": 95,
      "failed": 5,
      "errors": [
        {"row": 10, "reason": "成员名称不存在"},
        {"row": 25, "reason": "收缩压必须大于舒张压"}
      ]
    }
    ```
  - **响应 400**: 文件格式错误、文件过大、超过 1000 行
  - **响应 403**: 权限不足
  - **验证**: Postman 测试上传成功/失败场景

- [ ] **Task 1.3.3**: 添加权限控制 `@jwt_required()`
  - **验证**: 未登录用户调用接口返回 401

#### 1.4 单元测试
- [ ] **Task 1.4.1**: 测试 `parse_file` 方法
  - **文件**: `tests/test_import_manager.py`
  - **用例**: Excel 解析、CSV 解析、空文件、格式错误

- [ ] **Task 1.4.2**: 测试 `validate_row` 方法
  - **用例**: 
    - 必填字段缺失
    - 血压范围错误
    - 成员名称不存在
    - 时间格式错误
    - 标签解析

- [ ] **Task 1.4.3**: 测试 `batch_import` 方法
  - **用例**:
    - 全部成功
    - 部分失败（skip_errors=True）
    - 事务回滚（失败时不影响已有数据）

- [ ] **Task 1.4.4**: 测试 API 接口
  - **文件**: `tests/test_import_service.py`
  - **用例**: 文件上传、权限验证、错误响应

---

### Phase 2: 后端扩展 - 模板与日志

#### 2.1 标准模板生成
- [ ] **Task 2.1.1**: 创建 Excel 模板文件
  - **文件**: `static/templates/health_import_template.xlsx` (新建)
  - **内容**:
    - 第1行: 中文字段名（成员名称, 测量时间, 收缩压, 舒张压, 心率, 标签, 备注）
    - 第2行: 英文字段名（Member Name, Timestamp, Systolic, Diastolic, Heart Rate, Tags, Note）
    - 第3行: 必填说明（（必填）, （必填）, （必填）, （必填）, （可选）, （可选）, （可选））
    - 第4-5行: 示例数据
  - **工具**: 使用 `openpyxl` 代码生成或手动创建
  - **验证**: Excel 可正常打开，格式正确

- [ ] **Task 2.1.2**: 创建 CSV 模板文件
  - **文件**: `static/templates/health_import_template.csv` (新建)
  - **编码**: UTF-8 with BOM
  - **内容**: 与 Excel 模板相同
  - **验证**: Excel 打开 CSV 中文正常显示

- [ ] **Task 2.1.3**: 实现 `GET /api/v1/import/template` 接口
  - **功能**: 下载标准模板
  - **请求参数**: `format` (excel/csv, 默认 excel)
  - **响应**: 文件下载流
  - **验证**: 浏览器可正常下载并打开

#### 2.2 错误日志导出
- [ ] **Task 2.2.1**: 实现 `generate_error_log_csv(errors)` 方法
  - **文件**: `src/manager/import_manager.py`
  - **功能**: 将错误信息转换为 CSV 格式
  - **内容**:
    - 列: 行号, 成员名称, 测量时间, 收缩压, 舒张压, 心率, 标签, 备注, 错误原因
    - 每行包含原始数据 + 错误原因
  - **编码**: UTF-8 with BOM
  - **验证**: 单元测试验证 CSV 格式正确

- [ ] **Task 2.2.2**: 修改 `POST /api/v1/import/upload` 接口
  - **功能**: 返回错误日志下载 URL（如有错误）
  - **响应**（有错误时）:
    ```json
    {
      "message": "导入完成",
      "total": 100,
      "success": 95,
      "failed": 5,
      "error_log_url": "/api/v1/import/errors/{import_id}"
    }
    ```
  - **验证**: Postman 测试返回正确

- [ ] **Task 2.2.3**: 实现 `GET /api/v1/import/errors/{import_id}` 接口
  - **功能**: 下载错误日志 CSV
  - **权限**: 仅创建者可下载
  - **响应**: CSV 文件流
  - **验证**: 浏览器可正常下载

#### 2.3 导入历史查询（可选）
- [ ] **Task 2.3.1**: 实现 `GET /api/v1/import/history` 接口
  - **功能**: 查询当前用户的导入历史
  - **响应**:
    ```json
    {
      "imports": [
        {
          "id": 1,
          "filename": "health_data.xlsx",
          "total": 100,
          "success": 95,
          "failed": 5,
          "status": "partial",
          "created_at": "2025-12-19T10:30:00Z"
        }
      ]
    }
    ```
  - **验证**: 返回正确的导入记录

---

### Phase 3: 前端 UI - 导入流程

#### 3.1 导入入口与模板下载
- [ ] **Task 3.1.1**: 在健康记录页面添加"导入数据"按钮
  - **文件**: `frontend/src/pages/HealthRecords.js`
  - **位置**: 页面右上角，与"导出"按钮并排
  - **图标**: `<UploadOutlined />`
  - **验证**: 按钮显示正常

- [ ] **Task 3.1.2**: 创建导入向导 Modal
  - **组件**: `frontend/src/components/ImportWizard.js` (新建)
  - **步骤**:
    1. 下载模板
    2. 上传文件
    3. 预览数据
    4. 查看结果
  - **使用**: Ant Design `Steps` + `Modal`
  - **验证**: Modal 可正常打开和关闭

- [ ] **Task 3.1.3**: 实现步骤 1 - 下载模板
  - **UI**: 两个下载按钮（Excel / CSV）
  - **功能**: 调用 `GET /api/v1/import/template?format=excel|csv`
  - **实现**: 使用 `axios` 下载文件（`responseType: 'blob'`）
  - **验证**: 点击按钮可下载对应格式模板

#### 3.2 文件上传与预览
- [ ] **Task 3.2.1**: 实现步骤 2 - 上传文件
  - **UI**: Ant Design `Upload.Dragger` 组件
  - **限制**:
    - 文件类型: `.xlsx, .csv`
    - 文件大小: 5MB
    - 单个文件
  - **验证**: 文件大小超限时显示错误提示

- [ ] **Task 3.2.2**: 实现文件预览功能
  - **方案 A**（推荐）: 前端解析 Excel/CSV (使用 `xlsx` 或 `papaparse` 库)
  - **方案 B**: 后端提供预览接口 `POST /api/v1/import/preview`
  - **显示**: Ant Design `Table` 展示前 10 行数据
  - **验证**: 表格显示正确，列对齐

- [ ] **Task 3.2.3**: 实现步骤 3 - 确认导入
  - **UI**: "开始导入"按钮 + `skip_errors` 复选框
  - **功能**: 调用 `POST /api/v1/import/upload`
  - **加载状态**: 显示 `Spin` 加载动画
  - **验证**: 点击后显示加载状态

#### 3.3 结果展示与错误处理
- [ ] **Task 3.3.1**: 实现步骤 4 - 查看结果
  - **UI**: 结果摘要卡片（Ant Design `Result` 组件）
  - **显示内容**:
    - 图标: 全部成功 → `<CheckCircleOutlined />` (绿色)
    - 图标: 部分失败 → `<ExclamationCircleOutlined />` (黄色)
    - 统计: "总行数: 100 | 成功: 95 | 失败: 5"
  - **验证**: 不同结果显示不同样式

- [ ] **Task 3.3.2**: 实现错误列表展示
  - **UI**: Ant Design `List` 或 `Table` 组件
  - **内容**: 行号 + 错误原因
  - **分页**: 如果错误行 > 10 则分页显示
  - **验证**: 错误列表显示清晰

- [ ] **Task 3.3.3**: 实现错误日志下载
  - **UI**: "下载错误日志" 按钮
  - **功能**: 调用 `GET /api/v1/import/errors/{import_id}`
  - **验证**: 点击后下载 CSV 文件

#### 3.4 国际化支持
- [ ] **Task 3.4.1**: 添加中文翻译
  - **文件**: `frontend/src/locales/zh.json`
  - **内容**:
    ```json
    {
      "import": {
        "title": "导入健康记录",
        "downloadTemplate": "下载模板",
        "uploadFile": "上传文件",
        "preview": "预览数据",
        "startImport": "开始导入",
        "skipErrors": "跳过错误行继续导入",
        "result": {
          "success": "导入成功",
          "partial": "部分导入成功",
          "failed": "导入失败"
        },
        "downloadErrors": "下载错误日志"
      }
    }
    ```

- [ ] **Task 3.4.2**: 添加英文翻译
  - **文件**: `frontend/src/locales/en.json`
  - **内容**: 对应的英文翻译

---

### Phase 4: 测试与文档

#### 4.1 单元测试扩展
- [ ] **Task 4.1.1**: 补充边界场景测试
  - **用例**:
    - 空文件
    - 仅有表头无数据
    - 超过 1000 行
    - CSV 编码非 UTF-8
    - Excel 多个工作表（仅读取第一个）
  - **文件**: `tests/test_import_manager.py`

- [ ] **Task 4.1.2**: 测试时区处理
  - **用例**:
    - 无时区信息 → 默认北京时区
    - 有时区信息 → 使用原时区
    - 不同时间格式解析
  - **验证**: 数据库存储时间为 UTC

- [ ] **Task 4.1.3**: 测试权限控制
  - **用例**: 用户 A 尝试导入用户 B 的成员数据 → 403
  - **文件**: `tests/test_import_service.py`

#### 4.2 E2E 测试
- [ ] **Task 4.2.1**: 创建完整导入流程 E2E 测试
  - **文件**: `tests/e2e/tests/import.spec.js` (新建)
  - **场景**:
    1. 登录用户
    2. 点击"导入数据"按钮
    3. 下载模板
    4. 上传测试文件（预先准备）
    5. 预览数据
    6. 确认导入
    7. 验证结果摘要
    8. 下载错误日志（如有错误）
    9. 刷新健康记录列表，验证数据已导入

- [ ] **Task 4.2.2**: 测试错误场景
  - **场景**:
    - 上传空文件 → 提示错误
    - 上传超大文件 → 提示文件过大
    - 上传错误格式 → 提示格式错误
    - 上传包含错误数据的文件 → 显示错误列表

#### 4.3 性能测试（可选）
- [ ] **Task 4.3.1**: 测试大文件导入性能
  - **用例**: 导入 1000 条记录，测量耗时
  - **目标**: 响应时间 < 10 秒
  - **工具**: `pytest` + `time` 模块

- [ ] **Task 4.3.2**: 测试并发导入
  - **用例**: 5 个用户同时导入
  - **目标**: 无死锁、无数据错乱

#### 4.4 用户文档
- [ ] **Task 4.4.1**: 创建用户手册
  - **文件**: `docs/user-guide/health-record-import.md` (新建)
  - **内容**:
    - 功能介绍
    - 导入步骤（含截图）
    - 模板格式说明
    - 常见问题 FAQ

- [ ] **Task 4.4.2**: 更新 API 文档
  - **文件**: `docs/Design/API_Design.md`
  - **内容**: 添加导入相关接口说明

- [ ] **Task 4.4.3**: 更新 README
  - **文件**: `README.md`
  - **内容**: 在"核心功能"部分添加"批量导入"说明

---

## 4. 技术细节与最佳实践

### 4.1 文件解析库选择
- **Excel**: `openpyxl` (纯 Python, 不依赖 xlrd) 或 `pandas`
- **CSV**: Python 内置 `csv` 模块 或 `pandas`
- **推荐**: 使用 `pandas` 统一处理，API 一致

### 4.2 时区处理
```python
from datetime import datetime
from zoneinfo import ZoneInfo

# 用户输入时间（无时区）
user_time_str = "2025-12-19 08:30:00"

# 解析并添加北京时区
beijing_tz = ZoneInfo("Asia/Shanghai")
dt = datetime.strptime(user_time_str, "%Y-%m-%d %H:%M:%S")
dt_with_tz = dt.replace(tzinfo=beijing_tz)

# 转换为 UTC 存储
dt_utc = dt_with_tz.astimezone(ZoneInfo("UTC"))
```

### 4.3 批量插入优化
```python
from sqlalchemy.orm import Session

def batch_insert(session: Session, records: List[HealthRecord]):
    # 使用 bulk_insert_mappings 提升性能
    session.bulk_insert_mappings(HealthRecord, [
        {"systolic": r.systolic, "diastolic": r.diastolic, ...}
        for r in records
    ])
    session.commit()
```

### 4.4 错误日志 CSV 格式
```csv
行号,成员名称,测量时间,收缩压,舒张压,心率,标签,备注,错误原因
10,张三,2025-12-19 08:30:00,120,80,72,晨起,正常,成员名称不存在
25,Self,2025-12-18 20:00:00,85,90,,,,"收缩压必须大于舒张压"
```

---

## 5. 依赖与前置条件

### 5.1 Python 依赖包
需添加到 `requirements.txt`:
```
pandas>=2.0.0
openpyxl>=3.1.0
python-dateutil>=2.8.0
```

### 5.2 前端依赖包
需添加到 `frontend/package.json`:
```json
{
  "dependencies": {
    "xlsx": "^0.18.5",
    "papaparse": "^5.4.1"
  }
}
```

### 5.3 现有功能依赖
- ✅ 家庭成员管理功能已上线
- ✅ HealthRecord 和 RecordSubject 模型稳定
- ✅ JWT 认证和权限控制完善
- ✅ CSV 导出功能（可参考实现）

---

## 6. 风险管理

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| 用户上传非标准格式 | 中 | 提供清晰模板和说明；前端预览功能 |
| 大文件导入超时 | 高 | 限制 1000 行；异步处理（可选） |
| 时区处理错误 | 中 | 单元测试充分覆盖；文档明确说明 |
| 成员名称匹配失败 | 中 | 支持多种匹配方式；提供清晰错误提示 |
| 并发导入数据冲突 | 低 | 使用数据库事务隔离 |

---

## 7. 验收标准

### 功能完成度
- [ ] 所有 Phase 1-4 任务完成
- [ ] 单元测试通过率 > 95%
- [ ] E2E 测试通过率 100%

### 性能指标
- [ ] 1000 条记录导入时间 < 10 秒
- [ ] 文件上传成功率 > 99%
- [ ] 导入成功率 > 95%（正常数据）

### 用户体验
- [ ] 导入流程不超过 3 步
- [ ] 错误提示清晰易懂
- [ ] 支持中英文国际化

---

## 8. 后续优化方向

### Phase 2 扩展（智能导入）
1. **自动格式识别**: 分析任意格式文件，自动匹配字段
2. **自然语言映射**: "第3列是收缩压" → 自动建立映射规则
3. **AI 辅助**: 使用 LLM 理解用户的列描述
4. **规则保存**: 保存常用映射规则供下次使用
5. **历史导入管理**: 查看导入历史、回滚功能

### 其他数据源
- Apple Health 数据导入
- Google Fit 数据导入
- 小米健康数据导入
- OCR 识别纸质记录

---

**状态**: ✅ 计划制定完成，等待开发实施  
**预计完成时间**: 2 周（10 个工作日）  
**最后更新**: 2025-12-19  
**版本**: Health Platform v1.6+
