# 阶段二架构

## 范围

当前架构覆盖 SPEC.md 的阶段一基础设施和阶段二基础采集器。分类器、更新流水线、信息源发现、Web、导出、定时任务、浏览器获取和 AI 模块尚未创建。

## 依赖方向

```text
未来 Application Service
          ↓
CollectorRegistry → Collector → CollectedItem
          ↓             ↓
      Source 配置    Fetcher Protocol
                        ↓
                   HttpFetcher
          ↓
RepositoryUnitOfWork / 专用 Repository
          ↓
SQLAlchemy 2.x 映射与 SQLite
          ↓
Alembic 版本化迁移
```

Collector 通过 `CollectContext` 接收来源入口和配置，只返回 `CollectedItem`，不持有 Repository 或 SQLAlchemy Session。未来 Application Service 负责连接纯采集结果与持久化。调用方通过 `RepositoryUnitOfWork` 获取 `sources`、`items`、`crawl_runs` 和 `revisions` 仓储；上下文正常退出时提交，发生异常时回滚。

## 采集接口

`app/domain/collection.py` 定义稳定边界：

- `CollectedItem`：标题、原始/规范 URL、发布时间、简介和扩展字段；
- `CollectContext`：来源 URL、名称和不透明配置；
- `Fetcher` / `FetchResult`：隐藏具体 HTTP 客户端；
- `Collector`：异步返回一组 `CollectedItem`。

`CollectorRegistry` 将名称映射到工厂。运行时按 `Source.collector_name`（空值时按 `source_type`）构造采集器；新增实现只需注册工厂，采集主流程不需要增加 if-else 分支。

## HTTP 获取

`HttpFetcher` 使用 httpx `AsyncClient`，默认 15 秒超时、同域 1.5 秒请求间隔和最多 2 次重试。重试由 tenacity 指数退避实现，只覆盖超时、网络错误、429/rate limit 和 5xx。403、404 及其他不可恢复 HTTP 状态使用独立异常，不伪装成功。

Fetcher 只访问 HTTP(S) 公开资源，不执行脚本、不处理登录或验证码，也不尝试绕过访问控制。阶段二不包含 Playwright 或 BrowserFetcher。

## Collector 实现

- `RSSCollector`：解析 RSS/Atom 的标题、链接、日期和 Feed 摘要；单条损坏不影响其余条目；
- `HTMLListCollector`：selector 或 link-filter 模式，只分析列表页；允许显式分页选择器，但最大 100 页、深度 3，默认最多 20 页/深度 1；
- `GitHubReleaseCollector`：优先访问公开 GitHub Releases API，过滤 draft 和默认过滤 prerelease，不读取 assets；API rate limit 耗尽时使用公开 Atom Feed。

所有 Collector 均不进入详情页。HTML selector 模式可以按可配置字段，把服务端可见标题与页面脚本中内嵌的公开链接元数据关联；该能力只读取已下载 HTML，不执行 JavaScript。

## URL 边界

`app/utils/url.py` 负责相对地址解析、HTTP(S) 协议检查、fragment 和常见跟踪参数删除、默认端口与尾部斜杠统一、查询参数排序。`keep_query_params` 可将查询串收窄到来源必需参数。HTML Collector 在规范化后再次检查允许域名和静态资源/排除规则。

## 配置

`app/config/settings.py` 使用 Pydantic Settings。配置优先级为环境变量、项目根目录 `.env`、代码默认值，环境变量统一使用 `AIM_` 前缀。

关键配置包括：

- `AIM_DATABASE_URL`：默认 `data/intelligence.db`；
- `AIM_LOG_DIR`：默认 `logs/`；
- `AIM_LOG_LEVEL`：默认 `INFO`；
- `AIM_LOG_MAX_BYTES`：默认 10 MB；
- `AIM_LOG_BACKUP_COUNT`：默认 5。

`.env`、数据库、日志和导出目录均由 `.gitignore` 排除。

## 数据模型

### Source

保存运行时信息源入口和采集配置。`start_url` 全局唯一；结构可变的站点规则放入 JSON `collector_config`，无需按网站修改数据库表。删除已有历史条目的来源会被外键 `RESTRICT` 阻止，防止意外级联删除历史数据。

### IntelligenceItem

保存标题、原始/规范 URL、简介、时间、分类、指纹和扩展 JSON。`canonical_url` 全局唯一，同时 `(source_id, fingerprint)` 具有复合唯一约束，为后续增量去重提供数据库最后防线。URL 规范化已在阶段二实现；数据库增量写入、fingerprint 生成和业务去重编排属于阶段三，本阶段不实现。

### CrawlRun

保存一次更新任务的状态、开始/结束时间、来源统计和条目统计。当前只提供模型和 Repository，不运行更新任务。

### ItemRevision

用 JSON `old_data` / `new_data` 保存条目变化快照。修订必须关联 `IntelligenceItem`；`crawl_run_id` 可空，用于关联产生修订的更新任务，也允许未来记录非采集任务产生的修订。条目删除时修订级联删除；任务记录删除时修订保留并将任务外键置空。

## 数据库生命周期

生产/本地数据库以 Alembic 为结构真源：

```bash
uv run alembic upgrade head
```

`Database.create_schema()` 只为隔离单元测试提供快速建表能力。任何正式模型变更都必须新增迁移，不能删除数据库重建。

SQLite 连接会启用 `PRAGMA foreign_keys=ON`。Repository 默认 `expire_on_commit=False`，便于事务结束后读取已提交实体的标量字段。

## 日志

`configure_logging()` 创建：

- `application.log`：一般应用日志；
- `crawler.log`：供 `app.crawler` 命名空间使用；
- `error.log`：错误级别日志。

文件按大小滚动，默认单文件最多 10 MB、保留 5 份。过滤器会遮盖常见 `api_key`、`token`、`password`、`secret` 赋值，但调用方仍不得主动记录凭据或完整敏感配置。

## 后续扩展边界

后续 Application Service 应消费统一 `CollectedItem` 并调用 Repository；Fetcher/Collector 不得直接持有 Session。分类器不得操作数据库，Web/API 层不得包含采集逻辑。SourceDiscoverer 与正式 Collector 必须保持分离。新增字段或约束必须随 Alembic migration 一起提交。
