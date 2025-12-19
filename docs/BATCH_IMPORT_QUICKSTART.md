# 批量导入 API 快速开始指南

## 快速示例

### 1. 下载模板

```bash
# 下载 Excel 模板
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:5000/api/v1/health/batch-import/template?format=excel" \
  --output template.xlsx

# 下载 CSV 模板
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:5000/api/v1/health/batch-import/template?format=csv" \
  --output template.csv
```

### 2. 填写数据

编辑下载的模板，填入健康记录数据：

| 成员名称 | 测量时间 | 收缩压 | 舒张压 | 心率 | 标签 | 备注 |
|---------|---------|--------|--------|------|------|------|
| Self | 2025-12-19 08:30:00 | 120 | 80 | 72 | 晨起;空腹 | 早晨测量 |
| 张三 | 2025-12-18 20:00:00 | 135 | 85 | 78 | 晚餐后 | 感觉有点头晕 |

### 3. 上传导入

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@health_records.csv" \
  http://localhost:5000/api/v1/health/batch-import
```

### 4. 查看结果

```json
{
  "success": true,
  "summary": {
    "total_rows": 2,
    "success_count": 2,
    "error_count": 0
  },
  "errors": []
}
```

## JavaScript 示例

```javascript
// 上传文件进行批量导入
async function uploadFile(file) {
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
    alert(`成功导入 ${result.summary.success_count} 条记录！`);
    
    if (result.summary.error_count > 0) {
      console.log('部分记录导入失败：', result.errors);
      // 可以下载错误日志
      downloadErrorLog(result.errors);
    }
  }
}
```

## Python 示例

```python
import requests

# 上传文件进行批量导入
def batch_import(file_path, token):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        headers = {'Authorization': f'Bearer {token}'}
        
        response = requests.post(
            'http://localhost:5000/api/v1/health/batch-import',
            headers=headers,
            files=files
        )
        
        result = response.json()
        print(f"总计: {result['summary']['total_rows']} 条")
        print(f"成功: {result['summary']['success_count']} 条")
        print(f"失败: {result['summary']['error_count']} 条")
        
        if result['summary']['error_count'] > 0:
            print("错误详情:")
            for err in result['errors']:
                print(f"  行 {err['row']}: {', '.join(err['errors'])}")

# 使用示例
batch_import('health_records.csv', 'YOUR_TOKEN')
```

## 常见问题

### Q: 支持哪些文件格式？
A: 支持 `.xlsx`（Excel）和 `.csv`（UTF-8 编码）格式。

### Q: 如何匹配成员？
A: 使用成员的全名进行匹配。`Self`、`自己`、`本人` 会自动匹配到当前用户的 Self 成员。

### Q: 时区如何处理？
A: 如果时间不带时区信息，默认使用北京时区（UTC+8）。

### Q: 导入失败了怎么办？
A: 查看返回的 `errors` 数组获取详细错误信息，或下载错误日志 CSV 文件进行修正。

## 完整文档

查看完整的功能文档：[docs/BATCH_IMPORT.md](./BATCH_IMPORT.md)
