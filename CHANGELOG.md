# Changelog

本项目遵循语义化版本。所有重要变更记录在此文件。

## [Unreleased]

### Fixed

- 修复 SQLite batch migration 在已有修订记录时可能触发级联删除的问题；
- 修复不存在来源的单来源网页更新返回 500，以及超页分页和极端输入边界；
- 修复示例来源导入对等价 URL 重复创建来源的问题，并收紧更新错误与回跳地址展示边界；

### Added

- 增加 FastAPI、Jinja2、原生 JavaScript/CSS 的本地资讯、来源和更新记录页面；
- 增加资讯数据库层服务端分页、稳定回退排序、来源联表及组合筛选；
- 增加 POST 收藏、人工分类设置/清除、来源启停和安全回跳；
- 增加复用 `UpdatePipeline` 的全量/单来源网页更新及异常安全的进程内互斥锁；
- 增加 CrawlRun 分页页面、状态标签、净化错误摘要和更新结果页面；
- 增加显式、幂等且不覆盖同 URL 来源的三个示例来源导入命令；
- 增加资讯 `updated_at` Alembic 迁移和本地网页专项测试；

- 增加共享 `UpdatePipeline`、`CrawlService`、`ClassificationService`、
  `ItemPersistenceService` 和 `CrawlRunService`；
- 增加 `UpdateResult`、`SourceUpdateResult` 与 incremental/history 更新模式；
- 增加采集后标题、URL、简介、时区和 JSON `extra` 的统一标准化与单条隔离；
- 增加稳定 source-scoped fingerprint、canonical URL 优先去重和唯一约束保存点恢复；
- 增加规则分类持久化、人工分类保护及单条/全量基础重分类服务；
- 增加只记录有效内容字段变化并可关联 CrawlRun 的 `ItemRevision`；
- 增加来源级故障隔离、错误净化、来源状态更新和完整 CrawlRun 统计；
- 增加跨来源同 URL 的额外发现来源元数据和未来 `ItemSource` 扩展说明；
- 增加 `update` / `runs` 最小开发 CLI、阶段四离线测试和临时数据库真实网络烟雾测试；
- 增加 CrawlRun 状态值兼容迁移。
- 增加 `ClassificationResult` 与异步 `Classifier` 领域接口；
- 增加从 YAML 加载的纯逻辑规则分类器及严格配置校验；
- 增加标题/简介、词组/关键词、排除词、来源默认分类、阈值、分差和优先级综合评分；
- 增加人工分类解析和最终分类优先级合成服务；
- 增加保留模型版本号的文本规范化；
- 增加 71 条固定人工标注分类样本、总体/分类别准确率和混淆统计测试；
- 增加 `LLMClassifier` 与 `HybridClassifier` 空实现和分类扩展文档；
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

- 项目进度进入阶段五 A 本地网页 UI 与基础人工操作；
- CLI 与网页通过共享应用工厂构造同一个 `UpdatePipeline`；

- CrawlRun 完成状态统一为 `success`、`partial_success` 和 `failed`；
- 项目进度进入阶段四更新流水线、分类持久化与运行记录；
- 项目进度进入阶段三分类系统子范围，阶段二 Collector 接口和行为保持不变；
- 增加 PyYAML 运行依赖和类型存根开发依赖；
- 增加阶段二运行依赖和 pytest-asyncio 开发依赖；
- 默认 pytest 套件跳过带 `network` 标记的实时公网测试；
- GitHub API 配额耗尽时使用公开 Releases Atom Feed 降级采集。
- 为 RSS/HTML 返回结果、HTML 分页队列增加硬边界与去重；
- 允许来源显式保留名称类似跟踪参数的业务查询参数。
- 为并发请求增加同域 2、全局 5 的实际并发边界，并细化 GitHub 403 限流识别。

### Not Included

- 信息源自动发现/添加向导、Excel/Word 导出、定时任务、一键启动、Windows 打包、浏览器采集、
  登录权限和真实 AI 调用。

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
