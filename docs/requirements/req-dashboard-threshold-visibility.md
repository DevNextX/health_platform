# 需求：仪表盘健康阈值可视化与临界状态治理

- **状态**: 草稿
- **关联**: 
    - `/docs/requirements/req-threshold-config-governance.md` (阈值配置)
    - `/docs/requirements/req-health-record-validation-update.md` (输入校验)

## 背景
当前用户在仪表盘查看健康记录时，缺乏明确的健康标准参考。用户无法直观了解当前的“健康”、“临界”和“异常”范围具体是多少。此外，现有的状态判定逻辑（仅红/绿）不足以反映“临界”（Borderline）状态，导致用户对轻微超标产生不必要的恐慌或忽视。

## 业务价值
- **透明度**: 让用户清晰知晓当前的判定标准。
- **准确性**: 引入“临界”状态，更符合医疗场景（如高血压前期）。
- **可配置性**: 配合超级管理员配置功能，实现标准的动态调整与实时展示。

## 范围

### 范围内
- **仪表盘显示**: 在仪表盘顶部显著位置展示当前的健康标准参考卡片。
    - 显示内容：版本号、收缩压健康/临界范围、舒张压健康/临界范围。
- **状态判定逻辑升级**:
    - **健康 (Healthy)**: 在健康范围内 (Green)。
    - **临界 (Borderline)**: 超出健康范围但未达到异常极值 (Orange)。
    - **异常 (Out of Range)**: 超出临界范围 (Red)。
- **超级管理员配置升级**:
    - 配置表单需支持设置“健康范围”和“临界范围”（或自动推导）。
    - *注：为简化交互，建议配置“健康上限”和“临界上限”。例如：健康 90-120，临界 121-140。则 <90 或 >140 为异常。*

### 验收标准 (Acceptance Criteria)

#### 1. 仪表盘参考卡片 (Dashboard Reference Card)
- **AC1.1**: 仪表盘顶部增加 "Health Standards Reference" 区域。
- **AC1.2**: 展示当前生效的配置版本 (Version)。
- **AC1.3**: 清晰展示收缩压 (Systolic) 和 舒张压 (Diastolic) 的范围：
    - **Healthy**: [Min, Max] (e.g., 90-120) - 绿色图标/文字
    - **Borderline**: [Max+1, BorderlineMax] (e.g., 121-140) - 橙色图标/文字
    - **Out of Range**: < Min 或 > BorderlineMax - 红色图标/文字
- **AC1.4**: 若未配置或获取失败，显示默认占位符或提示，不应报错。

#### 2. 状态判定逻辑 (Status Logic)
- **AC2.1**: 系统根据以下逻辑判定单条记录状态：
    - **Systolic**:
        - Healthy: 90 <= val <= 120
        - Borderline: 121 <= val <= 140
        - Abnormal: val < 90 OR val > 140
    - **Diastolic**:
        - Healthy: 60 <= val <= 80
        - Borderline: 81 <= val <= 90
        - Abnormal: val < 60 OR val > 90
- **AC2.2**: 综合状态取“最差”原则（Worst Case）：
    - 若任一指标为 Abnormal -> Abnormal
    - 若任一指标为 Borderline 且无 Abnormal -> Borderline
    - 仅当两者均为 Healthy -> Healthy

#### 3. 列表与图表适配
- **AC3.1**: 历史记录列表中的 Tag 颜色应适配新逻辑 (Green/Orange/Red)。
- **AC3.2**: 趋势图的点颜色应适配新逻辑。

## 数据结构变更 (JSON Payload)
建议 `ThresholdConfig.payload` 结构扩展：
```json
{
  "systolic": {
    "healthy_min": 90,
    "healthy_max": 120,
    "borderline_max": 140
  },
  "diastolic": {
    "healthy_min": 60,
    "healthy_max": 80,
    "borderline_max": 90
  },
  "heart_rate": {
    "min": 60,
    "max": 100
  }
}
```
*注：心率通常仅有正常范围，超出即异常，暂不引入临界。*

## 风险
- **配置复杂性**: 管理员需要理解三个边界值。需在 UI 上提供清晰的图示或引导。
