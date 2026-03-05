# Bug Report: 既往病史页面中文文案显示异常（Action/Confirm 误用）

## 基本信息
- 类型: Bug
- 严重级别: Medium
- 优先级: High
- 影响范围: 前端 `MedicalHistory` 页面（中英文均受影响，中文更明显）

## 问题描述
在中文版“既往病史”页面中，存在两处文案问题：
1. 表格操作列标题写死为英文 `Actions`，未走国际化。
2. 新增/编辑弹窗必填校验文案误用了 `common.confirm`，导致出现“疾病名称 确认”一类不符合语义的提示。

这与“健康记录”页面的国际化风格不一致。

## 复现步骤
1. 切换系统语言为中文。
2. 打开“既往病史”页面。
3. 点击“新增病史”，不填必填字段直接提交。
4. 观察表格列头和表单校验提示。

## 实际结果
- 表格列头显示 `Actions`。
- 必填提示使用了“确认”语义，不符合“必填”语义。

## 预期结果
- 表格操作列应显示中文“操作”（或按当前语言自动切换）。
- 必填提示应为“{{field}}为必填项”类语义。

## 根因分析
- `frontend/src/pages/MedicalHistory.js` 中操作列标题使用硬编码字符串。
- 同文件中 `Form.Item` 校验消息使用错误 i18n key（`common.confirm`）。

## 修复方案
- 将操作列标题改为 `t('health.columns.actions')`。
- 新增 i18n key：
  - `common.requiredField`
  - `common.maxLength`
- 替换 `MedicalHistory` 页面中的相关校验消息为正确语义。

## 影响与回归
- 仅前端 UI 文案，不影响后端接口与数据。
- 建议手工回归：中文/英文语言切换下新增和编辑流程。

## 关联文件
- `frontend/src/pages/MedicalHistory.js`
- `frontend/src/i18n/locales/zh/translation.json`
- `frontend/src/i18n/locales/en/translation.json`
