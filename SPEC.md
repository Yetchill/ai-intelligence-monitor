# AI行业动态与成果申报情报工具

## 技术设计与开发规格书 v0.2

---

## 1. 项目背景

本项目是供公司主任或部门内部使用的轻量信息聚合工具。

系统访问一批人工维护的可靠信息源，自动发现这些网站中的新增文章、通知、案例和产品更新，提取标题、链接、来源、发布时间及可用简介，对信息进行分类和去重，最终通过本地网页集中展示，并支持导出 Excel 和 Word。

本项目不是搜索引擎，也不是自主寻找全网信息的 Agent。

信息源由开发者预置，或由普通用户在网页中自行添加。程序负责从已经确认的信息源中自动发现文章标题、链接和后续新增内容。

---

## 2. 项目目标

第一版必须实现以下完整流程：

```text
人工配置或用户添加可靠信息源
→ 系统检测信息源类型并预览
→ 程序访问列表页、RSS、GitHub Releases 或公开接口
→ 自动发现文章标题和链接
→ 与本地历史数据比较
→ 识别新增或更新内容
→ 自动分类
→ 保存至 SQLite
→ 在本地网页中展示
→ 导出 Excel 和 Word
```

每条有效信息必须具备：

- 标题；
- 原始链接；
- 来源；
- 分类；
- 首次发现时间。

尽量提取但不强制要求：

- 发布时间；
- 网页原有简介、摘要或导语；
- 附件名称及附件链接；
- 相关标签。

完整正文不是第一版必需内容。用户看到标题和简介后，可点击原始链接前往原网站查看详情。

---

## 3. 使用场景

### 3.1 主任日常使用

```text
双击启动程序
→ 浏览器自动打开本地页面
→ 点击“立即更新”
→ 查看本次新增信息
→ 按分类、来源、日期筛选
→ 点击标题进入原始网页
→ 收藏、修改分类或导出结果
```

### 3.2 主任自行添加信息源

```text
发现一个值得长期关注的新网站
→ 复制网站首页、新闻栏目、通知栏目或 RSS 地址
→ 打开“信息源管理”
→ 点击“添加信息源”
→ 系统自动检测类型并展示抓取预览
→ 用户确认后保存
→ 后续更新时自动检查该来源
```

系统不承诺自动适配任意网站。

对于 RSS、GitHub Releases 和结构简单的普通列表页，应尽量自动支持；对于 JavaScript 动态加载、登录、验证码、强反爬或结构特殊的网站，应明确提示“需要开发者适配”。

### 3.3 开发者维护信息源

开发者添加的不是单篇文章，而是：

- RSS 地址；
- 新闻列表页；
- 通知栏目页；
- 案例栏目页；
- GitHub Releases 地址；
- JSON 公开接口；
- 网站专用采集器。

### 3.4 首次初始化

系统可以根据配置抓取一定范围的历史数据：

- 技术和产品更新：最近 3 至 6 个月；
- 企业成果与获奖案例：最近 1 至 3 年；
- 申报和征集通知：最近 6 至 12 个月。

首次初始化完成后，日常更新只处理新增和发生变化的信息。

---

## 4. 第一版功能范围

### 4.1 信息源类型

第一版支持：

1. RSS / Atom；
2. 普通 HTML 列表页；
3. GitHub Releases；
4. JSON 公开接口；
5. 网站专用采集器。

第一版不做无限制的全站递归爬取，也不做大规模全网关键词搜索。

### 4.2 信息分类

使用以下一级分类：

```text
model_technology
模型与技术动态

agent_product
智能体与产品更新

enterprise_case
企业成果与应用案例

award_case
获奖与优秀案例

solicitation
奖项与成果征集

policy_industry
政策、标准与行业动态

unclassified
待确认
```

### 4.3 页面功能

本地网页至少包括：

- 首页信息流；
- 分类筛选；
- 来源筛选；
- 日期筛选；
- 标题和简介关键词搜索；
- 本次新增筛选；
- 收藏功能；
- 人工修改分类；
- 立即更新；
- 更新状态和结果统计；
- 信息源管理；
- 信息源测试与预览；
- Excel 导出；
- Word 导出。

### 4.4 第一版暂不实现

