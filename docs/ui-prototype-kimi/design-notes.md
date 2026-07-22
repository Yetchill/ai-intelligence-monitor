# 资讯首页 UI 原型 · 设计说明

> 目录：`docs/ui-prototype-kimi/`。这是一个**独立静态原型**，不修改任何生产代码，
> 不调用真实后端、不抓取、不调用 AI。所有数据为内置模拟数据。
>
> 打开方式：`open docs/ui-prototype-kimi/index.html`（macOS），或用任意静态服务器托管该目录。

## 1. 两种列表方案对比

### 方案 A：紧凑资讯卡片（默认）

- 每条一张白色卡片，标题 16px 加粗为最突出内容，摘要默认 2 行（长摘要可展开）。
- 元信息（分类 / 发布时间 / 发现时间 / 来源）分区放置：分类在左上，时间在右上，来源在标题下方。
- 操作按钮全部收进底部**同一行**操作栏，用细分隔线分组：原文与收藏 / 已读 | AI 操作 | 修改分类与更多信息。
- 单条高度约 160–190px，1080p 屏幕一屏可见约 4–5 条。

**优点**：标题和摘要阅读体验最好，接近 Readwise Reader；长摘要、英文长标题都有充足空间；
操作全部可见，不需要学习成本。适合以"读"为主的使用场景。
**缺点**：信息密度低于方案 B；扫读大量条目时眼球移动距离更长。

### 方案 B：表格与资讯流混合

- 固定四列网格：复选框 ｜ 分类列 ｜ 主内容（标题 1 行省略 + 摘要 1 行省略 + 元信息行）｜ 固定宽度操作列。
- 单条高度约 64–76px，1080p 屏幕一屏可见约 10 条以上。
- 长标题用省略号截断，不会撑破布局；修改分类和详细信息收进"▾"展开面板。
- 900px 以下自动退化为上下结构：分类并入元信息行，操作列贴右，展开面板占满整行。

**优点**：扫读密度高，未读圆点 + 左侧色条让"哪些没看"一目了然；操作区位置固定，
肌肉记忆友好，适合每天快速过几十条资讯的业务用户。
**缺点**：摘要只露一行，判断内容价值更依赖标题；单行省略对政策类长标题不够友好（需 hover 或展开）。

### 推荐

**推荐方案 A 作为默认视图，方案 B 作为可切换的高密度视图**（原型右上角分段控件即此设计）。
理由：该工具的目标用户是公司管理人员与业务人员，首要任务是"读懂并判断重要性"，
其次才是"快速过量"。方案 A 的标题 + 2 行摘要能显著减少逐条点开原文的次数；
方案 B 留给每天需要快速清仓未读的重度用户。两者共享同一套数据结构，后端模板只需输出两套 class 结构。

## 2. 色彩、字号、圆角、间距

全部定义为 CSS 变量（`prototype.css` 顶部 `:root`），接入生产时可直接迁移：

| 用途 | 值 |
| --- | --- |
| 页面背景 | `#F5F7F8` 暖灰 |
| 内容背景 | `#FFFFFF` |
| 主文字 | `#17212B` |
| 次要文字 | `#66727F`（时间等再弱一级 `#8A949E`） |
| 边框 | `#DDE3E7`（输入框用略深的 `#C8D0D6`） |
| 主色 | `#0F6B5C` 低饱和深青绿，hover `#0B5649`，浅底 `#EEF4F2` |
| 成功 / 警告 / 危险 | `#2E7D4F` / `#8A6D1F` / `#B4433A`，仅用于状态与危险操作 |
| 圆角 | 面板卡片 10px，按钮输入框 8px，小按钮 7px |
| 字号 | 正文 14px，辅助 13px，说明 12px，卡片标题 16px，页面标题 22px |
| 间距 | 4px 基准，常用 4/8/12/16/20/24px |
| 页面最大宽度 | 1560px；顶部导航高 60px |

刻意不做的事：无渐变、无阴影堆叠（仅输入框 focus 一圈浅色光晕）、无巨大数字卡片、
无彩色标签云。统计区是一行横向数字单元而不是四张卡片。

## 3. 按钮层级

四级，视觉重量严格递减：

1. **主要按钮**（深青绿实心）：一页最多 1–2 个。用于"更新全部启用来源""筛选""保存分类"。
2. **次要按钮**（白底描边）：批量操作（标为已读/未读、AI 分类、AI 总结）、导出、分页。
   未选中条目时批量按钮 `disabled` 并降至 45% 不透明度。
