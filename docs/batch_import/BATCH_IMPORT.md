# 健康记录批量导入功能文档

## 概述

批量导入功能允许用户通过上传 Excel 或 CSV 文件来批量导入健康记录。支持历史数据迁移和批量录入场景。

## 功能特性

### 核心能力
- ✅ 支持 Excel (.xlsx) 和 CSV (.csv) 格式
- ✅ 文件大小限制：5MB
- ✅ 单次导入限制：1000 条记录
- ✅ 中英文双语表头支持
- ✅ 智能成员匹配（支持 Self/自己/本人）
- ✅ 自动时区处理（默认北京时区 UTC+8）
- ✅ 完整的数据验证
- ✅ 详细的错误报告
- ✅ 模板下载
- ✅ 错误日志导出

### 数据验证规则
- **必填字段**：成员名称、测量时间、收缩压、舒张压
- **血压范围**：30-250 mmHg
- **关系验证**：收缩压 > 舒张压
- **心率范围**：30-150 bpm（可选）
- **标签**：支持分号或逗号分隔
- **备注**：最多 500 字符

## API 端点

### 1. 下载导入模板

**端点**: `GET /api/v1/health/batch-import/template`

**参数**:
- `format`: 模板格式（`excel` 或 `csv`，默认 `excel`）

**示例**:
```bash
# 下载 Excel 模板
curl -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/v1/health/batch-import/template?format=excel" \
  --output template.xlsx

# 下载 CSV 模板
curl -H "Authorization: Bearer <token>" \
  "http://localhost:5000/api/v1/health/batch-import/template?format=csv" \
  --output template.csv
```

### 2. 批量导入健康记录

**端点**: `POST /api/v1/health/batch-import`

**请求格式**: `multipart/form-data`

**参数**:
- `file`: 上传的 Excel 或 CSV 文件

**响应示例**:
```json
{
  "success": true,
  "summary": {
    "total_rows": 10,
    "success_count": 8,
    "error_count": 2
  },
  "errors": [
    {
      "row": 3,
      "data": {
        "member_name": "张三",
        "timestamp": "2025-12-19 08:30:00",
        "systolic": 25,
        "diastolic": 80
      },
      "errors": ["Systolic must be between 30-250 mmHg"]
    }
  ]
}
```

**示例**:
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -F "file=@health_records.csv" \
  http://localhost:5000/api/v1/health/batch-import
```

### 3. 导出错误日志

**端点**: `POST /api/v1/health/batch-import/errors`

**请求格式**: `application/json`

**请求体**:
```json
{
  "errors": [
    {
      "row": 2,
      "data": {
        "member_name": "Test",
        "timestamp": "2025-12-19 08:30:00",
        "systolic": 25,
        "diastolic": 80
      },
      "errors": ["Systolic must be between 30-250 mmHg"]
    }
  ]
}
```

**响应**: CSV 文件下载

## 文件格式说明

### CSV 格式要求
- 编码：UTF-8（推荐带 BOM）
- 分隔符：逗号
- 第一行：列标题

### Excel 格式要求
- 格式：.xlsx（Excel 2007+）
- 工作表：使用第一个工作表
- 第一行：列标题

### 列定义

| 中文列名 | 英文列名 | 必填 | 格式 | 说明 |
|---------|---------|------|------|------|
| 成员名称 | Member Name | ✅ | 文本 | 家庭成员姓名，支持 Self/自己/本人 |
| 测量时间 | Timestamp | ✅ | 日期时间 | 支持多种格式，默认北京时区 |
| 收缩压 | Systolic | ✅ | 整数 | 30-250 mmHg |
| 舒张压 | Diastolic | ✅ | 整数 | 30-250 mmHg |
| 心率 | Heart Rate | ⭕ | 整数 | 30-150 bpm |
| 标签 | Tags | ⭕ | 文本 | 分号或逗号分隔，如"晨起;空腹" |
| 备注 | Note | ⭕ | 文本 | 最多 500 字符 |

### 示例数据

**中文格式**:
```csv
成员名称,测量时间,收缩压,舒张压,心率,标签,备注
Self,2025-12-19 08:30:00,120,80,72,晨起;空腹,早晨测量
张三,2025-12-18 20:00:00,135,85,78,晚餐后,感觉有点头晕
Self,2025-12-17 09:00:00,118,78,70,运动后,跑步30分钟后
```

**英文格式**:
```csv
Member Name,Timestamp,Systolic,Diastolic,Heart Rate,Tags,Note
Self,2025-12-19 08:30:00,120,80,72,morning;fasting,Morning measurement
Zhang San,2025-12-18 20:00:00,135,85,78,after dinner,Feel a little dizzy
Self,2025-12-17 09:00:00,118,78,70,after exercise,After 30min running
```

## 时间格式支持

支持的时间格式示例：
- `2025-12-19 08:30:00`
- `2025-12-19T08:30:00`
- `2025-12-19 08:30:00+08:00`
- `2025-12-19T08:30:00Z`
- `2025/12/19 08:30:00`

**时区处理规则**:
1. 如果时间带时区信息（如 `+08:00` 或 `Z`），使用该时区
2. 如果时间不带时区信息，默认为北京时区（UTC+8）
3. 所有时间在数据库中统一存储为 UTC 时间

## 成员匹配规则

### 自动匹配
- `Self`、`self`、`SELF` → 匹配当前用户的 Self 成员
- `自己`、`本人` → 匹配当前用户的 Self 成员

### 名称匹配
- 大小写不敏感
- 自动去除前后空格
- 精确匹配成员全名

### 示例
```
输入成员名称    →  匹配结果
Self           →  当前用户的 Self 成员
自己            →  当前用户的 Self 成员
本人            →  当前用户的 Self 成员
张三            →  名为"张三"的家庭成员
 李四           →  名为"李四"的家庭成员（自动去除空格）
