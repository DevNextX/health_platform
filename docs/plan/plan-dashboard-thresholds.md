# 实施计划：仪表盘阈值展示与临界逻辑

**基于文档**: `/docs/requirements/req-dashboard-threshold-visibility.md`

## 1. 后端数据初始化 (Backend Data Init)
- [ ] **Task 1.1**: 修改 `scripts/init_thresholds.py`。
    - 更新默认 Payload 结构，增加 `borderline_max`。
    - 默认值：
        - Systolic: 90-120 (Healthy), 140 (Borderline Max)
        - Diastolic: 60-80 (Healthy), 90 (Borderline Max)
    - 增加逻辑：如果已存在旧格式配置，自动升级或提示。

## 2. 前端逻辑升级 (Frontend Logic)
- [ ] **Task 2.1**: 重构 `frontend/src/utils/thresholdCalculator.js`。
    - 适配新的 JSON 结构 (`{ min, max, borderline_max }`)。
    - 实现新的状态判定逻辑 (Healthy/Borderline/Out of Range)。
    - 增加防御性编程，处理旧格式数据（向后兼容）。

## 3. 前端 UI 开发 (Frontend UI)
- [ ] **Task 3.1**: 创建组件 `frontend/src/components/HealthStandardsReference.js`。
    - 使用 Ant Design `Card` 或 `Alert`。
    - 展示 Systolic/Diastolic 的 Healthy 和 Borderline 范围。
    - 支持国际化 (i18n)。
- [ ] **Task 3.2**: 集成到 `frontend/src/pages/HealthRecords.js`。
    - 在页面顶部（Filters 下方或上方）引入该组件。
    - 传递 `activeThreshold` prop。

## 4. 验证 (Verification)
- [ ] **Task 4.1**: 运行 `init_thresholds.py` 重置/更新数据。
- [ ] **Task 4.2**: 启动前端，验证仪表盘顶部是否显示参考卡片。
- [ ] **Task 4.3**: 验证列表和图表中的记录颜色是否符合新逻辑（特别是 121-140 区间应为橙色）。
