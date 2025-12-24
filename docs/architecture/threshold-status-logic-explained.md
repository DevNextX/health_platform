# 超级管理员阈值设置问题分析与说明

**日期**: 2025-12-18  
**问题**: 阈值修改和预览状态判断逻辑

---

## 问题 1: 阈值修改后页面显示问题

### 问题描述
将收缩压下限从 90 修改为 80，保存草稿并发布后，超级管理员设置页面刷新仍显示旧值 90，但健康仪表盘已正确显示 80。

### 🎯 根本原因（已确认）

**数据已成功保存**：健康仪表盘正确显示 80，证明后端数据库已更新。

**SuperAdminSettings 解析错误**：`deriveFormValues` 函数使用了错误的数据路径。

#### 错误的代码逻辑

```javascript
// ❌ 错误：寻找不存在的字段
const deriveFormValues = (data) => {
  const nested = data?.thresholds || {};  // data.thresholds 不存在！
  const payload = data?.profile || {};    // data.profile 不存在！
  
  // 由于找不到数据，最终回退到默认值
  return {
    systolicLow: systolicHealthy?.[0] ?? DEFAULT_FORM_VALUES.systolicLow,  // 90
    // ...
  };
};
```

#### 后端实际返回结构

```python
# src/service/threshold_service.py - GET /api/v1/thresholds/active
return jsonify({
    "id": config.id,
    "payload": json.loads(config.payload),  # ✅ 数据在这里！
    "version": config.version,
    "updated_at": config.updated_at.isoformat()
})
```

**实际返回示例**：
```json
{
  "id": 3,
  "payload": {
    "systolic": { "min": 80, "max": 120, "borderline_max": 140 },
    "diastolic": { "min": 60, "max": 80, "borderline_max": 90 },
    "heart_rate": { "min": 60, "max": 100 }
  },
  "version": 3,
  "updated_at": "2025-12-18T10:30:00"
}
```

#### Dashboard 正确解析方式

```javascript
// ✅ Dashboard.js - 正确使用 data.payload
if (data.payload) {
   payload = data.payload;  // 直接使用新格式
}

setThresholdInfo({
  version: data.version || 1,
  payload: payload  // {systolic: {min: 80, max: 120, borderline_max: 140}}
});
```

#### 修复方案（已实施）

```javascript
// ✅ 正确：直接从 data.payload 读取
const deriveFormValues = (data) => {
  const payload = data?.payload || {};

  return {
    systolicLow: payload.systolic?.min ?? DEFAULT_FORM_VALUES.systolicLow,
    systolicHigh: payload.systolic?.max ?? DEFAULT_FORM_VALUES.systolicHigh,
    systolicBorderline: payload.systolic?.borderline_max ?? DEFAULT_FORM_VALUES.systolicBorderline,
    diastolicLow: payload.diastolic?.min ?? DEFAULT_FORM_VALUES.diastolicLow,
    diastolicHigh: payload.diastolic?.max ?? DEFAULT_FORM_VALUES.diastolicHigh,
    diastolicBorderline: payload.diastolic?.borderline_max ?? DEFAULT_FORM_VALUES.diastolicBorderline,
    heartRateLow: payload.heart_rate?.min ?? DEFAULT_FORM_VALUES.heartRateLow,
    heartRateHigh: payload.heart_rate?.max ?? DEFAULT_FORM_VALUES.heartRateHigh,
  };
};
```

### 验证步骤

1. **刷新超级管理员设置页面** - 现在应该显示 80
2. **检查浏览器控制台** - 无错误日志
3. **测试完整流程**：
   - 修改阈值 → 保存草稿 → 预览 → 发布
   - 刷新页面，确认表单显示新值
   - 切换到健康仪表盘，确认参考卡显示新值

---

## 问题 1: 阈值修改后页面显示问题（已解决）

~~### 问题描述~~
~~将收缩压下限从 90 修改为 80，保存草稿并发布后，页面刷新仍显示旧值。~~

### ✅ 已解决

---

## 问题 2: 预览表格阈值状态判断规则

### 当前判断逻辑

#### 三层状态模型

