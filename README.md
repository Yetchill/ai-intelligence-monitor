# AI 行业动态与成果申报情报工具

> 阶段八 B 已引入完整来源目录、来源生命周期、taxonomy v2、可信/审核状态、候选 preview/激活门槛以及报告-案例父子模型。完整说明见 [来源目录](docs/source-catalog.md)、[分类体系](docs/taxonomy-v2.md)、[生命周期](docs/source-lifecycle.md) 和 [审核发布](docs/source-review.md)。

常用的阶段八 B 运维命令：

```bash
uv run alembic upgrade head
uv run python -m app.cli sources sync-catalog
uv run python -m app.cli sources preview <slug> --max-items 20 --no-persist
uv run python -m app.cli sources activate <slug> --confirm
uv run python -m app.cli sources purge-retired --dry-run
uv run python -m app.cli sources purge-retired --confirm --backup /safe/path/before-purge.db
```

目录同步将 28 条 active/candidate 来源全部写入数据库；candidate 不参加批量更新。清理 confirm 必须在数据库副本上运行并先创建显式备份。

这是一个面向公司内部使用的本地信息聚合工具。当前已完成基础数据库、采集器、规则分类，
以及 **阶段八 A：正式信息源体系与内容准入过滤**。

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
- UI、CLI 和未来任务可共同调用的 `UpdatePipeline` 应用服务；
- enabled/指定来源选择、disabled 来源保护及 incremental/history 两种更新模式；
- 采集后标准化、同来源 fingerprint 去重、全局 canonical URL 去重和幂等更新；
- 规则分类结果持久化、人工分类保护及独立 `reclassify_item` / `reclassify_all` 接口；
- 内容有效变化的精确 `ItemRevision`，以及可选的 `CrawlRun` 关联；
- `running`、`success`、`partial_success`、`failed` 完整运行生命周期和来源故障隔离；
- 跨来源相同 URL 保留首条记录并在 `extra._source_discoveries` 记录额外发现来源；
- 最小开发 CLI 和使用临时数据库的真实网络流水线烟雾测试；
- Ruff 与 Pyright 静态检查配置。
- FastAPI + Jinja2 本地资讯页、来源页和更新记录页；
- 数据库层服务端分页、稳定排序、关键词搜索及分类/来源/收藏/时间筛选；
- POST 收藏、人工分类覆盖/清除及来源启停；
- 网页复用 `UpdatePipeline` 的全量/单来源同步更新与进程内互斥锁；
- 显式、幂等且不覆盖用户修改的 7 个正式来源导入命令；新数据库不再创建 Qwen-Agent Releases。
- 来源添加向导，支持 RSS/Atom、GitHub Releases 和简单 HTML 列表自动识别；
- 实际连接固定到已验证公网 IP、逐跳复查、禁用环境代理并限制超时和解压后响应大小的 SSRF 安全 Fetcher；
- 复用现有 CollectorRegistry、Collector 和 Classifier 的最多 10 条无落库预览；
- 有 TTL 和容量上限的进程内检测 token，保存时不信任浏览器提交的采集器配置；
- 来源详情编辑、disabled 待处理来源和确认后才替换配置的重新检测流程；
- “保存”与“保存并立即更新”，后者复用现有 UpdatePipeline 和进程内锁。
- 可扩展的 `Exporter` Protocol、`ExcelExporter`、`WordExporter` 与共享 `ExportService`；
- 首页与导出复用同一数据库筛选、最终分类语义和稳定排序，导出不受网页页码限制；
- 带表头冻结、自动筛选、中文分类和可点击原文链接的 Excel 工作簿；
- 按最终分类有序分组、跳过空章节和空简介的 Word 报告；
- Excel 公式注入、非法 XML 字符、危险超链接、文件名和响应头安全处理；
- Web 内存下载及支持筛选、数量限制、原子写入和显式覆盖的最小导出 CLI。
- 强类型单例运行设置、IANA 时区、明确星期选择和 Alembic 迁移；
- FastAPI 生命周期管理的单进程调度器，以及保存后立即重载；
- 网页手动、CLI 手动和定时运行来源标记，以及三者共享的更新锁；
- 设置页面和 `schedule show/enable/disable/run` CLI。
- formal/test/fallback 来源边界、来源权威等级、目标受众及首页/正式导出可见性；
- 独立于 Collector 和分类器的 `ContentAdmissionPolicy`，提供结构化匹配规则、0..100 质量分和失败关闭；
- 首页默认仅展示领导可见正式来源，正式 Excel/Word 默认排除测试、备用、停用和拒绝内容；
- CrawlRun accepted/rejected/classified/duplicate/failed 统计及主要拒绝原因计数。

正式来源清单和限制见 [docs/content-sources.md](docs/content-sources.md)，准入规则与审计语义见
[docs/content-admission.md](docs/content-admission.md)。