- 登录和多用户权限；
- 云端部署；
- 强制抓取完整正文；
- 自动突破验证码和登录限制；
- 大规模全网关键词搜索；
- 新闻语义聚类；
- 本地大模型；
- 自动生成奖项申报材料；
- 自动下载全部附件；
- 多智能体系统；
- 可视化点击网页元素生成采集规则；
- 自动为复杂网站生成专用爬虫代码。

---

## 5. 技术选型

### 5.1 基础环境

- Python 3.12；
- uv 管理 Python 环境和依赖；
- Windows 为最终主要运行平台；
- macOS 和 Linux 可用于开发；
- 第一版不依赖 Docker。

### 5.2 后端和本地页面

- FastAPI；
- Uvicorn；
- Jinja2；
- 原生 HTML、CSS 和少量 JavaScript；
- 不使用 React、Vue 等大型前端框架；
- 所有前端静态资源保存在项目本地，不依赖 CDN。

本地服务只监听：

```text
127.0.0.1
```

禁止默认监听：

```text
0.0.0.0
```

### 5.3 数据采集

- httpx：HTTP 请求；
- feedparser：RSS 和 Atom 解析；
- BeautifulSoup4 + lxml：HTML 列表解析；
- dateparser：日期解析；
- tenacity：失败重试；
- urllib.robotparser：robots.txt 基础判断。

第一版不默认安装 Playwright。

后续如某些重要网站必须使用浏览器渲染，可通过独立 `BrowserFetcher` 插件加入。

### 5.4 数据库

- SQLite；
- SQLAlchemy 2.x；
- Alembic 数据库迁移。

### 5.5 导出

- openpyxl：Excel；
- python-docx：Word。

### 5.6 项目质量

- pytest；
- pytest-asyncio；
- Ruff；
- Pyright 或 mypy；
- pre-commit 可选。

---

## 6. 总体架构

系统使用分层、可替换、可扩展的模块结构。

```text
UI / API 层
    ↓
Application 服务层
    ↓
信息源发现、采集、分类、去重、导出接口
    ↓
SQLite 与外部网站适配器
```

核心流水线：

```text
SourceRegistry
→ Collector
→ Normalizer
→ Deduplicator
→ Classifier
→ Repository
→ Exporter
```

添加信息源流水线：

```text
用户输入 URL
→ SourceDiscoverer 自动检测
→ 生成候选采集配置
→ Preview 预览标题和链接
→ 用户确认
→ 保存至 SQLite
→ 后续由 Collector 正式采集
```

架构约束：

- 界面不得直接编写爬虫逻辑；
- 采集器不得直接操作 HTML 页面模板；
- 分类器不得直接操作数据库；
- AI 功能不得嵌入采集器；
- 信息源发现器和正式采集器必须分开；
- 所有模块通过统一数据结构进行通信。

---

## 7. 推荐目录结构

```text
ai-intelligence-monitor/
├── SPEC.md
├── pyproject.toml
├── uv.lock
├── README.md
├── CHANGELOG.md
├── .env.example
├── .gitignore
├── start.bat
├── start.command
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── launcher.py
│   ├── cli.py
│   │
│   ├── domain/
│   │   ├── models.py
│   │   ├── enums.py
│   │   └── interfaces.py
│   │
│   ├── services/
│   │   ├── crawl_service.py
│   │   ├── classification_service.py
│   │   ├── export_service.py
│   │   ├── source_service.py
│   │   ├── discovery_service.py
│   │   └── update_pipeline.py
│   │
│   ├── discoverers/
│   │   ├── base.py
│   │   ├── feed.py
│   │   ├── github.py
│   │   └── generic_html.py
│   │
│   ├── collectors/
│   │   ├── base.py
│   │   ├── rss.py
│   │   ├── html_list.py
│   │   ├── github_release.py
│   │   ├── json_api.py
│   │   └── custom/
│   │
│   ├── fetchers/
│   │   ├── base.py
│   │   ├── http.py
│   │   └── browser.py
│   │
│   ├── parsers/
│   │   ├── link_parser.py
│   │   ├── metadata_parser.py
│   │   ├── date_parser.py
│   │   └── attachment_parser.py
│   │
│   ├── classifiers/
│   │   ├── base.py
│   │   ├── rule_based.py
│   │   ├── manual.py
│   │   ├── hybrid.py
│   │   └── llm.py
│   │
│   ├── storage/
│   │   ├── database.py
│   │   ├── repositories.py
│   │   └── migrations/
│   │
│   ├── exporters/
│   │   ├── base.py
│   │   ├── excel.py
│   │   └── word.py
│   │
│   ├── web/
│   │   ├── routes/
│   │   ├── templates/
│   │   └── static/
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── preset_sources.yaml
│   │   └── classification_rules.yaml
│   │
│   └── utils/
│       ├── url.py
│       ├── hashing.py
│       ├── logging.py
│       └── text.py
│
├── data/
│   └── .gitkeep
├── output/
│   └── .gitkeep
├── logs/
│   └── .gitkeep
├── tests/
│   ├── fixtures/
│   ├── unit/
│   └── integration/
└── docs/
    ├── architecture.md
    ├── source-development.md
    └── classification.md
```

