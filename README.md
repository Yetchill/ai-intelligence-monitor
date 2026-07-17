# AI 行业动态与成果申报情报工具

这是一个面向公司内部使用的本地信息聚合工具。当前已完成 **阶段二：基础采集器**，并完成
**阶段三的分类系统子范围**。阶段三更新流水线尚未实现。

## 当前已实现

- Python 3.12 + uv 项目和项目内虚拟环境；
- `.env` / 环境变量驱动的类型化配置；
- SQLite、SQLAlchemy 2.x 与 Alembic 基础设施；
- `Source`、`IntelligenceItem`、`CrawlRun`、`ItemRevision` 数据模型；
- 隐藏 SQLAlchemy Session 的 Repository + Unit of Work 层；
- application、crawler、error 三类滚动日志；
- `CollectedItem`、`CollectContext`、`Collector`、`FetchResult`、`Fetcher` 统一接口；
- 基于 httpx 的异步 HTTP 获取、全局/同域并发边界、同域请求间隔和 tenacity 指数退避重试；
- 403、404、429/GitHub rate limit、5xx、超时和网络错误分类；
- HTTP(S) URL 解析、跟踪参数清理、查询参数保留配置和 canonicalization；
- RSS/Atom、HTML 列表和 GitHub Releases 三类 Collector，并对返回结果数量设置可配置硬边界；
- HTML selector/link-filter 模式、域名与包含/排除规则、有限列表分页及分页 URL 去重；
- 可扩展的 Collector 注册/工厂机制；
- 固定 HTML/RSS/Atom/JSON 样本、离线单元测试和可选真实网络测试；
- `ClassificationResult`、异步 `Classifier` Protocol 与纯逻辑分类边界；
- 从严格校验 YAML 加载的规则分类器，支持词组、关键词、排除词、字段权重、阈值和歧义分差；
- 来源默认分类回退、人工分类最高优先级和可读分类原因；
- 保守的中英文文本规范化，以及 71 条固定人工标注分类样本；
- 不接 SDK、API Key 或外部服务的 `LLMClassifier` / `HybridClassifier` 扩展空实现；
- Ruff 与 Pyright 静态检查配置。

## 尚未实现

更新流水线、分类结果持久化、信息源自动发现/添加向导、FastAPI 和网页 UI、Excel/Word
导出、定时任务、一键启动、浏览器采集和真实 AI 功能尚未实现。阶段二 Collector 仍只返回纯
采集结果，不写入正式数据库；分类器也不访问数据库或修改 `CollectedItem`。

## 开发环境

需要 Python 3.12 和 [uv](https://docs.astral.sh/uv/)。首次准备环境：

```bash
uv sync --locked --dev
```

uv 会在项目目录使用 `.venv`。应用默认读取项目根目录的 `.env`，可从示例开始：

```bash
cp .env.example .env
```

`.env` 不会提交到 Git。默认数据库为 `data/intelligence.db`，日志目录为 `logs/`。

## 数据库迁移

初始化或升级数据库：

```bash
uv run alembic upgrade head
uv run alembic current
```

数据库结构变更必须通过新的 Alembic revision 完成，不得通过删除 SQLite 数据库解决。

## 质量检查

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run alembic check
```

默认 `pytest` 跳过真实网络测试。手动验证公开来源：

```bash
uv run pytest -m network -s
```

网络测试只在内存中保留采集结果，不写入 `data/intelligence.db`。GitHub Releases 优先使用公开 API；未认证 API 配额耗尽时降级到公开 Releases Atom Feed。

项目架构和关键约束见 [`docs/architecture.md`](docs/architecture.md)，新增或配置采集器见
[`docs/source-development.md`](docs/source-development.md)，分类规则和扩展方式见
[`docs/classification.md`](docs/classification.md)。完整产品规格见 [`SPEC.md`](SPEC.md)。
