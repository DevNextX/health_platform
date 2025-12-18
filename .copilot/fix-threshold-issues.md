# 阈值功能修复任务

## 问题 1: 保存草稿 400 错误

**根因**: 前端发送的 payload 格式不匹配
- 前端发送: `{ thresholds: { systolic: {...}, diastolic: {...}, heart_rate: {...} } }`
- 后端期望: `{ systolic: {...}, diastolic: {...}, heart_rate: {...} }`

**修复方案**: 修改 `SuperAdminSettings.js` 的 `buildPayload` 函数，直接返回阈值对象，去掉 `thresholds` 包装层。

## 问题 2: 健康阈值参考显示不清楚

**现状**: 只显示收缩压和舒张压，缺少心率信息，且标签不够清晰

**修复方案**: 
1. 在 `HealthStandardsReference.js` 中添加心率显示
2. 使用更清晰的标题和分组
3. 添加单位说明 (mmHg, bpm)
4. 改进布局，使用卡片式分组

## 问题 3: 总记录数可点击跳转

**需求**: 点击统计卡片后跳转到健康记录页面对应的筛选视图

**修复方案**:
1. 找到 Dashboard/HealthRecords 页面的统计卡片组件
2. 添加 `onClick` 事件处理器
3. 使用 `react-router-dom` 的 `useNavigate` 进行路由跳转
4. 如果有状态筛选，通过 URL 参数传递筛选条件

## 实施顺序
1. 先修复问题 1 (阻塞性问题)
2. 再优化问题 2 (UI 改进)
3. 最后实现问题 3 (新功能)

## 需要修改的文件
- `frontend/src/pages/SuperAdminSettings.js` - 修复 payload 格式
- `frontend/src/components/HealthStandardsReference.js` - 优化显示
- `frontend/src/pages/HealthRecords.js` 或 `Dashboard.js` - 添加点击跳转