---

## 8. 核心数据模型

### 8.1 Source

表示一个信息源入口。

```python
class Source:
    id: int
    name: str
    source_type: str
    start_url: str
    enabled: bool

    default_category: str | None
    collector_name: str
    collector_config: dict

    discovery_status: str | None
    discovery_confidence: float | None
    requires_custom_collector: bool

    origin: str
    # preset / user_added / imported

    last_tested_at: datetime | None
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None

    created_at: datetime
    updated_at: datetime
```

`source_type` 支持：

```text
rss
html_list
github_release
json_api
custom
```

`collector_config` 用于保存：

- CSS 选择器；
- XPath；
- 允许域名；
- 允许子域名；
- 链接包含或排除规则；
- 日期解析规则；
- 最大页面数；
- 详情页策略。

不得为每个新增网站修改数据库表结构。

### 8.2 IntelligenceItem

表示一条采集到的信息。

```python
class IntelligenceItem:
    id: int
    source_id: int
    title: str
    original_url: str
    canonical_url: str
    summary: str | None
    published_at: datetime | None
    discovered_at: datetime
    last_seen_at: datetime
    category: str
    classification_score: float | None
    classification_reason: str | None
    automatic_category_provider: str | None
    manual_category: str | None
    fingerprint: str
    is_favorite: bool
    is_active: bool
    extra: dict
```

最终展示分类优先级：

```text
manual_category
> AI 分类结果
> 规则分类结果
> 来源默认分类
> unclassified
```

### 8.3 CrawlRun

记录一次完整更新任务。

```python
class CrawlRun:
    id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    source_total: int
    source_success: int
    source_failed: int
    discovered_count: int
    new_count: int
    updated_count: int
    skipped_count: int
    unclassified_count: int
    error_summary: str | None
```

### 8.4 ItemRevision

当已有信息的标题、简介、发布时间或附件发生变化时保存修订记录。

```python
class ItemRevision:
    id: int
    item_id: int
    changed_at: datetime
    old_data: dict
    new_data: dict
```

---

## 9. 信息源存储原则

SQLite 数据库中的 `sources` 表是运行时信息源的唯一数据来源。

`config/preset_sources.yaml` 仅用于：

- 保存系统预置来源；
- 首次启动时导入默认来源；
- 开发和测试；
- 备份、导入和导出信息源配置。

系统启动后不得在数据库和 YAML 之间进行双向实时同步。

用户通过网页新增或修改的信息源只写入 SQLite。

数据库迁移和程序升级不得覆盖用户自行添加的信息源。

---

## 10. 信息源自助添加流程

### 10.1 第一步：输入网址

用户填写：

- 来源名称，可暂时留空；
- 入口网址；
- 默认业务分类，可选择“自动判断”；
- 是否立即启用。

系统首先执行：

1. URL 格式校验；
2. 规范化 URL；
3. 检查是否已经存在；
4. 检查协议是否为 HTTP 或 HTTPS；
5. 获取网页；
6. 判断页面类型。

### 10.2 第二步：自动检测

系统按顺序尝试识别：

1. RSS 或 Atom；
2. GitHub 仓库或 Releases；
3. JSON 公开接口；
4. 普通 HTML 列表页。

对于普通网页，系统尝试：

