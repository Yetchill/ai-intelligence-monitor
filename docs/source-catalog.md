# 来源目录

`app/config/source_catalog.yaml` 是来源登记的唯一受管目录。Schema 拒绝未知字段、重复键、重复 slug、重复规范 URL、非法枚举和未校验的 `allowed_primary_types`。`implementation_status` 描述技术适配情况，不能替代 `lifecycle_state`。

## 同步与查询

```bash
uv run python -m app.cli sources sync-catalog
uv run python -m app.cli sources catalog
uv run python -m app.cli sources catalog --state candidate
```

同步会把 active、candidate 和 paused 全部写入数据库及来源管理页。它不创建退役来源，不覆盖用户修改，不重新启用 paused；受管字段发生冲突时报告 conflict。只有完全符合旧预设的 NDA、CAC 和 AIIA 记录才允许安全迁移到稳定 slug。

当前目录共 28 条：11 active、17 candidate、0 paused。数量是目录基线；用户暂停或人工激活后，数据库运行状态可以不同。Feed/RSSHub/sitemap/公开数据优先级与逐来源证据见 [`source-acquisition-review.md`](source-acquisition-review.md)。

## 当前清单

| slug | 来源 | 角色 | crawl mode | 初始状态 | 技术状态/原因 |
|---|---|---|---|---|---|
| nda-news | 国家数据局新闻动态 | official_industry | html_list | active | ready；阶段八 A selector 已验证 |
| cac-policy-regulations | 国家网信办政策法规 | official_policy | html_list | active | ready；服务端列表已验证 |
| isc-notices | 中国互联网协会通知公告 | opportunity_and_award_hub | html_list | active | ready；服务端列表已验证 |
| caict-aihub-docs | 鲸智社区文档中心 | report_hub | document_hub | candidate | needs_custom_collector；需适配附件与详情关系 |
| baidu-cloud-news | 百度智能云新闻 | official_product | html_list | active | ready；稳定详情 URL 过滤已验证 |
| deepseek-api-updates | DeepSeek API 更新日志 | official_product | single_page_changelog | active | ready；18 条真实 preview 三项有效率 100% |
| zhipu-research | 智谱研究与模型发布 | official_product | html_list | active | ready；公开内嵌 ID 与列表 preview 已验证 |
| baidu-qianfan-model-updates | 百度千帆模型更新记录 | official_product | single_page_changelog | active | ready；表格章节 preview 已验证 |
| qwen-official-blog | Qwen 官方博客 | official_product | api | candidate | needs_custom_collector；公开 JSON 可用但单响应约 4 MB，需有界 adapter |
| minimax-news | MiniMax 新闻资讯 | official_product | html_list | candidate | research_needed；需验收列表并强过滤宣传稿 |
| kimi-platform-changelog | Kimi 开放平台更新日志 | official_product | single_page_changelog | active | ready；8 条真实 preview 三项有效率 100% |
| tencent-hunyuan-product-updates | 腾讯混元产品动态 | official_product | single_page_changelog | candidate | research_needed；需验收文档分段 |
| tencent-hunyuan-product-announcements | 腾讯混元产品公告 | official_product | single_page_changelog | candidate | research_needed；需验收文档分段 |
| volcengine-ark-product-updates | 火山方舟产品更新 | official_product | single_page_changelog | candidate | blocked_by_javascript；未找到稳定公开数据 |
| volcengine-ark-model-releases | 火山方舟模型发布 | official_product | single_page_changelog | candidate | blocked_by_javascript；未找到稳定公开数据 |
| volcengine-ark-model-retirements | 火山方舟模型下线 | official_product | single_page_changelog | candidate | blocked_by_javascript；未找到稳定公开数据 |
| caict-special-reports | 中国信通院专题报告 | report_hub | document_hub | candidate | needs_custom_collector；需适配报告、详情及附件 |
| caict-aihub-cases | 鲸智社区案例展示 | official_case_hub | case_hub | candidate | needs_custom_collector；需抓详情并评估完整度 |
| caict-aiia-agent-working-group | AIIA 智能体工作组 | opportunity_and_award_hub | custom | candidate | needs_custom_collector；需专用解析 |
| miit-manufacturing-digital-platform | 制造业数字化转型平台 | official_case_hub | case_hub | candidate | blocked_by_javascript；尚无稳定公开接口 |
| mot-science-technology | 交通运输部科技司 | official_industry | html_list | candidate | research_needed；需验收栏目并限制 AI 范围 |
| xinhua-tech | 新华科技 | media_discovery | html_list | candidate | research_needed；需验收标题、日期和详情链接 |
| cls-ai-subject | 财联社人工智能专题 | media_discovery | api | active | ready；公开内嵌 JSON adapter，20 条真实 preview 三项有效率 100% |
| infoq-ai-llm | InfoQ AI 与大模型 | media_discovery | api | candidate | needs_custom_collector；公开 topic/article API 可用，待独立 adapter |
| zhidx-news | 智东西快讯 | media_discovery | html_list | candidate | research_needed；已采用重定向后的规范 URL |
| qbitai | 量子位 | media_discovery | rss | active | ready；官方资讯 Feed，10 条真实 preview 三项有效率 100% |
| jiqizhixin-dailies | 机器之心最新资讯 | media_discovery | html_list | candidate | research_needed；免费 RSS 当前需申请、登录和验证码 |
| 36kr-newsflashes | 36 氪快讯 | media_discovery | html_list | active | ready；相对日期和市场噪声过滤 preview 已验证 |

媒体技术上可用后允许 active，但仍固定 `always_review`、默认不进首页和正式导出。RSSHub 仅保留 `crawl_mode=rsshub` 作为未来自建适配器；本阶段不部署 Node.js、Docker 或公共 RSSHub 依赖。

## 2026-07-20 真实网络验收

network marker 共 10 项通过。限定来源的当前真实 preview：DeepSeek 18 条、Kimi 8 条、量子位 10 条、财联社 20 条，四者标题、日期、链接有效率均为 100%，重复率均为 0%。量子位和财联社仍全部进入 pending 媒体线索；财联社传闻条目被标记为 `rumor_or_prediction`。

机器之心 `/dailies`、`/articles` 和 `/rss` 当前均进入数据服务引导，公开脚本显示开通涉及创建用户、登录、验证码与订阅流程；本项目没有执行这些有状态操作，来源保持 candidate。其余候选的 Feed/RSSHub/sitemap/公开接口证据见 [`source-acquisition-review.md`](source-acquisition-review.md)。

## 新增来源

先新增严格目录项和角色规则，再运行同步、无落库 preview 与测试。能稳定抓取且达到激活门槛时设 active；需要大型适配、JavaScript、登录、验证码或无稳定链接时保留 candidate，并填写具体原因与建议下一步。