3. **文字按钮**（无边框，主色文字）：更多筛选、清除分类编辑的"取消"、卡片内的低密度操作。
4. **危险按钮**（红描边，hover 变红底白字）：仅用于破坏性操作（如删除来源、清除 API Key）。
   资讯列表页没有破坏性操作，故本页未出现；样式已定义在 `.btn-danger` 供来源/设置页使用。

卡片内操作（`.action-btn`）是第五种更轻的形态：无边框灰字，hover 才出现底色，
保证"存在但不抢眼"——尤其 AI 分类 / AI 总结，刻意不使用主色，避免 AI 喧宾夺主。

## 4. 标签使用限制

- 每条资讯**只显示一个分类标签**（`.category-chip`，主色浅底）。
- 唯一的彩色例外：`待分类` 使用低饱和琥珀色，提示需要人工处理——这是全页唯一的"行动召唤色"。
- 未读只用 8px 圆点 + 卡片左侧 3px 色条，**不显示"未读"文字徽章**；已读默认没有任何标识。
- 不显示"自动分类/规则分类"等来源徽章（移入"更多信息"展开区），不显示"已收藏"徽章（收藏按钮自身状态已表达）。
- AI 摘要不加徽章，直接在摘要位置呈现（生产模板可保留 `AI 摘要：` 前缀文本）。

## 5. 响应式规则

断点与行为（已按 1920 / 1440 / 1024 / 768 验证目标设计）：

- **≥1500px**：筛选主行所有控件一行排完，搜索框弹性占满剩余宽度；方案 B 四列完整。
- **1200–1500px**：下拉控件由 150px 收窄至 138px，仍保持单行；不换行、不挤压。
- **768–1200px**：筛选自然换行为两行，搜索框始终最宽；列表工具栏允许折行但按钮保持横排。
- **≤900px**：方案 B 转为上下结构（分类并入元信息行，操作列缩窄贴右，展开面板整行）。
- **≤768px**：筛选控件两列均分宽度（绝不退化成"宽屏单列 + 右侧空白"）；页面头部上下堆叠；
  统计栏允许换行；卡片内时间元信息换行显示；方案 B 操作按钮只留图标。
- **≤480px**：筛选控件才允许单列（此时单列是正确选择）。

全局 `overflow-x: hidden` 兜底，页面任何宽度不横向溢出。

## 6. 现有后端功能映射

原型每个区域对应的现有功能（路由见 `app/web/routes/pages.py`）：

| 原型元素 | 现有后端 |
| --- | --- |
| 顶部导航 资讯 / AI / 来源 / 设置 / 更新记录 | `GET /`、`GET /ai`、`GET /sources`、`GET /settings`、`GET /runs` |
| 更新全部启用来源 | `POST /updates` |
| 统计栏 全部资讯 | `page.total`；未读 / 今日新增 / 待分类可在现有查询上加 count 聚合，或暂用筛选链接替代 |
| 搜索标题和摘要 | query `keyword` |
| 分类 / 来源 / 阅读状态 | query `category`、`source_id`、`is_read` |
| 时间范围（今天/近 3 天…） | 前端换算为 `published_from` / `published_to` 后提交，后端无需改动 |
| 更多筛选：收藏 / 发布、发现时间 / 可信 / 审核 / 待分类 / 每页 | query `favorite`、`published_from/to`、`discovered_from/to`、`verification_status`、`review_status`、`unclassified`、`per_page` |
| 标为已读 / 未读（批量） | `POST /items/batch-read`（隐藏域 `item_ids`、`is_read`、`return_to`） |
| AI 分类 / AI 总结（批量） | `POST /items/batch-ai-classify`、`POST /items/batch-ai-summarize` |
| 导出 Excel / Word | `POST /exports/excel`、`POST /exports/word`（携带当前筛选隐藏域） |
| 查看原文并标为已读 | `item.original_url` + 现有 `markRead(item_id)` 逻辑 |
| 收藏 / 已读（单条） | `POST /items/{id}/favorite`、`POST /items/{id}/read` |
| 修改分类（编辑器默认收起） | `POST /items/{id}/category`（select name=`category`，空值=清除人工分类） |
| AI 分类 / AI 总结（单条） | `POST /items/{id}/ai-classify`、`POST /items/{id}/ai-summarize` |
| 更多信息展开区 | 现有 `item-details` 内容：信息形态、可信状态、审核状态、分类方式、来源类型 |

## 7. 接入真实 Jinja 模板时的注意事项