- 读取页面中的 RSS 发现标签；
- 查找常见 Feed 地址；
- 提取页面中的文章候选链接；
- 排除导航、登录、注册、联系我们等链接；
- 推断可能的标题、日期和简介；
- 计算通用列表采集器是否可用。

自动检测结果应返回：

```text
检测类型：普通网页列表
发现候选信息：12 条
可获取标题：是
可获取链接：是
可获取日期：8/12
可获取简介：3/12
检测置信度：中
```

### 10.3 第三步：预览并确认

页面展示最多 10 条预览：

- 标题；
- 发布时间；
- 简介；
- 原始链接；
- 预测分类。

只有测试成功且至少发现一条有效的“标题＋链接”记录，才允许直接保存并启用。

### 10.4 自动检测状态

```text
ready
通用采集器可以直接使用

partial
可以获取标题和链接，但日期或简介可能缺失

needs_configuration
发现了候选链接，但需要人工选择栏目或配置规则

needs_custom_collector
通用采集器无法可靠处理，需要开发者编写专用采集器

blocked
网站需要登录、出现验证码、拒绝访问或明确无法抓取

unreachable
网站当前无法访问
```

不得将检测失败简单显示为“未知错误”。

---

## 11. 普通网页自动发现规则

系统接收到一个普通网页入口后，可以自动寻找站内候选信息，但必须限制范围。

默认规则：

```text
最大扫描深度：1
最大扫描页面数：20
只跟踪同域名链接
默认不跨子域名
单域名并发数：2
```

自动优先保留链接文字或 URL 中包含以下内容的页面：

```text
新闻
动态
通知
公告
征集
申报
案例
成果
获奖
政策
标准
发布
更新
```

自动排除：

```text
登录
注册
联系我们
关于我们
成员介绍
组织架构
活动日历
招聘
下载中心首页
javascript:
mailto:
图片、视频和静态资源
```

系统可以推荐可能的栏目，但不得默认无限递归抓取整个网站。

用户可以在高级设置中选择允许的子域名。

---

## 12. 信息源配置示例

```yaml
sources:
  - id: aiia_home
    name: 中国人工智能产业发展联盟
    type: html_list
    enabled: true

    start_urls:
      - https://www.aiiaorg.cn/

    allowed_domains:
      - aiiaorg.cn
      - aihub.caict.ac.cn

    default_category: policy_industry

    discovery:
      mode: link_filter
      max_depth: 1
      max_pages: 50

      include_text:
        - 通知
        - 征集
        - 申报
        - 案例
        - 成果
        - 获奖
        - 发布
        - 标准

      exclude_text:
        - 登录
        - 注册
        - 联系我们
        - 联盟介绍
        - 活动日历

      include_url_patterns: []
      exclude_url_patterns:
        - "/login"
        - "/register"
        - "javascript:"
        - "#"

    extraction:
      title_selector: null
      link_selector: null
      date_selector: null
      summary_selector: null

    detail_policy: never
    request_interval_seconds: 2
```

支持两种 HTML 列表采集模式。

### 12.1 Selector 模式

适用于网页结构稳定的网站。

```yaml
discovery:
  mode: selectors

extraction:
  item_selector: ".news-list li"
  title_selector: "a"
  link_selector: "a"
  date_selector: ".date"
  summary_selector: ".summary"
```

### 12.2 Link Filter 模式

适用于首页或简单栏目页面。

系统获取所有链接后，根据以下条件判断是否保留：

- 是否属于允许域名；
- 是否为 HTTP 或 HTTPS；
- 链接文字是否像文章标题；
- 是否命中包含关键词；
- 是否命中排除规则；
- 是否为文件、图片、登录、注册等无关链接；
- 是否已经存在于数据库。

Selector 模式优先，Link Filter 模式作为通用兜底。

---

## 13. 抓取策略

### 13.1 请求限制

- 默认每个域名并发数：2；
- 全局并发数：5；
- 同域名请求间隔：1.5 至 3 秒；
- 默认超时：15 秒；
- 最大重试：2 次；
- 重试采用指数退避；
- 设置清晰的 User-Agent；
- 不绕过验证码、登录和明确禁止的访问限制。

### 13.2 URL 规范化

保存前必须：

