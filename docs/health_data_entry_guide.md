# 健康数据录入功能使用说明 (Health Data Entry Usage Guide)

本文档说明如何使用健康记录平台的数据录入功能。

## 功能概述 (Feature Overview)

健康数据录入功能支持以下内容：
- **血压记录**：收缩压/舒张压（范围：50-250 mmHg）
- **心跳记录**：心率数据
- **时间戳**：自动生成时间，支持手动修改
- **备注**：文本备注信息，支持中文
- **标签**：多标签支持，如"晨起"、"运动后"、"服药前"等

## API 端点 (API Endpoints)

### 1. 创建健康记录 (Create Health Record)
```bash
POST /api/v1/health
Authorization: Bearer <token>
Content-Type: application/json

{
  "systolic": 120,
  "diastolic": 80,
  "heart_rate": 72,
  "timestamp": "2025-08-26T08:00:00Z",  // 可选，不提供则自动生成
  "tags": ["晨起", "家里"],
  "note": "早晨起床后测量"
}
```

### 2. 查询健康记录 (List Health Records)
```bash
GET /api/v1/health?tags=晨起&page=1&size=20
Authorization: Bearer <token>
```

支持的查询参数：
- `tags`: 标签过滤，支持中文，多个标签用逗号分隔
- `date_from`: 开始日期 (ISO 8601格式)
- `date_to`: 结束日期 (ISO 8601格式)
- `page`: 页码 (默认: 1)
- `size`: 每页记录数 (默认: 20)

### 3. 获取单条记录 (Get Single Record)
```bash
GET /api/v1/health/{id}
Authorization: Bearer <token>
```

### 4. 更新记录 (Update Record)
```bash
PUT /api/v1/health/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "systolic": 125,
  "note": "更新后的备注"
}
```

### 5. 删除记录 (Delete Record)
```bash
DELETE /api/v1/health/{id}
Authorization: Bearer <token>
```

## 示例用法 (Usage Examples)

### 完整的数据录入流程

1. **用户注册和登录**
```bash
# 注册
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "张三", "email": "zhangsan@example.com", "password": "password123"}'

# 登录获取token
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "zhangsan@example.com", "password": "password123"}'
```

2. **录入健康数据**
```bash
# 早晨测量
curl -X POST http://localhost:5000/api/v1/health \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "systolic": 120,
    "diastolic": 80,
    "heart_rate": 72,
    "tags": ["晨起", "家里"],
    "note": "早晨起床后测量，感觉良好"
  }'

# 运动后测量
curl -X POST http://localhost:5000/api/v1/health \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "systolic": 135,
    "diastolic": 85,
    "heart_rate": 95,
    "tags": ["运动后", "健身房"],
    "note": "跑步30分钟后测量"
  }'
```

3. **查询和筛选数据**
```bash
# 查询所有晨起测量的记录
curl -X GET "http://localhost:5000/api/v1/health?tags=晨起" \
  -H "Authorization: Bearer <your_token>"

# 查询指定日期范围的记录
curl -X GET "http://localhost:5000/api/v1/health?date_from=2025-08-01T00:00:00Z&date_to=2025-08-31T23:59:59Z" \
  -H "Authorization: Bearer <your_token>"
```

## 验证标准 (Validation Rules)

- **血压范围**：收缩压和舒张压必须在50-250之间
- **标签格式**：必须是字符串数组
- **时间格式**：ISO 8601格式 (如: "2025-08-26T08:00:00Z")
- **中文支持**：所有文本字段完全支持中文字符

## 常见标签示例 (Common Tag Examples)

建议使用的标签：
- **时间相关**: "晨起", "午间", "晚间", "睡前"
- **活动相关**: "运动前", "运动后", "休息时"
- **地点相关**: "家里", "办公室", "医院", "健身房"
- **状态相关**: "服药前", "服药后", "紧张时", "放松时"

## 技术说明

- 所有数据按用户隔离，用户只能访问自己的记录
- 记录按时间戳倒序排列（最新的在前）
- 支持分页查询避免性能问题
- 标签搜索支持中文字符的精确匹配