1. **保留交互结构，替换数据**：原型中卡片/行的 DOM 结构（`.item-card` / `.item-row` 及其子元素 class）
   就是建议的 Jinja 输出结构；`prototype.js` 的 `renderCard` / `renderRow` 可直接当作模板片段参照。
2. **保持"默认折叠"由服务端渲染**：`category-editor`、`item-more`、方案 B 的 `row-expand` 在 HTML 中
   输出 `hidden` 属性，JS 只负责切换，保证无 JS 时页面仍然整洁（生产可用 `<details>` 替代）。
3. **两套列表只渲染一套**：原型为演示同时渲染两套 DOM。生产应只输出当前视图的一套，
   视图偏好用 query 参数（如 `view=compact`）或用户设置持久化。
4. **已读状态由 class 表达**：`is-unread` 决定未读圆点与左侧色条；不要在已读条目上输出任何徽章。
5. **分类标签文本必须用 `category_label()`**，禁止把 `model_technology` 等枚举值输出到页面；
   可信/审核等同理使用 `verification_label()` / `review_label()`。原型中所有可见文案均为中文。
6. **摘要截断交给 CSS**：输出完整摘要文本，用 `-webkit-line-clamp` 截 2 行（方案 B 截 1 行），
   不要在后端截断字符串，以保留"展开全部"能力。
7. **统计栏数字**如果暂不做聚合查询，可先只展示 `page.total`，其余三项留待后续迭代，不要硬编码。
8. **无 JS 降级**：筛选、导出、单条操作本质都是 form GET/POST；原型的 JS 增强（批量勾选、
   就地展开编辑器）不应破坏纯表单提交路径。
9. **样式迁移**：`prototype.css` 变量块可整体并入 `app/web/static/styles.css`，
   组件 class 命名（`item-card`、`list-toolbar` 等）与现有模板无冲突，迁移时按组件逐个替换。

## 8. 必须保留的 form action / route / name / id / query parameter

接入时以下契约**不可更改**，否则后端路由会 404 或收不到参数：

**路由与 form action**

- `POST /updates`
- `POST /exports/excel`、`POST /exports/word`
- `POST /items/batch-read`、`POST /items/batch-ai-classify`、`POST /items/batch-ai-summarize`
- `POST /items/{item_id}/favorite`、`/read`、`/category`、`/ai-classify`、`/ai-summarize`
- 筛选用 `GET /`（GET 表单，参数进 query string）

**input / select 的 name**

- 筛选：`keyword`、`category`、`source_id`、`is_read`、`favorite`、`published_from`、`published_to`、
  `discovered_from`、`discovered_to`、`per_page`、`verification_status`、`review_status`、`unclassified`
  （以及现有 `primary_type`、`source_scope`，可在更多筛选中按需保留）
- 单条操作隐藏域：`favorite`（true/false）、`is_read`（true/false）、`category`、`return_to`
- 批量表单隐藏域：`item_ids`（逗号分隔 id 串）、`is_read`、`return_to`

**id（现有生产 JS 依赖）**

- `#batch-read-form`、`#batch-item-ids`、`#batch-ai-classify-form`、`#batch-ai-item-ids`、
  `.item-checkbox`（批量勾选收集）、`data-update-form` / `data-processing-text`（更新按钮 loading 态）

**query parameter**

- 分页：`page`、`per_page`；所有筛选参数见上。`return_to` 必须回传当前完整 query string，
  保证操作后重定向回到原筛选页。

## 9. 第一阶段范围（资讯页，已完成并获批准）

第一阶段完成：顶部导航、资讯首页完整布局、方案 A/B 双列表与切换、更多筛选折叠、单选/全选与批量按钮
启停、已读/未读、收藏、修改分类展开/保存/取消、更多信息展开、摘要展开收起、1920/1440/1024/768 响应式、
纯本地无外部依赖。

---

# 第二阶段：AI / 来源 / 来源详情 / 设置 / 更新记录（本阶段新增）

> 以下页面沿用第一阶段已批准的设计系统，未改动资讯页的任何布局、配色与交互。
> 新增样式全部以可复用组件形式追加在 `prototype.css`「全局可复用组件」一节。

## 10. AI 页面设计说明

定位：**业务人员的 AI 工具页**，不是开发者控制台。所有文案面向非技术用户（"接口地址"标注
Base URL 但不展开协议细节；错误提示说明"资讯不受影响"而不是抛 HTTP 堆栈）。

