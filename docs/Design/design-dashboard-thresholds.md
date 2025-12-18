# 设计文档：仪表盘阈值展示与临界逻辑

## 1. 数据模型设计 (Data Model)

### ThresholdConfig Payload
我们将采用嵌套对象结构来存储阈值配置，以支持更丰富的元数据。

```json
{
  "systolic": {
    "min": 90,          // Healthy Min (Below = Abnormal Low)
    "max": 120,         // Healthy Max
    "borderline_max": 140 // Borderline Max (Above = Abnormal High)
  },
  "diastolic": {
    "min": 60,
    "max": 80,
    "borderline_max": 90
  },
  "heart_rate": {
    "min": 60,
    "max": 100
  }
}
```

**状态判定逻辑**:
- **Healthy**: `min <= val <= max`
- **Borderline**: `max < val <= borderline_max`
- **Abnormal**: `val < min` OR `val > borderline_max`

## 2. 前端架构 (Frontend Architecture)

### 2.1 工具库 (`utils/thresholdCalculator.js`)
需要重构以适配新的 Payload 结构。

```javascript
export const computeThresholdStatus = (systolic, diastolic, heartRate, config) => {
    // ... parsing logic ...
    // Returns: 'healthy' | 'borderline' | 'out_of_range'
}
```

### 2.2 新组件 (`components/HealthStandardsReference.js`)
用于在仪表盘顶部展示当前标准。

**UI Layout**:
- Card / Alert style
- Title: "Health Standards Reference (v{version})"
- Grid layout:
    - **Systolic**: Healthy 90-120 | Borderline 121-140
    - **Diastolic**: Healthy 60-80 | Borderline 81-90

### 2.3 页面集成 (`pages/HealthRecords.js`)
- 在 `fetchActiveThreshold` 获取配置后，将其传递给 `HealthStandardsReference`。
- 将配置传递给 `HealthChart` 和 `HealthList` (或 Table render) 用于实时计算颜色。

## 3. 后端变更 (Backend Changes)

### 3.1 初始化数据
- 更新 `scripts/init_thresholds.py` (如果存在) 或迁移脚本，确保默认数据符合新结构。

### 3.2 校验逻辑
- `ThresholdManager` 需校验 `min < max < borderline_max`。

## 4. 交互流程
1. **Admin** 配置 `min`, `max`, `borderline_max`。
2. **Backend** 保存 JSON。
3. **Frontend** 获取 JSON。
4. **Dashboard** 解析 JSON -> 展示 Reference Card -> 计算每条记录颜色。
