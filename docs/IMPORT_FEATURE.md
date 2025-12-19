# 健康记录批量导入功能

## 概述

健康记录批量导入功能允许用户通过 Excel 或 CSV 文件批量上传自己和家庭成员的健康记录。这个功能特别适合：

- 从其他平台迁移历史数据
- 批量录入纸质记录
- 定期导入体检数据

## API 接口

### POST /api/v1/import/upload

批量导入健康记录

**请求**
- Content-Type: `multipart/form-data`
- 需要 JWT 认证

**参数**
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | Excel (.xlsx) 或 CSV (.csv) 文件 |
| skip_errors | Boolean | 否 | 是否跳过错误行继续导入（默认：true）|

**约束**
- 文件大小：最大 5MB
- 行数限制：单次最多 1000 条记录
- 支持格式：.xlsx, .xls, .csv

**响应 200 - 成功**
```json
{
  "message": "导入完成",
  "total": 100,
  "success": 95,
  "failed": 5,
  "errors": [
    {
      "row": 10,
      "reason": "成员名称 '张三' 不存在"
    },
    {
      "row": 25,
      "reason": "收缩压必须大于舒张压"
    }
  ]
}
```

**响应 400 - 错误**
```json
{
  "code": "400",
  "message": "文件大小超过限制 (5.0MB)"
}
```

## 数据格式

### 必填字段

| 字段名 | 说明 | 格式 | 范围/规则 |
|--------|------|------|-----------|
| 成员名称 | 家庭成员名称 | 文本 | 必须是已存在的成员，或使用 Self/自己/本人 |
| 测量时间 | 测量的时间 | 日期时间 | YYYY-MM-DD HH:MM:SS 或 YYYY/MM/DD HH:MM |
| 收缩压 | 高压 | 整数 | 30-250 mmHg |
| 舒张压 | 低压 | 整数 | 30-250 mmHg，必须小于收缩压 |

### 可选字段

| 字段名 | 说明 | 格式 | 范围/规则 |
|--------|------|------|-----------|
| 心率 | 每分钟心跳次数 | 整数 | 30-150 bpm |
| 标签 | 记录标签 | 文本 | 多个标签用分号(;)分隔 |
| 备注 | 备注信息 | 文本 | 最多 500 字符 |

### 列名支持

系统支持多种列名格式，包括中文和英文：

- **成员名称**: 成员名称, Member Name, member_name, 姓名
- **测量时间**: 测量时间, Timestamp, timestamp, 时间
- **收缩压**: 收缩压, Systolic, systolic, SBP
- **舒张压**: 舒张压, Diastolic, diastolic, DBP
- **心率**: 心率, Heart Rate, heart_rate, HR
- **标签**: 标签, Tags, tags, 标记
- **备注**: 备注, Note, note, 说明

## 模板文件

### 下载模板

系统提供标准模板文件：

- Excel 模板: `static/templates/health_import_template.xlsx`
- CSV 模板: `static/templates/health_import_template.csv`

### Excel 模板示例

| 成员名称 | 测量时间 | 收缩压 | 舒张压 | 心率 | 标签 | 备注 |
|----------|----------|--------|--------|------|------|------|
| Self | 2025-12-19 08:30:00 | 120 | 80 | 72 | 晨起;空腹 | 正常 |
| 父亲 | 2025-12-19 09:00:00 | 135 | 88 | 78 | 餐后 | 血压稍高 |
| 母亲 | 2025-12-19 10:00:00 | 118 | 76 | 68 | 运动前 | 正常 |

### CSV 模板示例

```csv
成员名称,测量时间,收缩压,舒张压,心率,标签,备注
Self,2025-12-19 08:30:00,120,80,72,晨起;空腹,正常
父亲,2025-12-19 09:00:00,135,88,78,餐后,血压稍高
母亲,2025-12-19 10:00:00,118,76,68,运动前,正常
```

## 特殊说明

### 成员名称匹配

- **Self/自己/本人**: 自动匹配为当前用户的默认成员
- **其他名称**: 必须完全匹配已创建的家庭成员名称（不区分大小写）
- 如果成员不存在，该行会被标记为错误

### 时区处理

- **无时区信息**: 默认使用北京时区 (UTC+8)
- **有时区信息**: 使用原时区
- 所有时间最终转换为 UTC 存储

支持的时间格式：
- `2025-12-19 08:30:00`
- `2025-12-19T08:30:00`
- `2025/12/19 08:30`
- ISO 8601 格式

### 标签处理

- 多个标签使用分号(`;`)分隔
- 自动去除前后空格
- 示例: `晨起;空腹;正常` → `["晨起", "空腹", "正常"]`

### 错误处理