- **布局**：≥1024px 双栏（左：模型连接 + 配置说明；右：AI 分类 + AI 总结），下方全宽"最近 AI 任务"。
  <1024px 收为单栏。表单用 `.form-grid` 两列网格，接口地址与 API Key 占满整行（`.form-grid-wide`）。
- **页头状态**：右侧直接显示 `Key 已配置 / 未配置` 状态徽标 + 当前模型名，一进页面即可判断 AI 是否可用。
- **按钮层级**：保存设置=主要；测试连接=次要；清除 Key=危险文字按钮（`.btn-danger-text`），
  放在操作行最右侧，不与保存同级突出，点击需二次确认（生产中沿用现有 `confirm()` 即可）。
- **模式选择**：关闭/手动/自动参与更新用紧凑单选行（`.option-row`）：圆点 + 名称 + 一行说明，
  选中行浅主色底。选"自动参与更新"时才展开"自动分类策略"下拉，避免无关字段常驻。
- **费用与覆盖说明**：以 12px 灰字放在各区底部（`.foot-note`）："按调用量计费，混合策略费用更低"
  "AI 摘要单独保存，不会覆盖来源原始摘要"。
- **最近任务**：紧凑 `.data-table`，11 列；失败/部分失败行整行可点击展开错误详情（`.tr-expand`），
  长错误收在 `.error-box` 内，绝不铺在表格里。`跳过/回退/模型` 三列为 `.col-optional`，<1200px 隐藏。
- **真实功能对照**（全部保留）：`POST /ai/save`（含 provider/base_url/model/api_key/timeout_seconds/
  max_retries/classifier_mode/classifier_strategy/summarizer_mode）、`POST /ai/test-connection`、
  `POST /ai/clear-key`、`POST /ai/classify`（空 item_ids=全部待分类）、`POST /ai/summarize`（retry=1=仅重试失败项）、
  `ai_ops.get_recent_jobs(10)` 任务表。
- **原型演示、需绑后端**：测试连接loading与结果条（真实为表单提交后 query 回显 `test_result/test_ok`）、
  清除 Key 后的界面降级（禁用执行按钮、Key 徽标变灰）、待分类/未总结数量（需后端提供 count，
  现模板没有，可用固定文案或后续补充）。

## 11. 来源与来源详情设计说明

定位：让普通用户回答三个问题——**监控了哪些网站、是否正常、出问题怎么办**。

### 来源列表

- **页头**：标题 + 同步来源目录（次要，对应 `POST /sources/seed-formal`）+ 添加来源（主要，`GET /sources/new`）。
  统计条：总数 / 已启用 / 需要关注 / 候选。
- **页签**：`监控中 N` / `候选 N`（`.tabs`）。候选区先放一段 `.notice`，用业务语言说明
  "先预览确认内容符合预期，再启用并加入监控；启用后参与每次批量更新"——不出现 preview/activate 等词。
- **表格列**：来源（名称 + 域名）、类型（官方机构/企业官方/媒体 + 采集方式）、运行状态、启用（开关）、
  最近更新、最近结果、本次获取、操作（详情 / 更新）。状态只保留五个自然中文值：
  正常 / 部分可用 / 最近失败 / 已停用 / 候选，由后端 `lifecycle_state + implementation_status + last_error`
  组合映射，不直接输出枚举。
- **错误不铺开**：有错误的行在状态列下显示"查看错误"，点击展开整行 `.error-box`。
- **启用开关**（`.switch`）：行内直接切换，停用后状态列变"已停用"、更新按钮禁用；生产中对应
  `POST /sources/{id}/enabled`（hidden `enabled`、`return_to`）。
- **候选表**：来源、类型、检测结果、最近预览、预览数量、操作（预览 / 启用并加入监控）。
  预览=`POST /sources/{id}/preview`；启用=`POST /sources/{id}/activate`（hidden `confirm=true`），
  点击弹确认说明启用后的影响。

### 来源详情

- 页头：返回链接 + 名称 + 状态徽标 + URL；右侧操作：停用/启用（次要）、更新此来源（主要，
  `POST /sources/{id}/updates`）。
- **事实网格**（`.facts-grid`）：来源类型、采集方式、来源角色、审核策略、最近检查、最近结果——
  只展示普通用户需要知道的，slug、crawl_mode 原始值、配置 JSON 不上页面（与生产模板一致）。