## 尚未实现

一键启动、Windows 计划任务、系统托盘、Windows 打包、浏览器采集、PDF、自动邮件和真实 AI
功能尚未实现。
当前来源页面不允许删除来源、直接修改入口 URL 或任意编辑 `collector_config`。

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

## 更新流水线调试

数据库完成迁移并已有来源后，可使用最小 CLI：

```bash
uv run python -m app.cli update
uv run python -m app.cli update --source-id 1
uv run python -m app.cli update --source-id 1 --allow-disabled
uv run python -m app.cli update --mode history --max-pages 5 --max-items 200
uv run python -m app.cli runs --limit 5
```

CLI 不包含终端 UI；它与未来网页和任务调度入口共享同一个 `UpdatePipeline`。详细执行流程、
事务与去重策略见 [`docs/update-pipeline.md`](docs/update-pipeline.md)。

这些 CLI 命令默认直接读取并写入 `AIM_DATABASE_URL` 指向的数据库；未配置时就是正式本地库
`data/intelligence.db`。开发、测试或迁移验证应显式把 `AIM_DATABASE_URL` 指向临时数据库。

## 本地网页

首次使用先升级数据库；需要正式来源时再显式导入。导入只写来源配置，不会自动访问网络，
重复执行不会覆盖相同 URL 的已有来源：

```bash
uv run alembic upgrade head
uv run python -m app.cli sources seed-formal
uv run python -m app.web
```

这也是已有数据库从阶段七升级后的完整路径。Alembic 只迁移结构和旧来源安全默认值，不创建业务
来源；`seed-formal` 才初始化 7 个正式来源。命令可重复执行，不覆盖已有修改，不重新启用已停用
来源。阶段七原始 AIIA 预设仅在全部受管字段仍与旧版本完全一致时安全提升为正式来源；有修改时
报告 conflict 并保留原值。来源页也提供同一幂等初始化操作和当前正式来源数量提示。

启动网页：

```bash
uv run uvicorn app.web.app:app --host 127.0.0.1 --port 8000
```

也可以使用 Python 模块入口：

```bash
uv run python -m app.web
```

然后访问 `http://127.0.0.1:8000/`。页面可以搜索和筛选资讯、收藏、人工修改分类、添加和编辑
来源、抓取预览、更新全部 enabled 正式来源或显式选择单个 test/fallback 来源，并查看运行记录。启动只检查 Alembic 迁移状态，不会
自动迁移、重建数据库、导入来源或执行公网采集。完整说明见
[`docs/web-ui.md`](docs/web-ui.md)。
来源识别范围、SSRF 边界、token 和重新检测流程见
[`docs/source-onboarding.md`](docs/source-onboarding.md)。

## 定时更新

网页“设置”页面可开启计划、选择时间/星期和 IANA 时区。应用必须保持运行，内置计划才会执行；
关机或应用退出期间错过的任务会跳过，重启不会补跑。手动与定时更新共用进程内锁，互不并发。
独立 CLI 进程与 Web 进程之间不提供跨进程互斥；不要并行运行两个调度器。

```bash
uv run python -m app.cli schedule show
uv run python -m app.cli schedule enable --time 09:00 --days mon,tue,wed,thu,fri --timezone Asia/Shanghai
uv run python -m app.cli schedule disable
uv run python -m app.cli schedule run
```

前台 `schedule run` 用于开发验证，`Ctrl+C` 正常停止。当前不是系统服务，也不安装 Windows 计划
任务或桌面启动器。完整语义见 [`docs/scheduling.md`](docs/scheduling.md)。

资讯页会显示当前筛选匹配条数，可直接导出全部匹配结果为 Excel 或 Word，不受当前分页限制。
也可以使用 CLI：

```bash
uv run python -m app.cli export excel --output output/report.xlsx
uv run python -m app.cli export word --output output/report.docx
```

筛选参数、文件结构、10,000/2,000 条上限、`output/` 和安全边界见
[`docs/export.md`](docs/export.md)。

服务默认且应当只监听 `127.0.0.1`，不应直接暴露到公网。当前没有登录和 CSRF 防护；如果未来
部署到局域网或服务器，必须先增加认证、授权、CSRF 防护和合适的反向代理安全配置。

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
uv run pytest -m network -s -q
```

真实网络测试使用 pytest 临时数据库，不写入 `data/intelligence.db`。GitHub Releases 优先使用
公开 API；未认证 API 配额耗尽时降级到公开 Releases Atom Feed。

项目架构和关键约束见 [`docs/architecture.md`](docs/architecture.md)，新增或配置采集器见
[`docs/source-development.md`](docs/source-development.md)，分类规则和扩展方式见
[`docs/classification.md`](docs/classification.md)。完整产品规格见 [`SPEC.md`](SPEC.md)。
