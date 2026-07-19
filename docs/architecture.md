# 阶段六 Excel 与 Word 导出架构

## 范围

当前架构覆盖基础设施、基础采集器、纯逻辑分类子系统，以及更新流水线、分类持久化与运行
记录、本地 Web UI 与基础人工操作、信息源发现与管理，以及 Excel/Word 导出。定时任务、PDF、
自动邮件、一键启动、Windows 打包、浏览器获取和真实 AI 模块尚未创建。

## 依赖方向

```text
Jinja2 Web / 最小 CLI / 未来任务入口
          ↓
  WebDataService / ExportService / UpdatePipeline
          ↓             ↓                 ↓
   CrawlService   ClassificationService   CrawlRunService
          ↓             ↓                 ↓
CollectorRegistry  RuleBasedClassifier  CrawlRun Repository
          ↓
Collector → Fetcher → 外部站点
          ↓
标准化 → ItemPersistenceService
          ↓
RepositoryUnitOfWork / Repository
          ↓
SQLAlchemy 2.x 映射与 SQLite
          ↓
Alembic 版本化迁移
```

`ExportService` 与 `WebDataService` 共享 `ItemFilter`，Repository 的 `_item_filters` 和
`_item_order` 是列表与导出的唯一 SQL 条件和排序实现。分页列表增加 `LIMIT/OFFSET`；导出按
格式上限加一执行单次有界联表查询，用额外一条判断是否超限。过滤不在 Python 中重做，也不会
加载正式数据库全部资讯；单次查询也避免了 count 与 data 分两次读取产生快照差异。

导出器通过 `Exporter` Protocol 接收脱离 Session 的 `ExportItem` 和 `ExportMetadata`，不创建
Session、不查询数据库、不处理 Web 响应或 CLI 路径。`ExcelExporter` 与 `WordExporter` 只负责
Office 文档结构；未来增加格式只需注册新的导出器，核心查询流程不需要修改。

Web 通过 `BytesIO` 结果直接响应，路由不拼装 Office 文件且不能接受输出路径。CLI 通过同一
`build_export_service()` 构造服务，在生成成功后执行安全的原子文件写入。完整结构和安全边界见
[`export.md`](export.md)。

Collector 通过 `CollectContext` 接收来源入口和配置，只返回 `CollectedItem`，不持有 Repository
或 SQLAlchemy Session。`UpdatePipeline` 连接采集、标准化、分类和持久化。调用方只持有应用服务，
不接触 Session。

分类器本身仍与 Repository 无依赖。`ClassificationService` 负责运行时组合和独立重分类入口；
`ItemPersistenceService` 保存自动分类字段并保留 `manual_category`。最终展示仍按人工分类优先。

完整流水线、事务和故障语义见 [`update-pipeline.md`](update-pipeline.md)。

## 分类接口与实现

`app/domain/classification.py` 定义 `ClassificationResult` 和异步 `Classifier` Protocol。
`app/classifiers/` 包含：

- `RuleBasedClassifier`：从 YAML 载入规则并进行可解释评分；
- `ManualClassifier` / `FinalCategoryResolver`：解析人工分类并执行最高优先级覆盖；
- `LLMClassifier` / `HybridClassifier`：无 SDK、无外部调用的未来扩展空实现。

规则文件加载时严格验证分类集合、字段和分值。文本规范化及打分全部是确定性纯逻辑，分类器
不修改原始 `CollectedItem`。完整算法、规则格式和误判修正方式见
[`classification.md`](classification.md)。

## 采集接口

`app/domain/collection.py` 定义稳定边界：

- `CollectedItem`：标题、原始/规范 URL、发布时间、简介和扩展字段；
- `CollectContext`：来源 URL、名称和不透明配置；
- `Fetcher` / `FetchResult`：隐藏具体 HTTP 客户端；
- `Collector`：异步返回一组 `CollectedItem`。

`CollectorRegistry` 将名称映射到工厂。运行时按 `Source.collector_name`（空值时按 `source_type`）构造采集器；新增实现只需注册工厂，采集主流程不需要增加 if-else 分支。

## HTTP 获取

`HttpFetcher` 使用 httpx `AsyncClient`，默认 15 秒超时、同域并发 2、全局并发 5、同域 1.5 秒请求间隔和最多 2 次重试。同域间隔锁与并发信号量在并发调用下共同生效。重试由 tenacity 指数退避实现，只覆盖超时、网络错误、429/rate limit 和 5xx。普通 403、404 及其他不可恢复 HTTP 状态使用独立异常，不伪装成功；GitHub 403 只有带明确限流信号时才按 rate limit 处理。