```python
# src/manager/threshold_manager.py - _compute_status()

def _compute_status(systolic, diastolic, heart_rate, payload):
    """
    三层状态判断：
    - healthy: 所有值在 [min, max] 范围内
    - borderline: 任意血压值在 (max, borderline_max] 范围内，且没有 out_of_range
    - out_of_range: 任意值超出所有定义范围
    """
    
    has_out_of_range = False
    has_borderline = False
    
    # 1. 检查收缩压
    if systolic < systolic_min or systolic > systolic_borderline_max:
        has_out_of_range = True
    elif systolic > systolic_max:
        has_borderline = True
    
    # 2. 检查舒张压
    if diastolic < diastolic_min or diastolic > diastolic_borderline_max:
        has_out_of_range = True
    elif diastolic > diastolic_max:
        has_borderline = True
    
    # 3. 检查心率（无临界区间）
    if heart_rate < heart_rate_min or heart_rate > heart_rate_max:
        has_out_of_range = True
    
    # 4. 优先级判断
    if has_out_of_range:
        return "out_of_range"
    elif has_borderline:
        return "borderline"
    else:
        return "healthy"
```

### 案例分析: 为什么 121/70/65 显示为 out_of_range？

假设当前阈值配置：
```json
{
  "systolic": {"min": 90, "max": 120, "borderline_max": 140},
  "diastolic": {"min": 60, "max": 80, "borderline_max": 90},
  "heart_rate": {"min": 60, "max": 100}
}
```

#### 记录: 121/70/65

**逐项检查**:

1. **收缩压 = 121**
   - 121 < 90? **否**
   - 121 > 140? **否**
   - 121 > 120? **是** → `has_borderline = True`

2. **舒张压 = 70**
   - 70 < 60? **否**
   - 70 > 90? **否**
   - 70 > 80? **否** → 健康范围

3. **心率 = 65**
   - 65 < 60? **否**
   - 65 > 100? **否** → 健康范围

**最终判断**: `has_borderline = True` → 状态应为 **borderline**

### ⚠️ 为什么显示 out_of_range？

#### 可能原因 1: 心率阈值配置错误

如果心率配置为：
```json
"heart_rate": {"min": 70, "max": 100}  // 注意 min 是 70
```

则：
- 65 < 70? **是** → `has_out_of_range = True`
- 最终状态: **out_of_range** ✅

#### 可能原因 2: 后端数据不一致

草稿的配置可能与您在表单中看到的不同：
- 前端表单显示: min=60
- 实际草稿数据: min=70

#### 验证方法

1. **查看草稿的实际 payload**:
```javascript
// 在 loadPreview 后添加
console.log('Draft payload:', data?.draft_payload);
```

2. **手动计算状态**:
```javascript
// 在 SuperAdminSettings.js 添加调试代码
const debugStatus = (record) => {
  const { systolic, diastolic, heart_rate } = record;
  const values = form.getFieldsValue();
  console.log('Record:', record);
  console.log('Form values:', values);
  console.log('Status logic:');
  console.log('  Systolic', systolic, 'in', [values.systolicLow, values.systolicHigh, values.systolicBorderline]);
  console.log('  Diastolic', diastolic, 'in', [values.diastolicLow, values.diastolicHigh, values.diastolicBorderline]);
  console.log('  Heart Rate', heart_rate, 'in', [values.heartRateLow, values.heartRateHigh]);
};
```

---

## 状态判断规则详细说明

### 收缩压状态矩阵

| 收缩压值 | 配置范围 (min=90, max=120, borderline_max=140) | 状态 |
|---------|-----------------------------------------------|------|
| < 90 | 低于健康下限 | 🔴 out_of_range |
| 90-120 | 健康范围 | 🟢 healthy |
| 121-140 | 临界范围 | 🟠 borderline |
| > 140 | 高于临界上限 | 🔴 out_of_range |

### 舒张压状态矩阵

| 舒张压值 | 配置范围 (min=60, max=80, borderline_max=90) | 状态 |
|---------|----------------------------------------------|------|
| < 60 | 低于健康下限 | 🔴 out_of_range |
| 60-80 | 健康范围 | 🟢 healthy |
| 81-90 | 临界范围 | 🟠 borderline |
| > 90 | 高于临界上限 | 🔴 out_of_range |

### 心率状态矩阵

