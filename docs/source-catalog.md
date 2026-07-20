# 来源目录

`app/config/source_catalog.yaml` 是来源登记的唯一受管目录。Schema 拒绝未知字段、重复键、重复 slug、重复规范 URL、非法枚举和未校验的 `allowed_primary_types`。`implementation_status` 描述技术适配情况，不能替代 `lifecycle_state`。

## 同步与查询

```bash
uv run python -m app.cli sources sync-catalog
uv run python -m app.cli sources catalog
uv run python -m app.cli sources catalog --state candidate
```

同步会把 active、candidate 和 paused 全部写入数据库及来源管理页。它不创建退役来源，不覆盖用户修改，不重新启用 paused；受管字段发生冲突时报告 conflict。只有完全符合旧预设的 NDA、CAC 和 AIIA 记录才允许安全迁移到稳定 slug。

当前目录共 28 条：4 active、24 candidate、0 paused。数量是目录基线；用户暂停或人工激活后，数据库运行状态可以不同。

## 当前清单

| slug | 来源 | 角色 | crawl mode | 初始状态 | 技术状态/原因 |
|---|---|---|---|---|---|
| nda-news | 国家数据局新闻动态 | official_industry | html_list | active | ready；阶段八 A selector 已验证 |
| cac-policy-regulations | 国家网信办政策法规 | official_policy | html_list | active | ready；服务端列表已验证 |
| isc-notices | 中国互联网协会通知公告 | opportunity_and_award_hub | html_list | active | ready；服务端列表已验证 |
| caict-aihub-docs | 鲸智社区文档中心 | report_hub | document_hub | candidate | needs_custom_collector；需适配附件与详情关系 |
| baidu-cloud-news | 百度智能云新闻 | official_product | html_list | active | ready；稳定详情 URL 过滤已验证 |
| deepseek-api-updates | DeepSeek API 更新日志 | official_product | single_page_changelog | candidate | research_needed；需验收分段 selector、日期和 fingerprint |
| zhipu-research | 智谱研究与模型发布 | official_product | html_list | candidate | research_needed；需确认静态数据与详情链接 |
| baidu-qianfan-model-updates | 百度千帆模型更新记录 | official_product | single_page_changelog | candidate | research_needed；需验收服务端分段 |
| qwen-official-blog | Qwen 官方博客 | official_product | html_list | candidate | blocked_by_javascript；服务端无稳定条目 |
| minimax-news | MiniMax 新闻资讯 | official_product | html_list | candidate | research_needed；需验收列表并强过滤宣传稿 |
| kimi-platform-changelog | Kimi 开放平台更新日志 | official_product | single_page_changelog | candidate | research_needed；需验收静态分段和日期 |
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
| cls-ai-subject | 财联社人工智能专题 | media_discovery | html_list | candidate | research_needed；需排查登录/验证码与稳定链接 |
| infoq-ai-llm | InfoQ AI 与大模型 | media_discovery | html_list | candidate | research_needed；需确认服务端列表 |
| zhidx-news | 智东西快讯 | media_discovery | html_list | candidate | research_needed；已采用重定向后的规范 URL |
| qbitai | 量子位 | media_discovery | html_list | candidate | research_needed；需控制导航和推荐位误抓 |
| jiqizhixin-dailies | 机器之心最新资讯 | media_discovery | html_list | candidate | research_needed；需确认服务端渲染与日期 |
| 36kr-newsflashes | 36 氪快讯 | media_discovery | html_list | candidate | research_needed；需稳定快讯数据并过滤市场内容 |

媒体技术上可用后允许 active，但仍固定 `always_review`、默认不进首页和正式导出。RSSHub 仅保留 `crawl_mode=rsshub` 作为未来自建适配器；本阶段不部署 Node.js、Docker 或公共 RSSHub 依赖。

## 2026-07-20 真实网络验收

四个初始 active 均通过只读真实抓取：NDA 25 条、CAC 20 条、ISC 20 条、百度新闻 10 条，标题与详情链接有效。候选探测不写数据库。

第一批完整 preview 结果：

| 来源 | HTTP/抽取 | 日期/链接 | 结论 |
|---|---|---|---|
| DeepSeek | 200，20 条 | 65% / 100% | “时间”被拆成独立条目，保持 candidate |
| 百度千帆 | 200，0 条 | 0% / 0% | 通用 selector 无结果，保持 candidate |
| Kimi | 200，20 条 | 100% / 100% | 标题全为日期，需合并正文标题 |
| 腾讯混元动态 | 200，0 条 | 0% / 0% | 通用 selector 无结果 |
| 腾讯混元公告 | 200，0 条 | 0% / 0% | 通用 selector 无结果 |
| MiniMax | 200，2 条 | 0% / 100% | 两条均 unclassified，需专用适配 |
| 智东西 | 200，2 条 | 0% / 100% | 抽到旧话题/导航，误抓严重 |
| 财联社 AI | 200，10 条 | 0% / 100% | 可产生 pending/media_only 线索，但日期门槛未通过 |

因此本轮没有为了提高 active 数量而放宽门槛。第二批可访问性探测显示：智谱、InfoQ HTTP 200 且标题/日期/链接可见；机器之心和 36 氪缺日期；Qwen、火山方舟及 CAICT 多入口表现为 JavaScript 主导；CAICT 报告为 HTTP 412；工信部平台与量子位拒绝公开访问；交通运输部发生 HTTPS 降级；新华入口未通过安全访问。以上均继续 candidate，原因已经写回 catalog。

## 新增来源

先新增严格目录项和角色规则，再运行同步、无落库 preview 与测试。能稳定抓取且达到激活门槛时设 active；需要大型适配、JavaScript、登录、验证码或无稳定链接时保留 candidate，并填写具体原因与建议下一步。
