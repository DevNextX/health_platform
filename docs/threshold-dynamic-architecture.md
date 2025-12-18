# 阈值治理架构设计 - 动态计算方案

## 设计原则

### 问题
最初的设计中，`health_records` 表包含 `threshold_status` 和 `threshold_version` 列，导致：
1. **数据冗余**：每条记录都存储计算结果
2. **维护困难**：标准更新时需要批量更新历史数据
3. **失去灵活性**：无法用新标准重新评估历史数据

### 解决方案
采用**前端动态计算**架构：
- 后端只存储原始测量值（`systolic`, `diastolic`, `heart_rate`）
- 前端获取活跃阈值配置并动态计算健康状态
- 标准更新后，历史数据自动使用新标准重新评估

## 架构流程

```
┌─────────────────┐
│ 用户访问健康记录 │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ 前端并行发起两个请求 │
├─────────────────────┤
│ 1. GET /api/v1/health              (健康记录列表)
│ 2. GET /api/v1/thresholds/active   (活跃阈值配置)
└────────┬───────────┘
         │
         ▼
┌─────────────────────────────┐
│ 前端计算模块                 │
│ thresholdCalculator.js      │
├─────────────────────────────┤
│ computeThresholdStatus(     │
│   systolic,                 │
│   diastolic,                │
│   heart_rate,               │
│   config                    │
│ )                           │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ 动态渲染健康状态标签         │
│ 🟢 健康 / 🟠 临界 / 🔴 异常  │
└─────────────────────────────┘
```

## 数据流

### 后端 API

#### 健康记录 API
```javascript
GET /api/v1/health
Response:
{
  "records": [
    {
      "id": 1,
      "systolic": 110,
      "diastolic": 75,
      "heart_rate": 72,
      "timestamp": "2025-12-01T10:00:00Z",
      "tags": ["早晨"],
      "note": "感觉良好"
      // ❌ 不再返回 threshold_status
      // ❌ 不再返回 threshold_version
    }
  ]
}
```

#### 阈值配置 API
```javascript
GET /api/v1/thresholds/active
Response:
{
  "profile": {
    "id": 1,
    "payload": "{\"systolic_healthy\":[90,120],\"systolic_borderline\":[120,140],...}",
    "status": "active"
  },
  "version": 1
}
```

### 前端计算逻辑

```javascript
// utils/thresholdCalculator.js
export const computeThresholdStatus = (systolic, diastolic, heartRate, config) => {
  if (!config) return null;
  
  const { systolic_healthy, systolic_borderline, diastolic_healthy, diastolic_borderline } = config.payload;
  
  // 判断收缩压状态
  let sStatus = 'out_of_range';
  if (systolic >= systolic_healthy[0] && systolic <= systolic_healthy[1]) {
    sStatus = 'healthy';
  } else if (systolic >= systolic_borderline[0] && systolic <= systolic_borderline[1]) {
    sStatus = 'borderline';
  }
  
  // 判断舒张压状态
  let dStatus = 'out_of_range';
  if (diastolic >= diastolic_healthy[0] && diastolic <= diastolic_healthy[1]) {
    dStatus = 'healthy';
  } else if (diastolic >= diastolic_borderline[0] && diastolic <= diastolic_borderline[1]) {
    dStatus = 'borderline';
  }
  
  // 组合规则：最差状态优先
  if (sStatus === 'out_of_range' || dStatus === 'out_of_range') {
    return 'out_of_range';
  }
  if (sStatus === 'borderline' || dStatus === 'borderline') {
    return 'borderline';
  }
  return 'healthy';
};
```

## 优势分析

### 1. 数据一致性
- ✅ 标准更新后，所有历史记录自动使用新标准评估
- ✅ 无需批量更新数据库
- ✅ 避免数据不同步问题

### 2. 灵活性
- ✅ 可以随时切换不同的评估标准
- ✅ 支持"如果用2020标准，我的历史数据如何？"这样的场景
- ✅ 便于A/B测试不同阈值方案

