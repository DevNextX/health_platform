---
title: "feat: Dashboard Threshold Visibility & Borderline Logic"
labels: "enhancement, dashboard, ux"
assignees: ""
---

## 需求概述
**基于文档**: `/docs/requirements/req-dashboard-threshold-visibility.md`

当前仪表盘缺乏健康标准参考，且状态判定逻辑过于简单（仅二元）。本功能旨在：
1. 在仪表盘显式展示当前生效的健康/临界范围。
2. 引入“临界 (Borderline)”状态，优化视觉反馈。
3. 升级超级管理员配置，支持定义临界范围。

## 任务分解

### Phase 1: Backend & Data Model
- [ ] 更新 `ThresholdConfig` 的 JSON Schema 定义，支持 `borderline_max`。
- [ ] 更新默认初始化数据 (Seed Data) 包含临界值。
- [ ] 更新 `ThresholdManager` 校验逻辑 (Healthy Max < Borderline Max)。

### Phase 2: Frontend Logic
- [ ] 更新 `thresholdCalculator.js` 适配新的 JSON 结构。
- [ ] 实现“最差状态”判定逻辑 (Worst Case Logic)。

### Phase 3: Dashboard UI
- [ ] 开发 `ReferenceCard` 组件，展示当前标准。
- [ ] 集成到 `HealthRecords` 页面顶部。
- [ ] 更新图表和列表的颜色映射。

### Phase 4: Admin UI
- [ ] 更新超级管理员配置表单，增加“临界上限”输入项。
- [ ] 增加输入联动校验。
