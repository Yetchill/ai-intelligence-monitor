# 阶段一架构

## 范围

当前架构只覆盖 SPEC.md 的阶段一：配置、核心数据模型、数据库迁移、Repository 和日志。后续阶段的采集器、分类器、服务、Web 和导出模块尚未创建，避免空壳和提前耦合。

## 依赖方向

```text
未来 Application Service
          ↓
RepositoryUnitOfWork / 专用 Repository
          ↓
SQLAlchemy 2.x 映射与 SQLite
          ↓
Alembic 版本化迁移
```

调用方通过 `RepositoryUnitOfWork` 获取 `sources`、`items`、`crawl_runs` 和 `revisions` 仓储。SQLAlchemy `Session` 只存在于存储层内部；上下文正常退出时提交，发生异常时回滚。

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

保存标题、原始/规范 URL、简介、时间、分类、指纹和扩展 JSON。`canonical_url` 全局唯一，同时 `(source_id, fingerprint)` 具有复合唯一约束，为后续增量去重提供数据库最后防线。URL 规范化和业务去重算法属于阶段二/三，本阶段不实现。

### CrawlRun

保存一次更新任务的状态、开始/结束时间、来源统计和条目统计。阶段一只提供模型和 Repository，不运行采集任务。

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
- `crawler.log`：预留给后续 `app.crawler` 命名空间；
- `error.log`：错误级别日志。

文件按大小滚动，默认单文件最多 10 MB、保留 5 份。过滤器会遮盖常见 `api_key`、`token`、`password`、`secret` 赋值，但调用方仍不得主动记录凭据或完整敏感配置。

## 后续扩展边界

阶段二开始后，Fetcher/Collector 应返回统一领域数据，并通过 Application Service 调用 Repository；不得直接持有 Session。分类器不得操作数据库，Web/API 层不得包含采集逻辑。新增字段或约束必须随 Alembic migration 一起提交。
