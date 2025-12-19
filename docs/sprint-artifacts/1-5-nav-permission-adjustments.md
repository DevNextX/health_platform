# Story 1.5: 导航与权限调整

Status: drafted

## Story

作为平台超级管理员，我希望侧边导航能区分个人用户设置与超级管理员阈值配置入口，并根据角色隐藏不应访问的菜单，这样每个用户都能快速找到自己的设置，且阈值治理功能只对授权角色开放。

## Acceptance Criteria

1. 侧边导航中的“Settings” 标签被替换为 “User Setting”，普通用户与管理员点击后仍然进入现有用户设置页面（语言、密码等）。
2. “User Management” 菜单依旧仅对管理员/超级管理员显示，行为与现状一致。
3. 新增 “Super Admin Setting” 菜单，仅超级管理员可见；点击后跳转到 `/super-admin/settings` 页面，非超级管理员访问该路由时被重定向或显示无权限提示。

## Tasks / Subtasks

- [ ] 更新导航菜单与翻译资源（AC 1, AC 2）
  - [ ] 在 `frontend/src/components/Layout.js` 中将 `nav.settings` 调整为新的 `menu.userSetting` 文案，并保留原 `/settings` 路径
  - [ ] 更新 `frontend/src/i18n/locales/en/translation.json` 与 `zh/translation.json`，新增 `nav.userSetting`、`nav.superAdminSetting` 键值，保持 `nav.adminUsers` 不变
  - [ ] 确认 `useTranslation` 消费的 key 变更不会影响现有页面标题与面包屑
- [ ] 新增超级管理员设置页面及路由（AC 3）
  - [ ] 创建 `frontend/src/pages/SuperAdminSettings.js` 占位组件，为后续阈值治理故事提供容器
  - [ ] 在 `frontend/src/App.js` 中引入该页面，并添加受保护路由 `/super-admin/settings`
  - [ ] 在 `Layout.js` 的 `menuItems` 中依据 `getRoleFromToken()` 判断是否向超级管理员渲染新菜单
  - [ ] 为非 SUPER_ADMIN 角色访问 `/super-admin/settings` 提供防护逻辑（重定向到 `/dashboard` 或展示 403 提示）
- [ ] 权限与 UI 回归验证（AC 1~3）
  - [ ] 编写或更新前端测试（推荐在 `frontend/src/components/__tests__/Layout.test.js` 新增用例）验证不同角色的菜单可见性
  - [ ] 手动/自动检查 i18n 切换后菜单名称正确显示
  - [ ] 验证首次登录强制改密逻辑仍指向 `/settings`（User Setting 页面）

## Dev Notes

- 页面结构：继续复用 `Layout` 组件的菜单生成逻辑，新增超级管理员菜单时需同步考虑移动端抽屉模式（`Drawer`）和桌面侧边栏。
- 新路由应复用 `ProtectedRoute` 组件，同时增加一个 role guard（可在 `SuperAdminSettings` 内部或外部封装）。
- 用户设置页面路径仍为 `/settings`，只更换 i18n 文案，确保 `mustChange` 引导逻辑不受影响。[Source: frontend/src/components/Layout.js]
- 后续故事（例如 1.1 阈值配置界面）将在 `SuperAdminSettings` 页面内填充表单，此故事需为其留出主内容容器与标题。[Source: docs/epics.md#史诗-1：超级管理员阈值治理中心]

### Project Structure Notes

- 新增文件建议路径：`frontend/src/pages/SuperAdminSettings.js`，并在同目录下创建样式或复用现有样式。
- i18n Key 约定：使用 `nav.userSetting`、`nav.superAdminSetting`，保持命名一致方便后续翻译维护。
- 如果需复用基础布局，可考虑抽离 `Menu` 配置为常量并在测试中复用，避免重复逻辑。

### References

- [Source: docs/prd.md#用户体验原则] —— 明确新增 “Super Admin Setting” 页面与菜单重命名的 UX 要求。
- [Source: docs/epics.md#故事-1.5：导航与权限调整] —— 接受标准与权限约束。
- [Source: frontend/src/components/Layout.js] —— 现有菜单渲染逻辑与角色判断。
- [Source: frontend/src/App.js] —— 受保护路由定义，需追加超级管理员路由。

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Goldeneye (Preview)

### Debug Log References


### Completion Notes List


### File List

- 新增：`frontend/src/pages/SuperAdminSettings.js`
- 修改：`frontend/src/components/Layout.js`
- 修改：`frontend/src/App.js`
- 修改：`frontend/src/i18n/locales/en/translation.json`
- 修改：`frontend/src/i18n/locales/zh/translation.json`
- （待选）新增：`frontend/src/components/__tests__/Layout.test.js`
