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

## 9. 本原型做了/没做什么

做了：顶部导航、资讯首页完整布局、方案 A/B 双列表与切换、更多筛选折叠、单选/全选与批量按钮
启停、已读/未读、收藏、修改分类展开/保存/取消、更多信息展开、摘要展开收起、占位页切换、
1920/1440/1024/768 响应式、纯本地无外部依赖。

没做（有意）：不修改 `app/` 任何文件；不发起任何真实请求；AI、来源、设置、更新记录页仅占位；
登录/权限、审核流操作（`POST /items/{id}/review`）未在本轮范围内。
