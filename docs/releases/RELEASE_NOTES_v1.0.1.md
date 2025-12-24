# Release Notes - v1.0.1

发布日期：2025-12-24

## 概述
本版本为 Patch 发布（1.0.0 → 1.0.1），聚焦于补齐批量处理能力与修复“重复记录”问题，提升数据一致性与导入体验。

## 变更摘要

## 关联 Issue
- 批量上传/导入（Batch Import）：https://github.com/DevNextX/health_platform/issues/79
- 重复记录防护（Duplicate Prevention）：https://github.com/DevNextX/health_platform/issues/87

### 新增功能
- 健康记录批量导入：支持 Excel/CSV 上传导入、模板下载、数据校验、错误报告与错误导出。（Issue: https://github.com/DevNextX/health_platform/issues/79）
  - 参考文档：`docs/BATCH_IMPORT.md`

### 修复
- 重复记录防护：同一成员在同一分钟内的重复记录将被拦截。（Issue: https://github.com/DevNextX/health_platform/issues/87）
- 批量导入重复处理：若导入数据与已有记录重复，将自动跳过并在汇总中体现。（Issue: https://github.com/DevNextX/health_platform/issues/87）
  - 参考测试/说明：`docs/DUPLICATE_RECORDS_FIX_REPORT.md`

## 兼容性说明
- 无 Breaking Changes。
- 历史数据本身不自动修改；如数据库中已有重复数据，建议按“升级步骤”执行一次清理。

## 升级步骤（建议）
1) 备份数据库（必做）
- SQLite：备份 `src/instance/health_platform.db`
- MySQL：使用现有备份方案（如 `mysqldump`）

2) 拉取代码并安装依赖
- `pip install -r requirements.txt`

3) 数据库迁移
- `flask db upgrade`

4) 清理历史重复数据（如需要）
- 预览：`.venv\Scripts\python.exe scripts\clean_duplicate_records.py --dry-run`
- 执行：`.venv\Scripts\python.exe scripts\clean_duplicate_records.py`
- 复核：再次 `--dry-run` 应输出无重复

5) 版本确认
- 调用 `GET /api/v1/version` 应返回 `1.0.1`

## 回归验证清单
- 单条创建：同一成员、同一分钟重复创建应返回 400（或对应业务错误）。
- 批量导入：重复行应被跳过，汇总中 `skipped_count`（或等价字段）递增，且不影响非重复行导入。
- Dashboard/列表：导入后记录数与预期一致。

## 发布流程（按仓库规范）
仓库已有发布约定（见 `CONTRIBUTING.md`），建议执行：
1) 更新 `VERSION` 与 `CHANGELOG.md`
2) 提交：`git commit -m "chore: release v1.0.1"`
3) 打标签：`git tag v1.0.1`
4) 推送：`git push origin main --tags`

> 如有 CI/CD：确保 tag 对应构建通过后再部署生产。