- **近 30 天统计条**：抓取 / 通过准入 / 未通过准入 / 新增 / 更新 / 失败（复用 `.stats-strip`）。
- **最近错误**：仅存在时显示 `.notice.is-error` 一条，不给堆栈。
- **基本信息表单**：名称、默认分类、来源说明、"参与批量更新"开关 + 保存修改（`POST /sources/{id}/edit`，
  字段 name/default_category/description/enabled 与现模板一致）。
- **最近运行**：`.mini-table` 三次记录（时间/触发/结果/抓取/新增）+ 重新检测来源
  （`POST /sources/{id}/rediscover`，说明"生成独立预览，确认前不覆盖配置"）。
- **最近抓取的资讯**：紧凑行列表 + "查看该来源全部资讯 →"（生产中 `GET /?source_id={id}`，
  需后端在详情页提供最近 N 条查询，属新增小查询，不影响现有接口）。

## 12. 设置页面设计说明

原则：**只做小而完整的真实页面**。生产系统当前仅支持定时更新设置
（`POST /settings`：enabled/schedule_time/days/timezone），因此页面只有三组内容，
不虚构分页、导出等不存在的偏好：

1. **定时更新表单**：开关（`.switch`，关闭时其余字段禁用）、每天执行时间（time）、时区（IANA 文本）、
   执行星期（`.weekday-chip` 多选胶囊，比 7 个复选框更紧凑且不易错位）、保存设置（主要按钮）。
2. **当前状态**（`.kv-list`）：调度状态徽标、下一次计划运行、最近一次计划触发、最近修改。
3. **运行说明**（`.note-list`）：应用需保持运行、错过的任务不补跑、手动与定时互斥——沿用生产原文案。
   页面说明中引导 AI 相关设置前往「AI」页面，避免两个页面职责混淆。

## 13. 更新记录设计说明

定位：业务运行结果页——**每次更新发生了什么、哪一步少了、为什么**。

- **统计条**：记录总数 / 近 7 天成功 / 部分失败 / 失败。
- **筛选**：状态 + 触发方式（原型为前端演示过滤；生产可加 query 参数，当前路由仅支持分页）。
- **表格 13 列**：状态（徽标 + #编号）、触发方式、开始/完成（两行一列）、耗时、来源（成功/总数）、
  抓取、通过准入、拒绝、分类、新增、更新、重复、失败。数字列 `.num` 等宽便于横向扫读；
  `耗时/分类/更新/重复` 为 `.col-optional`，<1200px 隐藏（数据仍在行展开中可见）。
- **状态色克制**：成功绿 / 部分失败琥珀 / 失败红，仅徽标小面积使用。
- **行展开详情**（点击整行）：三栏 `.expand-grid`——各来源结果 `.mini-table`（来源/结果/抓取/准入/新增/备注）、
  未通过准入原因与处理失败原因 `.reason-list`（原因中文标签 + 数量，对应 `rejection_reason_counts` /
  `failure_reason_counts` 与 `PROCESS_REASON_LABELS`）、运行信息（耗时、触发、AI 调用、错误摘要 `.error-box`）。
- **真实功能对照**：`GET /runs` 分页列表全部字段；各来源结果对应 domain 中按来源的运行统计
  （需后端在模板上下文中补充该查询，现有模型已存储）；AI 调用情况来自 `ai_jobs`（trigger=auto），
  如当次无自动 AI 任务则不显示该区块。

## 14. 全局组件清单（第二阶段新增，全部可复用）

| 组件 | class | 用途 |
| --- | --- | --- |
| 区块卡片 | `.section-card` + `.section-head` | 各页内容分组，标题 + 一句说明 |
| 表单网格 | `.form-grid` / `.form-grid-wide` / `.form-stack` / `.form-actions` | 两列表单，宽字段整行 |
| 危险文字按钮 | `.btn-danger-text` | 清除 Key 等低频危险操作 |
| 提示条 | `.notice`（`.is-success` / `.is-error`） | 状态回显与说明 |
| 备注列表 | `.note-list` | 配置说明、运行说明 |
| 状态徽标 | `.status`（`-ok/-warn/-error/-muted/-info`） | 全站统一状态，克制用色 |
| 单选选项行 | `.option-list` / `.option-row` / `.option-extra` | AI 模式选择（替代巨型卡片） |
| 页签 | `.tabs` / `.tab` / `.tab-count` | 来源监控中/候选 |
| 数据表格 | `.table-wrap` + `.data-table`（`.table-cards` 响应式变体） | 来源/任务/运行记录 |
| 行内操作 | `.row-ops` / `.op`（`.op-danger`） | 表格内文字操作，横向排列 |
| 可展开行 | `.tr-expandable` / `.tr-expand` / `.expand-caret` | 运行记录、AI 任务、来源错误 |
| 展开内容 | `.expand-grid` / `.expand-block` / `.mini-table` / `.reason-list` / `.error-box` | 行详情 |
| 键值列表 | `.kv-list` / `.kv-row` | 当前状态、运行信息 |
| 事实网格 | `.facts-grid` / `.fact` | 来源详情摘要 |
| 开关 | `.switch` / `.switch-row` | 启用来源、定时更新 |
| 星期胶囊 | `.weekday-chips` / `.weekday-chip` | 设置页执行星期 |
| 返回链接 | `.back-link` | 详情页返回 |
| 空状态 | `.empty-state` | 筛选无结果、无候选 |
| 可选列 | `.col-optional` | <1200px 隐藏的次要表格列 |