- 删除 `utm_source` 等跟踪参数；
- 删除 URL 片段 `#...`；
- 统一尾部斜杠；
- 解析相对链接；
- 排除 `mailto:`、`javascript:`；
- 可配置保留必要查询参数。

### 13.3 详情页策略

每个来源可配置：

```text
never
不进入详情页

when_summary_missing
列表页没有简介时进入详情页

always
总是进入详情页
```

第一版默认：

```text
never
```

详情页不是必需流程。

### 13.4 增量更新

判断顺序：

1. canonical URL 完全匹配；
2. 同一来源中规范化标题匹配；
3. 标题、链接、简介生成的 fingerprint 匹配；
4. 已存在且 fingerprint 未变则跳过；
5. 已存在但 fingerprint 变化则更新并记录 Revision；
6. 不存在则新增。

---

## 14. 分类系统

### 14.1 分类接口

```python
class Classifier(Protocol):
    async def classify(
        self,
        item: IntelligenceItem,
        source: Source
    ) -> ClassificationResult:
        ...
```

返回：

```python
class ClassificationResult:
    category: str
    score: float
    reason: str
    provider: str
```

### 14.2 第一版规则分类器

分类综合以下信息：

```text
来源默认分类
+ 标题关键词
+ 标题词组组合
+ 简介关键词
+ 排除词
+ 分类优先级
```

示例规则：

```yaml
categories:
  solicitation:
    priority: 100
    phrases:
      "案例征集": 8
      "申报通知": 8
      "征集启动": 7
      "征集工作": 6
      "申报工作": 6
      "参评": 5
      "截止日期": 4
    keywords:
      "征集": 4
      "申报": 4
      "评选": 3
      "材料": 2
    negative_phrases:
      "申报上市": -10
      "征集意见结束": -3

  award_case:
    priority: 90
    phrases:
      "获奖名单": 8
      "优秀案例名单": 8
      "入选名单": 7
      "成功入选": 6
    keywords:
      "获奖": 5
      "入选": 4
      "表彰": 4
      "优秀案例": 4
```

### 14.3 分类判定

- 最高分达到阈值时采用该分类；
- 最高分和第二名差距过小时进入待确认；
- 没有分类达到阈值时使用来源默认分类；
- 来源默认分类也为空时进入待确认；
- 用户手动分类后永久优先采用人工分类。

### 14.4 AI 扩展

AI 功能不得嵌入采集器。

后续增加：

```text
RuleBasedClassifier
LLMClassifier
HybridClassifier
```

Hybrid 模式：

```text
规则分类置信度高
→ 直接使用规则结果

规则置信度低
→ 调用 AI 分类

AI 不可用
→ 进入待确认
```

AI 模型配置为空时，整个系统必须正常运行。

未来可继续增加独立接口：

```text
Summarizer
Ranker
EntityExtractor
```

不得因为增加 AI 功能重写现有采集和数据库代码。

---

## 15. UI 设计

页面风格参考 TrendRadar 的日报和信息卡片布局，但增加筛选、来源状态和操作按钮。

### 15.1 首页顶部

显示：

- 项目名称；
- 上次更新时间；
- 立即更新；
- 导出 Excel；
- 导出 Word；
- 暗色模式；
- 设置入口。

统计卡片：

```text
本次新增
本次更新
待确认
成功来源
失败来源
```

### 15.2 左侧分类导航

```text
全部信息
本次新增
模型与技术动态
智能体与产品更新
企业成果与应用案例
获奖与优秀案例
奖项与成果征集
政策、标准与行业动态
待确认
收藏
信息源管理
```

### 15.3 信息卡片

每条卡片展示：

- 分类标签；
- 新增标签；
- 标题；
- 来源；
- 发布时间；
- 简介；
- 首次发现时间；
- 查看原文；
- 收藏；
- 修改分类。

标题和“查看原文”均在新标签页打开原始网页。

### 15.4 搜索筛选

支持：

- 标题和简介关键词；
- 分类；
- 来源；
- 发布时间范围；
- 本次新增；
- 收藏；
- 待确认；
- 是否具有简介。

### 15.5 信息源管理页面

至少显示：

- 来源名称；
- 入口网址；
- 来源类型；
- 默认分类；
- 是否启用；
- 检测状态；
- 上次成功时间；
- 上次发现数量；
- 最近错误。