**skip_errors=true (默认)**
- 跳过错误行，继续导入有效数据
- 返回所有错误信息
- 最多返回前 100 个错误

**skip_errors=false**
- 遇到第一个错误立即终止
- 不导入任何数据（保证原子性）
- 返回所有验证错误

## 导入日志

每次导入操作都会记录审计日志，包括：

- 导入文件名
- 总行数、成功行数、失败行数
- 导入状态（success/partial/failed）
- 错误摘要（JSON 格式）
- 导入时间

日志存储在 `import_logs` 表中，可用于：
- 追踪导入历史
- 分析导入质量
- 排查问题

## 常见错误

| 错误信息 | 原因 | 解决方法 |
|----------|------|----------|
| 成员名称 'XXX' 不存在 | 成员未创建 | 先在成员管理中创建该成员 |
| 测量时间格式无效 | 时间格式错误 | 使用标准格式 YYYY-MM-DD HH:MM:SS |
| 收缩压必须大于舒张压 | 数据错误 | 检查并修正血压数值 |
| 收缩压必须在 30-250 mmHg 范围内 | 数值超出范围 | 检查数值是否合理 |
| 文件大小超过限制 | 文件过大 | 分批导入或减少行数 |
| 文件行数超过限制 (1000 行) | 数据量过大 | 分批导入 |

## 最佳实践

1. **准备数据**
   - 下载并使用标准模板
   - 确保所有家庭成员已创建
   - 检查数据格式和范围

2. **导入前验证**
   - 使用 Excel 或 CSV 编辑器检查数据
   - 确认成员名称拼写正确
   - 验证血压值的合理性

3. **分批导入**
   - 大量数据建议分批导入（每批不超过 500 条）
   - 避免单次导入过多数据影响性能

4. **错误处理**
   - 首次导入建议使用 skip_errors=false 确保数据质量
   - 修复错误后重新导入失败的行

5. **数据备份**
   - 导入前备份原始文件
   - 保存导入结果用于核对

## 示例代码

### Python 示例

```python
import requests

# 登录获取 token
login_response = requests.post('http://localhost:5000/api/v1/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})
token = login_response.json()['access_token']

# 上传文件
with open('health_records.xlsx', 'rb') as f:
    files = {'file': f}
    data = {'skip_errors': 'true'}
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(
        'http://localhost:5000/api/v1/import/upload',
        files=files,
        data=data,
        headers=headers
    )
    
    result = response.json()
    print(f"导入完成: 成功 {result['success']}/{result['total']} 条")
    
    if result['failed'] > 0:
        print(f"失败 {result['failed']} 条:")
        for error in result['errors']:
            print(f"  第 {error['row']} 行: {error['reason']}")
```

### cURL 示例

```bash
# 登录
TOKEN=$(curl -s -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  | jq -r '.access_token')

# 上传文件
curl -X POST http://localhost:5000/api/v1/import/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@health_records.xlsx" \
  -F "skip_errors=true"
```

## 技术实现

### 架构

```
Client → Service Layer → Manager Layer → Database
         (import_service.py) → (import_manager.py) → (models.py)
```

### 关键组件

1. **ImportManager** (`src/manager/import_manager.py`)
   - `parse_file()`: 文件解析
   - `validate_row()`: 数据验证
   - `batch_import()`: 批量插入
   - `save_import_log()`: 日志保存

2. **ImportService** (`src/service/import_service.py`)
   - `POST /api/v1/import/upload`: API 端点
   - 文件验证和上传处理

3. **ImportLog Model** (`src/models.py`)
   - 导入审计日志表

### 性能优化

- 使用 pandas 高效解析文件
- 批量插入减少数据库操作
- 事务保证数据一致性
- 限制单次导入量避免超时

### 安全措施

- JWT 认证保护 API
- 文件类型和大小验证
- SQL 注入防护（ORM）
- 权限控制（仅能导入自己家庭的成员）

## 后续增强 (Phase 2+)

计划中的功能增强：

1. **模板下载接口** (Phase 2)
   - GET /api/v1/import/template
   - 动态生成包含用户成员的模板

2. **错误日志导出** (Phase 2)
   - 导出错误行为 CSV 文件
   - 方便修正后重新导入

3. **导入历史查询** (Phase 2)
   - GET /api/v1/import/history
   - 查看过去的导入记录

4. **智能列映射** (未来)
   - 自动识别任意格式文件
   - AI 辅助字段匹配

5. **其他数据源** (未来)
   - Apple Health 数据导入
   - Google Fit 数据导入
   - OCR 识别纸质记录

---

**版本**: Health Platform v1.6+  
**最后更新**: 2025-12-19  
**作者**: Copilot Agent
