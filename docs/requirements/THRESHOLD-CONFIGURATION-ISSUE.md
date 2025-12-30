# 健康阈值配置问题分析与解决方案

## 问题描述

管理员在"超级管理员设置"页面中配置的血压和心率范围，与仪表盘显示的"健康"和"临界"范围之间存在理解困惑。

### 当前状态

**管理员配置界面**：
- 收缩压：下限 90，上限 120
- 舒张压：下限 60，上限 80  
- 心率：下限 60，上限 90

**仪表盘显示**：
- 收缩压：健康 90-120，临界 121-140
- 舒张压：健康 60-80，临界 81-90

## 根本原因

### 1. 数据结构不一致

**数据库中的实际存储结构**（由 `scripts/init_thresholds.py` 初始化）：
```json
{
  "systolic": {
    "min": 90,           // 健康下限
    "max": 120,          // 健康上限
    "borderline_max": 140 // 临界上限
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

**管理员配置页面使用的API结构**（`SuperAdminSettings.js` 发送给后端）：
```javascript
{
  "thresholds": {
    "systolic": {
      "lower": 90,   // 仅两个值
      "upper": 120
    },
    "diastolic": {
      "lower": 60,
      "upper": 80
    },
    "heart_rate": {
      "lower": 60,
      "upper": 90
    }
  }
}
```

### 2. 配置界面缺少"临界上限"字段

超级管理员配置页面**只提供了**：
- 下限（Lower Bound）→ 对应数据库的 `min`
- 上限（Upper Bound）→ 对应数据库的 `max`

**缺少**：
- 临界上限（Borderline Max）→ 数据库中的 `borderline_max` 字段

### 3. 临界范围的来源

仪表盘显示的"临界 121-140"来自：
1. 初始化脚本 `scripts/init_thresholds.py` 写入的默认 `borderline_max` 值
2. 这个值**无法通过管理员界面修改**
3. 即使管理员保存了新的配置，`borderline_max` 仍然保留旧值

## 业务逻辑说明

### 状态判定规则（`thresholdCalculator.js`）

对于收缩压 Systolic（以 min=90, max=120, borderline_max=140 为例）：

| 血压值 | 状态 | 颜色 | 说明 |
|--------|------|------|------|
| < 90 | Out of Range（异常） | 红色 | 低于健康下限 |
| 90 - 120 | Healthy（健康） | 绿色 | 在健康范围内 |
| 121 - 140 | Borderline（临界） | 橙色 | 超出健康但未达极端 |
| > 140 | Out of Range（异常） | 红色 | 高于临界上限 |

### 预期的完整配置项

每个指标应该配置**三个关键值**：
1. **健康下限**（min）：低于此值为异常（低）
2. **健康上限**（max）：健康范围的上界
3. **临界上限**（borderline_max）：临界范围的上界，超过为异常（高）

## 解决方案

### 方案 A：扩展管理员配置界面（推荐）

**优点**：
- 提供完整的配置能力
- 符合"临界"状态的医学场景
- 用户可灵活调整三级阈值

**需要修改**：
1. `SuperAdminSettings.js`：增加"临界上限"输入字段
2. `buildPayload` 函数：发送 `borderline_max`
3. 后端 `ThresholdManager`：验证 `max < borderline_max`
4. i18n 翻译：增加"临界上限"标签

**示例 UI**：
```
收缩压健康范围 (mmHg)
├─ 下限：[90]
├─ 上限：[120]
└─ 临界上限：[140]  ← 新增字段
```

### 方案 B：简化为二级阈值

**优点**：
- 界面简单
- 仅需修改仪表盘显示逻辑

**缺点**：
- 失去"临界"状态，仅有健康/异常
- 不符合医学场景（如高血压前期）

**需要修改**：
1. 移除 `borderline_max` 字段
2. `HealthStandardsReference.js`：不显示临界范围
3. `thresholdCalculator.js`：简化为二元判定

## 推荐实施步骤（方案 A）

### Phase 1: 扩展前端配置表单
- [ ] 在 `SuperAdminSettings.js` 中增加三个字段：
  - `systolicBorderline`
  - `diastolicBorderline`
  - `heartRateBorderline` (可选)
- [ ] 添加校验规则：`max < borderline_max`
- [ ] 更新 `buildPayload` 函数

### Phase 2: 更新后端验证
- [ ] 修改 `ThresholdManager.validate_config`
- [ ] 支持新的 payload 结构

### Phase 3: 数据迁移
- [ ] 确保现有数据包含 `borderline_max`
- [ ] 为心率增加 `borderline_max`（可选）

### Phase 4: 测试
- [ ] 管理员保存配置后，验证数据库包含三个值
- [ ] 仪表盘验证显示逻辑正确
- [ ] E2E 测试覆盖新字段

## 相关文件

- **前端配置页面**：`frontend/src/pages/SuperAdminSettings.js`
- **仪表盘展示**：`frontend/src/components/HealthStandardsReference.js`
- **状态计算**：`frontend/src/utils/thresholdCalculator.js`
- **后端验证**：`src/manager/threshold_manager.py`
- **初始化脚本**：`scripts/init_thresholds.py`

## 临时建议

在完整修复前，建议在管理员配置页面添加以下提示：

> **注意**：当前仅可配置"健康范围"（下限-上限）。系统会自动设置"临界范围"（上限+1 至默认临界值）。如需调整临界上限，请联系技术支持。

---

**结论**：当前系统存在配置项不完整的问题，导致管理员无法理解仪表盘显示的"临界"范围从何而来。推荐实施方案 A，为管理员提供完整的三级阈值配置能力。