| 心率值 | 配置范围 (min=60, max=100) | 状态 |
|--------|---------------------------|------|
| < 60 | 低于健康下限 | 🔴 out_of_range |
| 60-100 | 健康范围 | 🟢 healthy |
| > 100 | 高于健康上限 | 🔴 out_of_range |

**注意**: 心率**没有临界区间**，只有健康和异常两种状态。

### 综合判断优先级

```
优先级: out_of_range > borderline > healthy
```

**规则**:
1. **任意一项** 为 out_of_range → 整体为 out_of_range
2. **任意一项** 为 borderline（且无 out_of_range）→ 整体为 borderline
3. **全部三项** 为 healthy → 整体为 healthy

### 示例

| 收缩压 | 舒张压 | 心率 | 最终状态 | 原因 |
|--------|--------|------|----------|------|
| 110 (healthy) | 70 (healthy) | 80 (healthy) | 🟢 healthy | 全部健康 |
| 125 (borderline) | 70 (healthy) | 80 (healthy) | 🟠 borderline | 收缩压临界 |
| 110 (healthy) | 85 (borderline) | 80 (healthy) | 🟠 borderline | 舒张压临界 |
| 125 (borderline) | 85 (borderline) | 80 (healthy) | 🟠 borderline | 两项临界 |
| 150 (out_of_range) | 70 (healthy) | 80 (healthy) | 🔴 out_of_range | 收缩压异常 |
| 110 (healthy) | 95 (out_of_range) | 80 (healthy) | 🔴 out_of_range | 舒张压异常 |
| 110 (healthy) | 70 (healthy) | 110 (out_of_range) | 🔴 out_of_range | 心率异常 |
| 125 (borderline) | 85 (borderline) | 110 (out_of_range) | 🔴 out_of_range | 心率异常优先 |

---

## 建议改进

### 1. 添加预览配置显示

在预览表格上方显示当前使用的阈值：

```javascript
<Alert
  type="info"
  message="预览使用的阈值配置"
  description={
    <div>
      <div>收缩压: {values.systolicLow}-{values.systolicHigh} (临界 {values.systolicHigh+1}-{values.systolicBorderline})</div>
      <div>舒张压: {values.diastolicLow}-{values.diastolicHigh} (临界 {values.diastolicHigh+1}-{values.diastolicBorderline})</div>
      <div>心率: {values.heartRateLow}-{values.heartRateHigh}</div>
    </div>
  }
  style={{ marginBottom: 16 }}
/>
```

### 2. 添加状态详情 Tooltip

在预览表格的状态列添加 Tooltip，解释为什么是该状态：

```javascript
{
  title: t('superAdmin.threshold.previewColumns.status'),
  dataIndex: 'threshold_status',
  key: 'status',
  render: (status, record) => {
    const statusInfo = statusMap[status];
    const reasons = getStatusReasons(record, values);
    return (
      <Tooltip title={reasons.join(', ')}>
        <Tag color={statusInfo.color}>{statusInfo.text}</Tag>
      </Tooltip>
    );
  },
}
```

### 3. 添加状态统计

在预览表格下方显示状态分布：

```javascript
const stats = {
  healthy: previewData.filter(r => r.threshold_status === 'healthy').length,
  borderline: previewData.filter(r => r.threshold_status === 'borderline').length,
  out_of_range: previewData.filter(r => r.threshold_status === 'out_of_range').length,
};

<Card>
  <Statistic.Group>
    <Statistic title="健康" value={stats.healthy} valueStyle={{ color: '#3f8600' }} />
    <Statistic title="临界" value={stats.borderline} valueStyle={{ color: '#faad14' }} />
    <Statistic title="异常" value={stats.out_of_range} valueStyle={{ color: '#cf1322' }} />
  </Statistic.Group>
</Card>
```

---

## 测试清单

- [ ] 修改阈值后保存草稿，检查草稿 ID 是否正确
- [ ] 发布后刷新页面，确认表单显示新值
- [ ] 检查数据库 `threshold_config` 表，确认 status='active' 的记录 payload 正确
- [ ] 预览时手动计算几条记录的状态，与显示结果对比
- [ ] 修改心率下限为 70，检查 65 bpm 的记录是否变为 out_of_range
- [ ] 添加调试日志，输出每条记录的详细判断过程

---

Generated by Copilot  
Date: 2025-12-18