Fetcher 只访问 HTTP(S) 公开资源，不执行脚本、不处理登录或验证码，也不尝试绕过访问控制。阶段二不包含 Playwright 或 BrowserFetcher。

## Collector 实现

- `RSSCollector`：解析 RSS/Atom 的标题、链接、日期和 Feed 摘要；单条损坏不影响其余条目；默认最多返回 1000 条，硬上限 10000 条；
- `HTMLListCollector`：selector 或 link-filter 模式，只分析列表页；允许显式分页选择器，但最大 100 页、深度 3，默认最多 20 页/深度 1；分页 URL 在入队前去重，默认最多返回 1000 条、硬上限 10000 条；
- `GitHubReleaseCollector`：优先访问公开 GitHub Releases API，过滤 draft 和默认过滤 prerelease，不读取 assets；API rate limit 耗尽时使用公开 Atom Feed。

所有 Collector 均不进入详情页。HTML selector 模式可以按可配置字段，把服务端可见标题与页面脚本中内嵌的公开链接元数据关联；该能力只读取已下载 HTML，不执行 JavaScript。

## URL 边界

`app/utils/url.py` 负责相对地址解析、HTTP(S) 协议检查、fragment 和常见跟踪参数删除、默认端口与尾部斜杠统一、查询参数排序。`keep_query_params` 可将查询串收窄到来源必需参数；显式列入的参数即使名称类似跟踪参数也会保留。HTML Collector 在规范化后再次检查允许域名和静态资源/排除规则。

## 配置

`app/config/settings.py` 使用 Pydantic Settings。配置优先级为环境变量、项目根目录 `.env`、代码默认值，环境变量统一使用 `AIM_` 前缀。

关键配置包括：

- `AIM_DATABASE_URL`：默认 `data/intelligence.db`；
- `AIM_LOG_DIR`：默认 `logs/`；
- `AIM_LOG_LEVEL`：默认 `INFO`；
- `AIM_LOG_MAX_BYTES`：默认 10 MB；
- `AIM_LOG_BACKUP_COUNT`：默认 5。

`.env`、数据库、日志和导出文件均由 `.gitignore` 排除；`output/.gitkeep` 保留目录结构。

## 数据模型

### Source

保存运行时信息源入口和采集配置。`start_url` 全局唯一；结构可变的站点规则放入 JSON `collector_config`，无需按网站修改数据库表。删除已有历史条目的来源会被外键 `RESTRICT` 阻止，防止意外级联删除历史数据。

### IntelligenceItem

保存标题、原始/规范 URL、简介、时间、分类、指纹和扩展 JSON。`canonical_url` 全局唯一，同时
`(source_id, fingerprint)` 具有复合唯一约束。流水线先查 canonical URL，再查同来源 fingerprint；
插入仍使用保存点捕获唯一约束竞争。

跨来源相同 canonical URL 不创建第二条记录，保留最早记录的 `source_id`、内容、收藏和分类，
只更新 `last_seen_at` 并在 `extra._source_discoveries` 记录额外来源。该字段是阶段四的最小发现
元数据。未来若需要按来源分别记录状态、排序或审计，应新增 `ItemSource` 关联表并用 Alembic
迁移，而不是继续扩展 JSON 或改变全局唯一约束的语义。

### CrawlRun

保存一次更新任务的状态、开始/结束时间、来源统计和条目统计。状态为 `running`、`success`、
`partial_success` 或 `failed`；流水线开始即提交 running 记录，正常或异常路径都会尽力完成它。

### ItemRevision

用 JSON `old_data` / `new_data` 只保存变化的 `title`、`summary`、`published_at` 或业务 `extra`。
`last_seen_at` 和自动分类变化不属于内容修订。修订必须关联条目，流水线修订同时关联本次
`CrawlRun`；自动分类审计未来如有需要应使用独立机制，不与内容 Revision 混合。

## 数据库生命周期

生产/本地数据库以 Alembic 为结构真源：

```bash
uv run alembic upgrade head
```

`Database.create_schema()` 只为隔离单元测试提供快速建表能力。任何正式模型变更都必须新增迁移，不能删除数据库重建。

迁移 `8df43a9b1c2e` 对 `succeeded`/`partial` 做一一状态重命名，`running`/`failed` 原样保留；
升级前若发现约束之外的未知历史状态，会在任何表结构修改前明确失败并保留原数据。downgrade
执行反向一一映射，因此该状态迁移可无损往返。