支持操作：

```text
添加
测试
预览
编辑
启用
停用
删除
重新检测
立即抓取该来源
```

删除来源时默认只删除来源配置，不删除已经抓取的历史信息。

如用户希望同时删除历史信息，必须进行二次确认。

### 15.6 更新过程

点击“立即更新”后：

- 按钮进入禁用状态；
- 页面显示当前执行状态；
- 显示正在处理的信息源；
- 完成后显示统计结果；
- 单个来源失败不影响其他来源；
- 不允许同时启动两个更新任务。

第一版可以使用轮询接口获取进度，不必实现 WebSocket。

---

## 16. Web API

```text
GET  /
首页

GET  /api/items
查询信息列表

GET  /api/items/{id}
查看单条信息

PATCH /api/items/{id}
修改分类、收藏等字段

POST /api/crawl-runs
启动更新任务

GET  /api/crawl-runs/current
查看当前任务进度

GET  /api/crawl-runs
查看历史运行记录

GET  /api/sources
查看信息源

POST /api/sources/discover
输入网址并检测来源类型

POST /api/sources/preview
使用临时配置预览抓取结果

POST /api/sources
保存新来源

GET  /api/sources/{id}
查看来源详情

PATCH /api/sources/{id}
修改来源

DELETE /api/sources/{id}
删除来源配置

POST /api/sources/{id}/test
重新测试来源

POST /api/sources/{id}/preview
预览该来源当前结果

POST /api/sources/{id}/crawl
只更新当前来源

GET  /api/export/excel
导出 Excel

GET  /api/export/word
导出 Word
```

`discover` 和 `preview` 接口不得直接把来源写入数据库。

导出接口必须接受与信息列表相同的筛选参数。

---

## 17. Excel 与 Word 导出

### 17.1 Excel 字段

```text
序号
标题
分类
来源
发布时间
简介
原文链接
首次发现时间
最后更新时间
是否收藏
```

要求：

- 标题或原文链接可点击；
- 表头冻结；
- 自动筛选；
- 合理列宽；
- 支持只导出当前筛选结果。

### 17.2 Word 结构

```text
AI 行业动态与成果申报情报汇总
生成时间
统计信息

一、模型与技术动态
1. 标题
   来源：
   发布时间：
   简介：
   原文：

二、智能体与产品更新
...
```

Word 中的原文链接必须可点击。

---

## 18. 启动与运行

