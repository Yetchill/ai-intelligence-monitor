# AI 行业动态与成果申报情报工具

这是一个面向公司内部使用的本地信息聚合工具。当前版本为 **0.1.0，且只完成了阶段一：项目骨架和数据库**。

## 当前已实现

- Python 3.12 + uv 项目和项目内虚拟环境；
- `.env` / 环境变量驱动的类型化配置；
- SQLite、SQLAlchemy 2.x 与 Alembic 基础设施；
- `Source`、`IntelligenceItem`、`CrawlRun`、`ItemRevision` 数据模型；
- 隐藏 SQLAlchemy Session 的 Repository + Unit of Work 层；
- application、crawler、error 三类滚动日志；
- 阶段一数据库和 Repository 单元测试；
- Ruff 与 Pyright 静态检查配置。

## 尚未实现

采集器、信息源自动发现、URL 规范化、分类与 AI、更新流水线、FastAPI 和网页 UI、Excel/Word 导出、一键启动均不在阶段一范围内，目前不可用。

## 开发环境

需要 Python 3.12 和 [uv](https://docs.astral.sh/uv/)。首次准备环境：

```bash
uv sync --dev
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
```

项目架构和关键约束见 [`docs/architecture.md`](docs/architecture.md)。完整产品规格见 [`SPEC.md`](SPEC.md)。