应用运行时的 SQLite 连接会启用 `PRAGMA foreign_keys=ON`。Alembic 自有的迁移连接保持 SQLite
默认的外键关闭状态，避免 batch 重建父表时触发子表的 `ON DELETE` 动作并误删或改写历史数据；
迁移结束后的应用连接仍会重新启用并校验外键。Repository 默认 `expire_on_commit=False`，便于事务结束后读取已提交实体的标量字段。
SQLite 的 `DateTime(timezone=True)` 读回值可能不携带 `tzinfo`；应用服务在比较和返回运行时间时
统一把 naive 值解释为 UTC，避免与 aware datetime 混用。未来迁移到更严格数据库时仍使用同一
UTC 规范化边界。

## 日志

`configure_logging()` 创建：

- `application.log`：一般应用日志；
- `crawler.log`：供 `app.crawler` 命名空间使用；
- `error.log`：错误级别日志。

文件按大小滚动，默认单文件最多 10 MB、保留 5 份。过滤器会遮盖常见 `api_key`、`token`、`password`、`secret` 赋值，但调用方仍不得主动记录凭据或完整敏感配置。

## 事务边界

来源查询和 CrawlRun 创建分别使用短 UoW，随后关闭事务再执行网络采集。采集结束后，每个来源
由 `ItemPersistenceService` 使用独立短事务写入。单条插入使用嵌套保存点；唯一约束竞争只回滚
该保存点并重新查询已有记录。一个来源写入失败不会回滚已成功来源，失败状态再用独立短 UoW
写入。Repository 和服务均不公开 Session。

## Web 层

`app/web/app.py` 负责应用工厂、静态文件、Jinja2 自动转义、迁移状态检查和统一错误页面；
`app/web/routes/` 只解析已校验输入并调用应用服务。`WebDataService` 持有短 Unit of Work 边界，
路由从不接触 SQLAlchemy Session。

资讯列表的 count 与 data 使用相同 SQLAlchemy 条件。data 查询一次联表 `Source`，按
`coalesce(published_at, discovered_at, updated_at) DESC, id DESC` 稳定排序，再在数据库执行
`LIMIT/OFFSET`。标题/简介关键词使用绑定参数和显式 LIKE 通配符转义；人工分类筛选和展示均按
`manual_category` 优先。来源和 CrawlRun 也使用数据库分页。

所有状态修改均为 POST。收藏、人工分类和来源启停由 `WebDataService` 提供明确接口；人工分类
只写 `manual_category` 和 `updated_at`，不修改自动分类字段、`last_seen_at` 或 ItemRevision。
`WebUpdateService` 使用进程内非阻塞锁串行化更新，并通过共享工厂构造现有 `UpdatePipeline`；
锁在 `finally` 中释放。

Web 应用启动时只核对当前 Alembic revision 与 head。版本落后会给出升级命令，不自动迁移、
重建数据库、导入来源或启动采集。详细运行和安全边界见 [`web-ui.md`](web-ui.md)。

## 后续扩展边界

Web、CLI 和未来任务入口都调用现有 `UpdatePipeline`；Fetcher/Collector 不得直接持有
Session。分类器不得操作数据库，Web/API 层不得包含采集逻辑。
SourceDiscoverer 与正式 Collector 必须保持分离。新增字段或约束必须随 Alembic migration 一起提交。

Web 与 CLI 导出都调用同一个 `ExportService`。导出层只读现有表，不创建 CrawlRun、
ItemRevision 或任何导出记录；阶段六没有数据模型变化或 Alembic migration。

## 来源添加边界

`SourceDiscoveryService` 只识别并生成有限配置，`SourcePreviewService` 通过现有
`CollectorRegistry` 和 `Classifier` 执行最多 10 条预览。两者都不依赖 Repository。
`SourceManagementService` 只在最终保存、允许字段编辑或用户确认重新检测时打开短 UoW。

用户输入网络请求使用独立 `SafeHttpFetcher`：`SourceUrlGuard` 在初始 URL 和每次重定向前检查
协议、认证信息、安全端口、DNS 的全部 IP 和公网属性；自定义 httpcore 网络后端在实际建连时
再次校验并直接连接已验证 IP，消除校验后由客户端二次 DNS 解析的目标偏移。Fetcher 禁用系统
代理与底层自动重定向，并限制逐项超时、解压后响应大小和请求头。用户添加来源的正式更新在
组合层选择同一安全 Fetcher，现有 UpdatePipeline 不被修改或复制。

`DiscoveryTokenStore` 是单进程、15 分钟 TTL、256 条上限的临时状态。它只持有有长度边界的
结构化检测结果和预览，不持有完整响应。保存时会原子占用并在成功后消费 token；浏览器 token
不能决定 collector 名称或配置。多进程与应用重启不会共享状态。完整流程见
[`source-onboarding.md`](source-onboarding.md)。