### 18.1 开发环境

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.main
```

### 18.2 命令行入口

```bash
uv run python -m app.cli update
uv run python -m app.cli init-history
uv run python -m app.cli export-excel
uv run python -m app.cli export-word
```

所有界面和未来定时任务都调用同一套 Application Service。

### 18.3 一键启动

`launcher.py` 负责：

1. 检查数据库；
2. 执行数据库迁移；
3. 在 127.0.0.1 上寻找空闲高位端口；
4. 启动 Uvicorn；
5. 自动打开默认浏览器；
6. 程序退出时停止服务。

Windows 开发版提供：

```text
start.bat
```

后续稳定后使用 PyInstaller 或便携 Python 环境打包。

不得在核心功能稳定前优先处理 EXE 打包。

---

## 19. 存储空间控制

默认只保存结构化字段，不保存完整网页、图片和附件。

预计：

- 程序源码：小于 10 MB；
- Python 环境和依赖：约 150 至 350 MB；
- 打包便携版本：约 100 至 300 MB；
- 10,000 条记录：通常小于 100 MB；
- 长期运行总空间：通常低于 1 GB。

报告清理策略：

- 数据库长期保留；
- 日报默认只保留最近 30 天；
- 月报可以长期保留；
- 不自动下载附件。

---

## 20. 日志与错误处理

日志分为：

```text
application.log
crawler.log
error.log
```

要求：

- 日志滚动；
- 单个日志文件最大 10 MB；
- 默认保留 5 个历史文件；
- 日志不得记录 API Key；
- 每个来源的异常独立捕获；
- 请求失败、解析失败、分类失败分别记录；
- 页面必须能看到简化后的来源错误状态。

---

## 21. 安全要求

- 服务仅监听 127.0.0.1；
- 默认不需要管理员权限；
- 不创建防火墙规则；
- 不上传公司数据；
- 不执行网页中的脚本；
- 不自动打开或执行下载的附件；
- API Key 只能存放在环境变量或本地配置中；
- `.env` 不得提交 Git；
- 所有外部链接打开前进行协议检查。

---

## 22. 项目管理要求

### 22.1 版本管理

使用语义化版本：

```text
0.1.0 项目骨架、数据库与基础采集
0.2.0 分类、更新流水线与信息流页面
0.3.0 信息源自助添加、预览和管理
0.4.0 导出与一键启动
1.0.0 部门可稳定使用版本
```

### 22.2 Git 要求

- `main` 始终保持可运行；
- 每个开发阶段使用独立分支；
- 每完成一个阶段提交一次或数次小提交；
- 不允许一次提交整个项目；
- 每次提交附带简洁说明；
- 数据库、日志和导出文件不得提交；
- 不提交 API Key、Cookie 或公司内部敏感配置。

### 22.3 文档要求

必须维护：

```text
README.md
CHANGELOG.md
docs/architecture.md
docs/source-development.md
docs/classification.md
```

增加新的 Discoverer、Collector 或 Classifier 时，应同步更新文档。

### 22.4 数据库兼容

新增字段必须使用 Alembic 迁移。

禁止通过删除数据库解决模型变化。

---

## 23. 测试要求

### 23.1 单元测试

至少覆盖：

- URL 规范化；
- 相对链接解析；
- 标题清洗；
- 日期解析；
- fingerprint 生成；
- 去重逻辑；
- 分类规则；
- 分类阈值；
- 导出字段；
- 手动分类优先级；
- 信息源类型识别；
- 信息源检测状态；
- 预览不会写入数据库。

### 23.2 HTML 固定样本测试

将目标网站的脱敏 HTML 样本保存在：

```text
tests/fixtures/
```

测试不得全部依赖实时网络。

### 23.3 集成测试

至少准备以下来源：

1. 一个 RSS 源；
2. 一个 AI 公司新闻列表；
3. 一个政府或协会通知列表；
4. 一个 GitHub Releases 源；
5. 一个 JSON 接口源；
6. 一个用户通过网页自行添加的简单 HTML 来源。

### 23.4 异常测试

必须验证：

- 网站超时；
- 返回 403；
- 返回 404；
- HTML 结构变化；
- 日期缺失；
- 标题缺失；
- 数据库已存在重复链接；
- 某个来源失败；
- 更新按钮重复点击；
- 用户输入重复来源；
- 用户输入非 HTTP/HTTPS 地址；
- 来源需要登录或验证码；
- 自动检测失败但页面仍可正常使用。

---

## 24. 开发阶段与验收标准

### 阶段一：项目骨架和数据库

实现：

- `pyproject.toml`；
- 配置加载；
- SQLAlchemy 模型；
- Alembic；
- Repository；
- 基础日志。

验收：

- 可以初始化数据库；
- 可以创建和读取 Source；
- 可以创建和查询 IntelligenceItem；
- 测试通过。

### 阶段二：基础采集器

实现：

- HttpFetcher；
- RSSCollector；
- HTMLListCollector；
- GitHubReleaseCollector；
- URL 规范化；
- 基础重试。

验收：

- 至少三个真实来源能够采集标题和链接；
- 重复运行不会重复插入。

### 阶段三：分类系统和更新流水线

实现：

- RuleBasedClassifier；
- YAML 规则；
- 分类得分；
- 待确认；
- 人工分类覆盖；
- UpdatePipeline；
- CrawlRun；
- 增量检测；
- 单来源故障隔离。

验收：

- 使用固定测试标题验证六类分类；
- 分类原因可查询；
- 人工分类不会被自动结果覆盖；
- 某来源失败时其他来源继续；
- 更新记录可查询。

### 阶段四：基础本地网页

实现：

- FastAPI；
- 首页；
- 信息列表；
- 分类和来源筛选；
- 搜索；
- 收藏；
- 修改分类；
- 立即更新；
- 进度轮询。

验收：

- 浏览器可以完成核心使用流程；
- 标题可点击打开原文；
- 页面风格接近 TrendRadar 的信息卡片。

### 阶段五：信息源自助管理

实现：

- 数据库存储所有运行时来源；
- YAML 预置来源首次导入；
- SourceDiscoverer 接口；
- FeedDiscoverer；
- GitHubDiscoverer；
- GenericHtmlDiscoverer；
- 来源类型检测；
- 来源测试；
- 抓取结果预览；
- 新增、编辑、启用、停用和删除；
- 单来源立即抓取。

验收：

- 用户可以粘贴一个 RSS 地址并成功添加；
- 用户可以粘贴一个 GitHub Releases 地址并成功添加；
- 用户可以粘贴一个简单新闻列表页，预览标题和链接后保存；
- 无法自动适配的网站会显示具体原因；
- 新增来源不需要重启程序；
- 程序升级后用户来源仍然存在。

### 阶段六：导出

实现：

- ExcelExporter；
- WordExporter；
- 按筛选结果导出。

验收：

- Excel 和 Word 链接可点击；
- 中文显示正常；
- 筛选结果与导出结果一致。

### 阶段七：启动和稳定性

实现：

- `launcher.py`；
- `start.bat`；
- 自动打开浏览器；
- 端口自动选择；
- 日志滚动；
- Windows 实测。

验收：

- 普通用户无需输入命令即可启动；
- 程序退出后本地端口关闭；
- 不要求管理员权限。

### 阶段八：AI 扩展预留

只实现接口和空实现，不调用真实模型：

```text
LLMClassifier
Summarizer
HybridClassifier
```

验收：

- 未配置 API Key 时系统正常启动；
- 未来可以通过新增 Provider 实现模型调用；
- 现有采集和分类代码无需修改。

---

## 25. 第一批建议测试信息源

第一批控制在 8 至 12 个来源。

至少包含：

- AIIA；
- 中国信通院相关通知栏目；
- 一个政府部门 AI 相关栏目；
- DeepSeek 官方更新；
- 百度或文心官方更新；
- 智谱 AI 官方更新；
- 通义千问 GitHub Releases；
- 一个智能体平台更新源；
- 一个可靠行业媒体或 RSS 源。

每个来源独立验收，不要求一个通用采集器立即适配所有网站。

---

## 26. 第一版最终验收标准

系统达到以下条件后，视为第一版完成：

1. Windows 普通用户可以一键启动；
2. 不配置 AI Key 也能完整运行；
3. 可以管理并抓取至少 8 个预设来源；
4. 主任可以自行添加 RSS、GitHub Releases 和简单 HTML 列表来源；
5. 添加来源前可以预览标题和链接；
6. 每条有效信息一定有标题、链接、来源和分类；
7. 能正确识别新增信息；
8. 大部分信息可以被合理分类；
9. 不确定信息进入待确认；
10. 标题可以点击打开原网站；
11. 支持搜索、筛选、收藏和人工改分类；
12. 支持带可点击链接的 Excel 和 Word 导出；
13. 单个来源失败不会终止整个更新任务；
14. 后续加入 AI、浏览器抓取和新导出格式时不需要重写核心模块。

---

## 27. 给 Codex 的实现约束

Codex 必须遵守：

- 先完整阅读本技术文档再修改代码；
- 严格按照开发阶段逐步实现；
- 第一轮只实现阶段一；
- 每完成一个阶段先运行测试；
- 不一次性生成全部项目；
- 不自行增加 React、Redis、Celery、Docker 等重型依赖；
- 不把所有逻辑写入单个文件；
- 不将 AI 功能设为强依赖；
- 不为了适配一个网站破坏通用接口；
- 不通过删除数据库处理数据模型变化；
- 预览和检测操作不得产生正式业务数据；
- 遇到不确定需求时优先实现最小、可测试版本；
- 每次修改后说明改动文件、运行命令和测试结果；
- 每完成一个可运行阶段后提交 Git，但不要自动推送包含敏感信息的内容。

建议给 Codex 的第一条指令：

```text
请完整阅读项目根目录的 SPEC.md。当前只实现“阶段一：项目骨架和数据库”，不要提前实现后续阶段。完成后运行测试和静态检查，并汇报：修改了哪些文件、如何运行、测试结果、尚未实现的内容。确认 main 分支保持可运行后再提交 Git。
```
