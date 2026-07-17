# Changelog

本项目遵循语义化版本。所有重要变更记录在此文件。

## [Unreleased]

### Added

- 增加统一采集领域对象及 Collector/Fetcher Protocol；
- 增加基于 httpx AsyncClient 的 HttpFetcher、同域请求间隔和指数退避重试；
- 增加明确的 403、404、429/rate-limit、5xx、超时与网络错误类型；
- 增加 URL 解析、跟踪参数清理、查询参数保留配置和 canonicalization；
- 增加 RSS/Atom、HTML 列表与 GitHub Releases Collector；
- 增加 HTML selector、link-filter、有限分页和内嵌链接字段关联配置；
- 增加 Collector 注册/工厂机制；
- 增加固定 HTML、RSS、Atom、JSON 样本和可选真实网络集成测试；
- 增加采集器扩展与来源配置文档。

### Changed

- 增加阶段二运行依赖和 pytest-asyncio 开发依赖；
- 默认 pytest 套件跳过带 `network` 标记的实时公网测试；
- GitHub API 配额耗尽时使用公开 Releases Atom Feed 降级采集。

### Not Included

- 分类器、更新流水线、网页 UI、信息源添加向导、导出、定时任务、浏览器采集和 AI 功能。

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
