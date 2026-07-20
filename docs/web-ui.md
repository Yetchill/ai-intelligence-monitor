# 阶段七本地网页 UI

## 阶段八 B 页面

来源管理页显示 catalog 的全部 active/candidate/paused，而不是只显示可运行项；candidate 显示技术阻碍、preview 信息和入口。active media 明示“采集行业线索、默认不进首页和正式导出”。

首页使用 PublicationPolicy 的正式资格。导航新增最小“行业线索”视图，可筛选 industry_signal、media_only、rumor 和 pending。人工 taxonomy/review 修改记录审计事件。整体视觉结构保持原有页面，不做全站重构。

## 当前范围

阶段七提供本地服务端渲染页面、Office 导出和运行设置：

- `/`：资讯卡片、搜索筛选、收藏、人工分类和当前结果导出；
- `POST /exports/excel`、`POST /exports/word`：返回当前筛选的 Excel 或 Word 文件；
- `/sources`：来源查看、添加入口、启停和单来源更新；
- `/sources/new` 与 `/sources/discover/{token}`：安全检测、类型说明和最多 10 条抓取预览；
- `/sources/{id}`：允许字段编辑、状态说明和重新检测入口；
- `/runs`：更新运行记录和净化后的错误摘要。
- `/settings`：定时开关、时间、星期、IANA 时区、下一次运行和最近触发。

当前不包含来源删除或任意 `collector_config` 编辑、PDF、自动邮件、Windows 计划任务/打包、
浏览器自动化、真实 AI、登录权限、后台队列或 WebSocket。

## 准备与启动

安装锁定依赖并升级数据库：

```bash
uv sync --locked --dev
uv run alembic upgrade head
```

需要初始化正式来源时显式执行：

```bash
uv run python -m app.cli sources seed-formal
```

该命令导入 `content-sources.md` 记录的 7 个正式来源。它是幂等操作，不覆盖同 URL 的已有修改，
不重新启用已停用来源，不创建 Qwen-Agent Releases，不自动更新，也不会在 Web 启动时执行。
来源页会显示当前正式来源数量，并提供等价的“初始化正式来源”按钮。数据库迁移本身不创建业务
来源，因此已有数据库升级后必须执行 CLI 命令或使用该按钮。

启动服务：

```bash
uv run uvicorn app.web.app:app --host 127.0.0.1 --port 8000
```

或：

```bash
uv run python -m app.web
```

访问 `http://127.0.0.1:8000/`。启动会加载项目配置和日志、检查 Alembic 版本并读取运行设置。
数据库未升级时会停止并提示运行 `uv run alembic upgrade head`；应用不会自动删除、重建或迁移
数据库。计划关闭时不访问公网；计划开启时只等待下一次未来时间，不补跑停机期间任务。

## 使用

资讯页默认每页 20 条，可选 20、50 或 100。排序优先使用发布时间；缺少发布时间时使用发现
时间，并用 id 保证稳定顺序。筛选支持标题/简介关键词、最终分类、来源、收藏、发布时间范围、
发现时间范围和是否待分类；多个条件按 AND 组合，分页链接保留筛选。

来源范围默认“领导首页（正式）”，只显示 enabled、formal、homepage visible 且 audience 为
leadership/all 的来源。“全部来源”“非正式来源”“备用技术来源”“已停用来源历史”必须显式选择；
未知来源范围安全回退到默认，不扩大可见范围。

筛选面板下方显示导出范围和匹配条数。“导出 Excel”和“导出 Word”通过 POST 继承当前筛选，
导出全部匹配记录而不使用当前页码。Excel 最多 10,000 条，Word 最多 2,000 条；超过上限、筛选
为空或参数非法时显示普通错误页，不返回空文件或部分文件。详细文件结构见
[`export.md`](export.md)。

默认 Excel/Word 导出要求来源 enabled、formal 且 export visible，并只包含已经通过准入而入库的
记录。显式选择全部/非正式/备用/停用范围时可以导出历史内容，文件附带来源性质字段。

标题和“查看原文”在新标签页打开，使用 `noopener noreferrer`。页面不代理原站图片，不执行或
安全渲染来源 HTML；没有简介时省略摘要，没有发布时间时显示“发布时间未知”。人工分类优先于
自动分类并标注“人工”；清除后立即恢复自动分类显示。

收藏、分类、来源启停和更新都使用 POST。全量更新只选择 enabled formal 来源；test/fallback
仅能通过显式单来源操作或 CLI `update --all-enabled` 参与。单来源更新复用同一个
`UpdatePipeline`。更新期间前端禁用按钮，后端进程内锁拒绝并发任务。完成页显示来源成功/失败、
fetched、normalized、accepted、rejected、classified、inserted、updated、duplicate、failed 和
待分类数量，并按来源显示 fetch/解析、配置、规范化、分类、写入失败以及独立的准入拒绝主因。
已保存来源的“运行时预览”最多处理 10 条，使用实际配置但不分类、不写资讯和 CrawlRun。

来源添加先 POST 检测，再跳转到只读结果页。预览为空或需要自定义采集器时，页面明确提示不能
直接启用。保存表单不包含 collector JSON；来源详情也只编辑名称、enabled、默认分类和说明。
重新检测先显示独立预览，确认前不改旧配置。完整说明见
[`source-onboarding.md`](source-onboarding.md)。

设置页面只接受 `HH:MM`、明确星期复选框和 IANA 时区，不接受 cron。保存成功立即唤醒调度器并
重算；保存失败不改变原设置。设置 GET 只读，尚未保存时显示内存默认值。数据库提交后若调度器
重载失败，页面明确提示设置已保存并可通过再次保存或重启恢复。应用必须保持运行，内置计划才会
执行。手动更新与定时更新共享锁，网页冲突返回 409，计划冲突安全跳过。完整语义见
[`scheduling.md`](scheduling.md)。更新记录页会显示网页手动、CLI 手动、历史手动或定时来源。

## 本地安全边界

服务默认只监听 `127.0.0.1`，不得改为默认监听 `0.0.0.0`，也不应直接暴露到公网。静态资源全部
随项目提供，不访问 CDN。Jinja2 自动转义保持开启，来源内容未使用 `safe`；外链只接受 HTTP(S)。
查询参数不能指定数据库路径、项目文件或任意抓取 URL。

Web 导出同样不能指定服务器路径、文件名或格式外的任意值。文件在内存中生成，响应同时提供
安全 ASCII 文件名和 RFC 5987 UTF-8 中文文件名，并设置正确 Office Content-Type 和
`nosniff`。错误页不显示临时路径、数据库位置或堆栈。

当前是单机本地工具，没有登录和完整 CSRF 系统。如果未来部署到局域网或服务器，必须先增加
认证、授权、CSRF 防护、HTTPS 和适合部署形态的更新任务互斥机制。