## 15. 第二阶段响应式规则

- **≥1200px**：全部列显示；AI/设置/详情双栏布局。
- **≤1200px**：`.col-optional` 列隐藏（耗时/分类/更新/重复/跳过/回退/模型），数据收进行展开详情。
- **≤1024px**：双栏布局收单栏；`.table-cards` 表格转卡片式（每行一张卡，单元格带 `data-label` 标签，
  展开行保持可开合并整行显示；卡片化选择器仅匹配 `> tbody > tr > td` 直接子代，
  避免穿透展开区内的 `.mini-table`）。
- **≤768px**：`.form-grid` 单列；页头操作按钮换行不竖排；事实网格两列；星期胶囊紧凑。
- 已验证：五个页面在 1920/1440/1024/768 下 `scrollWidth ≤ innerWidth`，无横向溢出
  （含运行记录行展开状态）。修复过的两类问题：隐藏 checkbox 需有定位上下文父级（`.weekday-chip`），
  卡片化表格需直接子代选择器 + 显式保持 `.tr-expand` 隐藏。

## 16. 第二阶段生产接入契约（不可更改的既有约定）

**AI**：`POST /ai/save` 表单字段 `provider/base_url/model/api_key/timeout_seconds/max_retries/
classifier_mode/classifier_strategy/summarizer_mode`；`POST /ai/test-connection`（同表单字段，
结果经 `?test_result=&test_ok=` 回显）；`POST /ai/clear-key`；`POST /ai/classify`（`item_ids` 空=全部）；
`POST /ai/summarize`（`retry=1` 仅重试失败项）。Key 输入框保持 `type=password` 与"留空保留旧 Key"语义。

**来源**：`GET /sources?filter=&per_page=&page=`；`POST /sources/seed-formal`；`POST /sources/{id}/enabled`
（`enabled=true/false`、`return_to`）；`POST /sources/{id}/updates`；`POST /sources/{id}/preview`；
`POST /sources/{id}/activate`（`confirm=true`）；`GET /sources/{id}`；`POST /sources/{id}/edit`
（`name/default_category/description/enabled`）；`POST /sources/{id}/rediscover`。

**设置**：`POST /settings`（`enabled/schedule_time/days/timezone`，`days` 为多值）。

**更新记录**：`GET /runs?page=&per_page=`。

**原型中仅作演示、生产中需绑定真实后端的交互**：
AI 测试连接 loading 与结果条、清除 Key 后的降级、待分类/未总结数量、来源筛选（生产现为
`filter` 单参数，多条件筛选需扩展查询）、来源启用开关（生产为表单 POST 整页刷新，原型为就地切换）、
候选启用确认弹窗（生产已有 confirm，可保留）、详情页"最近抓取的资讯"与"近 30 天统计"
（需后端补充两个小查询）、运行记录状态/触发方式筛选（需后端补 query 参数）、
所有 toast 提示（生产为提交后重定向 + `?saved=1` 等回显）。

## 17. 本阶段做了/没做什么

做了：AI、来源（监控中/候选页签）、来源详情、设置、更新记录五个页面的完整静态原型；
全局组件整理；14 张真实截图（全部目检）；五页面 × 四宽度横向溢出自动化检查；交互断言
（AI 模式联动、来源筛选/启用/候选启用、运行记录筛选/展开、详情加载）。

没做（有意）：未修改 `app/`、`tests/`、`data/`、配置与迁移；未接入任何生产模板；
未运行真实抓取与 AI 调用；添加来源与自动发现页面（`/sources/new`、`/sources/discover`）
不在本轮范围，原型中以提示说明；资讯页保持已批准状态未改动。