```

## 错误处理

### 验证错误类型

1. **文件验证**
   - 文件大小超过 5MB
   - 不支持的文件格式
   - 缺少必填列

2. **数据验证**
   - 必填字段为空
   - 数值超出范围
   - 时间格式错误
   - 成员不存在

3. **关系验证**
   - 收缩压 ≤ 舒张压

### 错误处理策略

- **跳过错误行**：遇到错误时跳过该行，继续处理其他行
- **部分成功**：即使有错误行，成功的行仍会被导入
- **详细报告**：返回每个错误行的行号、数据和错误信息
- **错误导出**：可以下载包含所有错误的 CSV 文件

## 使用流程

### 前端集成示例

```javascript
// 1. 下载模板
async function downloadTemplate(format = 'excel') {
  const response = await fetch(
    `/api/v1/health/batch-import/template?format=${format}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `template.${format === 'excel' ? 'xlsx' : 'csv'}`;
  a.click();
}

// 2. 上传文件进行批量导入
async function batchImport(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/v1/health/batch-import', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log(`成功导入 ${result.summary.success_count} 条记录`);
    if (result.summary.error_count > 0) {
      console.log(`${result.summary.error_count} 条记录导入失败`);
      // 显示错误或提供下载错误日志
      downloadErrorLog(result.errors);
    }
  }
}

// 3. 下载错误日志
async function downloadErrorLog(errors) {
  const response = await fetch('/api/v1/health/batch-import/errors', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ errors })
  });
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `import_errors_${Date.now()}.csv`;
  a.click();
}
```

## 性能考虑

- **批量插入**：使用数据库批量操作优化性能
- **事务处理**：成功的记录在单个事务中提交
- **内存限制**：5MB 文件大小限制防止内存溢出
- **记录限制**：1000 条记录限制保证响应时间 < 10 秒

## 权限控制

- 用户只能导入自己家庭的成员数据
- 尝试导入不存在的成员会返回错误
- 所有操作都需要有效的 JWT 令牌

## 审计日志

批量导入操作会记录：
- 用户 ID
- 导入时间
- 文件名
- 成功/失败记录数

## 故障排查

### 常见问题

**Q: 导入失败，提示"文件格式错误"**
A: 请确保文件是 .xlsx 或 .csv 格式，并包含所有必填列

**Q: 成员名称匹配失败**
A: 请检查成员名称是否与家庭成员列表中的名称完全一致（不区分大小写）

**Q: 时间格式错误**
A: 请使用支持的时间格式，如 `2025-12-19 08:30:00`

**Q: 部分记录导入失败**
A: 下载错误日志查看详细错误信息，修正后重新导入失败的记录

## 开发者信息

### 测试
运行单元测试：
```bash
pytest tests/test_batch_import.py -v
```

### 依赖包
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- python-dateutil >= 2.8.0

### 扩展开发
可以通过继承 `HealthManager.bulk_create()` 方法来扩展批量导入功能。

## 更新历史

- **v1.0 (2025-12-19)**: 初始版本
  - 支持 Excel 和 CSV 格式
  - 实现数据验证和错误处理
  - 添加模板下载和错误日志导出

## 相关文档

- [API 设计文档](../docs/API_Design.md)
- [贡献指南](../CONTRIBUTING.md)
- [开发环境配置](../docs/DEVELOPMENT.md)
