# 正式信息源体系

## 阶段八 B 来源边界

正式来源清单不再散落于 seed 和 UI；以 [source-catalog.md](source-catalog.md) 为准。OpenAI RSS、Google Blog RSS、Qwen-Agent 旧 Releases 和百度智能云客户案例已退休，原因是本产品聚焦国内权威来源、稳定语义及可验收质量；百度智能云新闻继续保留。通用 `RSSCollector`、`GitHubReleaseCollector` 和 Fetcher 没有删除，GitHub Release 仍是非默认备用能力。

业务数据删除不放在 Alembic：Schema migration 应可重复、可回滚，不能在升级时不可逆删除用户收藏、人工分类或历史 Item。使用备份门控的 `sources purge-retired`，且只在正式数据库副本执行确认。

新角色包括 official_product/policy/industry、opportunity_and_award_hub、official_case_hub、report_hub、media_discovery 与 fallback；规则和完整目录见来源目录文档。

本文记录阶段八 A 的首批正式来源。最近一次人工可访问性验证日期为 **2026-07-19**。
正式来源配置位于 `app/config/preset_sources.yaml`，通过 `sources seed-formal` 命令或来源页按钮
幂等导入；URL 已存在时不覆盖名称、启停状态或用户修改。唯一兼容提升是阶段七原始 AIIA
受管预设：仅当名称、采集配置、来源属性和新增准入字段都仍与旧版精确一致时，seed 才将其提升
为当前正式配置，同时原样保留 enabled；任一字段被用户修改就报告 conflict，不做覆盖。

## 首批正式来源

| 来源 | URL | 等级 / 覆盖类别 | Collector | 链接质量与外部跳转 | 选择理由与已知限制 |
|---|---|---|---|---|---|
| 国家数据局政策发布 | https://www.nda.gov.cn/sjj/zwgk/zcfb/list/index_pc_1.html | government；政策行业 | `html_list` selector | 官网详情链接、无登录、无外跳 | 国家数据主管部门政策原文，权威性最高；栏目含非 AI 数据政策，需 include terms 收窄。 |
| 国家网信办网信发布 | https://www.cac.gov.cn/wxzw/wxfb/A093702index_1.htm | government；政策行业 | `html_list` selector | 官网详情链接、无登录、无外跳 | 覆盖生成式人工智能备案、算法与网信政策；栏目也有综合发布内容。 |
| 百度智能云新闻 | https://cloud.baidu.com/news/news | official_company；模型、智能体产品 | `html_list` link-filter | `/news/news_*` 官方详情链接 | 百度、文心和千帆的官方产品动态；页面为 SSR，但样式类名不稳定，因此只信任稳定 URL 形态。 |
| 百度智能云客户案例 | https://cloud.baidu.com/case/index.html | official_company；企业案例 | `html_list` link-filter | `/customer/case/` 官方详情链接 | 官方客户案例提供实施主体与业务结果；条目多且部分较旧，依靠时间筛选与准入分数控制。 |
| 中国互联网协会通知公告 | https://www.isc.org.cn/category/7330.html | association；征集、名单、政策 | `html_list` selector | 协会官网详情链接 | 稳定覆盖案例征集、申报与公布；栏目混有培训、会议和会员内容，必须经过排除规则。 |
| AIIA 人工智能产业发展联盟 | https://www.aiiaorg.cn/ | association；征集、名单、政策 | `html_list` selector + 内嵌链接 | 官网列表可信；允许跳转 CAICT/微信公众号 | 覆盖标准、征集和优秀案例。部分正文只能外跳；不抓取登录后正文，不伪造摘要，只保留公开稳定链接。 |
| OpenAI News RSS | https://openai.com/news/rss.xml | official_company；模型、智能体、企业案例 | `rss` | 官方 RSS 直达原文 | 稳定、结构化、持续更新，覆盖国际重要模型和产品发布；英文为主，以发布和重大升级信号准入。 |

首批共 7 个来源，没有为数量加入聚合站、普通媒体或高维护成本站点。所有来源均为
`source_kind=formal`、`audience=leadership`、首页和正式导出可见；具体 category scope、
include/exclude terms 与最低分数由 seed 显式给出。

## 候选但未接入

- 智谱 AI 新品发布页：官方且可访问，但多条发布共用一个页面、详情只有页面 fragment，现有
  canonical URL 语义会把它们合并；本阶段不引入站点专用拆分与虚拟 URL。
- Qwen 官方博客：当前列表依赖客户端 JavaScript/CSR，服务端 HTML 不能稳定得到条目和原文链接。
- DeepSeek API 更新日志：官方但多次更新共用单页，缺少稳定的逐条详情 URL。
- 普通 GitHub Releases：技术维护内容比例过高，并且通常存在质量更高的官网新闻或产品更新页。

这些候选不会在普通测试中访问，也不会伪造成已验证来源。若未来站点提供稳定 RSS/API 或逐条
详情链接，可重新评估；需要专用 Collector 时必须单独实现、注册和测试。

## GitHub 的边界

GitHub Releases 不是常规正式业务来源。`Qwen-Agent Releases` 已从默认 seed 删除，新数据库
不会创建它。迁移对已有 Qwen-Agent 来源执行安全兼容：保留全部历史 item、收藏和人工分类，
仅将来源 disabled、设为 fallback，并关闭首页/正式导出可见性。用户在首页显式选择“全部来源”、
“备用技术来源”或“已停用来源历史”后仍可查阅。

`GitHubReleaseCollector` 继续保留为备用采集能力，这不代表 GitHub Releases 是正式来源。
人工添加 GitHub 来源默认 `source_kind=fallback`、首页/导出隐藏且不允许技术更新。只有人工明确
设置 `allow_technical_updates=true` 后，正式大版本才可能通过准入；patch、普通修复、依赖升级、
预发布和无业务说明的维护日志仍会被拒绝。

## 外部页面与微信公众号

AIIA 是首批来源中唯一明确允许外部跳转的来源，允许域限于配置中的联盟官网、CAICT AI Hub
和微信公众号。微信公众号登录页、空白页和导航页不视为正文；系统不绕过登录、验证码或私有接口。
当前 Collector 只使用官网列表标题、日期和官方公开链接，不会因正文不可达而生成摘要。