### 3. 存储优化
- ✅ 减少数据库列（从11列降至9列）
- ✅ 避免冗余存储计算结果
- ✅ 数据库体积更小

### 4. 维护性
- ✅ 前端计算逻辑独立、易测试
- ✅ 后端无需关心状态计算
- ✅ 业务规则变更只需修改前端

## 性能考虑

### 潜在问题
- 每次渲染都需要计算（N条记录 × 3次判断）

### 优化方案
1. **React Memoization**：使用 `useMemo` 缓存计算结果
2. **批量计算**：一次获取配置后批量处理所有记录
3. **Web Worker**：大数据量时在后台线程计算

```javascript
// 优化示例
const recordsWithStatus = useMemo(() => {
  if (!activeThreshold) return records;
  return records.map(record => ({
    ...record,
    status: computeThresholdStatus(
      record.systolic,
      record.diastolic,
      record.heart_rate,
      activeThreshold
    )
  }));
}, [records, activeThreshold]);
```

## 特殊场景处理

### 1. 无活跃配置
```javascript
if (!activeThreshold) {
  // 不显示状态标签，只显示原始数值
  return `${systolic}/${diastolic} mmHg`;
}
```

### 2. 配置加载失败
```javascript
try {
  const config = await getActiveThreshold();
} catch (error) {
  // 降级方案：使用默认阈值或不显示状态
  console.log('Using default thresholds or no status');
}
```

### 3. 离线模式
- 可以缓存最后一次的阈值配置到 `localStorage`
- 离线时使用缓存配置进行计算

## Preview 接口特例

**唯一例外**：`GET /api/v1/thresholds/preview` 接口仍然返回 `threshold_status`

```javascript
GET /api/v1/thresholds/preview?draft_id=1&sample=30
Response:
{
  "preview": [
    {
      "id": 1,
      "systolic": 110,
      "diastolic": 75,
      "threshold_status": "healthy"  // ✅ Preview 接口特殊处理
    }
  ]
}
```

**原因**：
- Preview 是临时查看草稿效果的场景
- 用于对比"如果启用这个草稿，会影响多少记录"
- 前端不需要重新计算，后端一次性返回结果更高效

## 数据库迁移

### 移除的列
```sql
-- 不再需要这两列
ALTER TABLE health_records DROP COLUMN threshold_status;
ALTER TABLE health_records DROP COLUMN threshold_version;
```

### 迁移脚本
如果已部署旧版本，需要平滑迁移：
1. 部署新版前端（兼容有/无 threshold 字段）
2. 验证前端动态计算正常
3. 部署新版后端（移除字段返回）
4. 数据库迁移（删除列）

## 测试策略

### 单元测试
- ✅ 测试 `computeThresholdStatus` 各种边界值
- ✅ 测试状态颜色和文本映射

### E2E 测试
- ✅ 验证健康记录页面能正确显示状态标签
- ✅ 验证标准更新后，历史记录状态自动更新
- ❌ 不再测试后端返回 `threshold_status` 字段

## 相关文件

| 类型 | 文件 | 说明 |
|-----|------|------|
| 前端计算 | `frontend/src/utils/thresholdCalculator.js` | 动态计算逻辑 |
| 前端页面 | `frontend/src/pages/HealthRecords.js` | 使用动态计算 |
| 后端模型 | `src/models.py` | 移除 threshold 列 |
| 后端管理 | `src/manager/health_manager.py` | 移除自动计算 |
| 后端服务 | `src/service/health_service.py` | 移除字段序列化 |
| E2E 测试 | `tests/e2e/tests/threshold-governance.spec.js` | 更新断言 |

## 总结

这个新架构体现了"关注点分离"的设计原则：
- **后端**：负责存储和查询原始数据
- **前端**：负责呈现和业务规则计算
- **配置**：独立管理，随时更新

用户体验上：
- 🎯 标准更新后，历史数据立即反映新标准
- 🎯 无需等待后台批量更新任务
- 🎯 性能影响微乎其微（<1ms per record）
