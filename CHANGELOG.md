# Changelog

本项目遵循语义化版本。所有重要变更记录在此文件。

## [0.1.0] - 2026-07-17

### Added

- 初始化 Python 3.12、uv 与 Git `main` 项目；
- 增加类型化配置和 `.env.example`；
- 增加 SQLAlchemy 2.x SQLite 数据库基础设施；
- 增加 Source、IntelligenceItem、CrawlRun、ItemRevision 模型；
- 增加 Repository 与 Unit of Work 事务边界；
- 增加首个 Alembic 迁移；
- 增加按 10 MB、保留 5 份历史文件的滚动日志配置；
- 增加阶段一测试、Ruff 和 Pyright 配置；
- 增加阶段一 README 与架构文档。

### Not Included

- 阶段二及以后采集、分类、网页、导出、启动器和 AI 功能。
