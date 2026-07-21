# 阶段九来源整合验证报告

**日期**: 2026-07-21
**分支**: feat/stage-9-source-integration
**报告 commit**: 5c405bf（本报告将在此基础上新增 commit）

---

## 1. 集成分支和最终 HEAD

- **分支**: `feat/stage-9-source-integration`
- **最新 HEAD**（撰文时）: `5c405bf5ff9e2fdf14b153f0a055b34ef72f9c4e`
- **起点**（阶段九开始前）: `86b3cec`
- **commit 序列**（`86b3cec..HEAD`）:

```
5c405bf chore: activate validated sources
f1064c6 feat: add domestic media sources
6d9162f feat(classification): improve model/agent/policy/enterprise keyword coverage and add regression tests
bc41030 docs: add W5 first-round classification post-evaluation report
8c2c8a3 chore: remove abandoned sources
a7479c2 fix: remove stray registry lines from W2 conflict resolution
786d992 fix: SafeHttpFetcher.post must not follow redirects (SSRF bypass)
4de79f5 feat: add PublicJsonCollector and InfoQAICollector for qwen-official-blog and infoq-ai-llm
4c3260c feat: adapt minimax-news and xinhua-tech sources
5ed57bf fix: adapt tencent-hunyuan-product-updates and announcements for Slate editor table extraction
```

### 最终 Commit 统计

| 类别 | 数量 |
|---|---|
| 总 commit 数 | 10 |
| Source collector 适配 | 3（5ed57bf, 4c3260c, 4de79f5） |
| SSRF 安全修复 | 1（786d992） |
| 冲突解决 | 1（a7479c2） |
| 来源删除 | 1（8c2c8a3） |
| 来源新增 | 1（f1064c6） |
| 分类规则评测 | 1（bc41030） |
| 分类规则升级 | 1（6d9162f） |
| 来源激活 | 1（5c405bf） |

---

## 2. 已整合的第一轮 commit（W1–W3 + W5）

各 commit 已在 `feat/stage-9-source-integration` 分支上通过 `chore: remove abandoned sources` 和 `chore: activate validated sources` 完成整合，包括生命周期固化、测试同步、目录文案更新。

### W3 混元产品动态与公告 — 5ed57bf

- 适配 `tencent-hunyuan-product-updates` 和 `tencent-hunyuan-product-announcements` 两个基于 Slate 编辑器渲染的数据表
- `single_page_changelog` collector 配置 `entry_title_cells`、`entry_date_cell` 等 Slate 表格专用字段
- 本轮 real preview 验证通过（20/20 和 2/2，三项有效率 100%），已激活

### W1 minimax/xinhua — 4c3260c

- **minimax-news**: 专用 `MiniMaxNewsCollector` 解析公开 `/api/news` JSON，12/12 全部 accepted
- **xinhua-tech**: HTML selector `filter_selector_items` + 强 include/exclude 过滤非 AI 内容，extracted=8 accepted=7
- 两来源本轮 real preview 通过，已激活

### W2 qwen/infoq — 4de79f5 + 786d992

- **4de79f5**: 新增 `PublicJsonCollector`（通用公开 JSON adapter，最多 50 条/6 MB）和 `InfoQAICollector`（专用 InfoQ POST API adapter），注册进 `CollectorRegistry`
- **786d992**: SSRF 修复 — `SafeHttpFetcher.post` 禁止跟随重定向，防止被攻击者控制的 URL 利用 POST 请求跳转到内网

### W5 分类规则升级 — 6d9162f

- 基于 103 条真实样本评测（详见第 16 节），准确率从 43.69% → 80.58%（+36.89pp）
- 新增 fixtures 覆盖 71 个固定标注 case + 124 个 adversarial case
- 无新回归，1 个 fixture 失败为预期行为变化（歧义样本变得清晰）

---

## 3. 未整合的 commit 及原因

W4 分支 `agent/stage9-w4-jqxhh-yanbaohu` 上有两个 commit：

| commit | 内容 | 未整合原因 |
|---|---|---|
| ce972ff | 机器之心调查文档 | 用户已明确删除 `jiqizhixin-dailies` 来源（`8c2c8a3`），该文档失去引用价值 |
| 78b44b5 | 越界修改新华科技（xinhua-tech） | 修改了不属于 W4 范围的新华来源 selector，已在 `4c3260c` 中通过正确方式修复，此处修改为冗余/越界 |

结论：W4 分支无整合价值，最终跳过。

---

## 4. 删除的 6 个来源（commit: 8c2c8a3）

| slug | 名称 | 初始状态 | 技术状态 | 删除原因 |
|---|---|---|---|---|
| volcengine-ark-product-updates | 火山方舟产品更新 | candidate | blocked_by_javascript | JavaScript 壳，无公开接口 |
| volcengine-ark-model-releases | 火山方舟模型发布 | candidate | blocked_by_javascript | 同上 |
| volcengine-ark-model-retirements | 火山方舟模型下线 | candidate | blocked_by_javascript | 同上 |
| miit-manufacturing-digital-platform | 制造业数字化转型平台 | candidate | blocked_by_javascript | SPA 壳，无稳定接口 |
| mot-science-technology | 交通运输部科技司 | candidate | research_needed | HTTPS 降级，站点异常 |
| jiqizhixin-dailies | 机器之心最新资讯 | candidate | research_needed | RSS 需申请/登录/验证码 |

全部引用（`source_catalog.yaml`、`docs/source-catalog.md`、`docs/source-acquisition-review.md`、`sources.html` 模板）均已同步清理，无遗漏。

---

## 5. 新增的 4 个来源（commit: f1064c6）

| slug | 名称 | URL | source_role | crawl_mode | collector_name |
|---|---|---|---|---|---|
| leiphone-ai | 雷锋网 AI | https://www.leiphone.com/feed | media_discovery | rss | rss |
| geekpark-ai | 极客公园 | https://www.geekpark.net | media_discovery | custom | custom |
| ithome-ai | IT之家 AI | https://www.ithome.com/list/ai.html | media_discovery | html_list | html_list |
| huxiu-ai | 虎嗅 AI | https://www.huxiu.com/article/ | media_discovery | custom | huxiu |

全部为 `review_policy: always_review`、`homepage_visible: false`、`export_visible: false`。

---

## 6. 最终 26 个来源清单

| # | slug | 名称 | 角色 | mode |
|---|---|---|---|---|
| 1 | nda-news | 国家数据局新闻动态 | official_industry | html_list |
| 2 | cac-policy-regulations | 国家网信办政策法规 | official_policy | html_list |
| 3 | isc-notices | 中国互联网协会通知公告 | opportunity_and_award_hub | html_list |
| 4 | caict-aihub-docs | 鲸智社区文档中心 | report_hub | document_hub |
| 5 | baidu-cloud-news | 百度智能云新闻 | official_product | html_list |
| 6 | deepseek-api-updates | DeepSeek API 更新日志 | official_product | single_page_changelog |
| 7 | zhipu-research | 智谱研究与模型发布 | official_product | html_list |
| 8 | baidu-qianfan-model-updates | 百度千帆模型更新记录 | official_product | single_page_changelog |
| 9 | qwen-official-blog | Qwen 官方博客 | official_product | api |
| 10 | minimax-news | MiniMax 新闻资讯 | official_product | api |
| 11 | kimi-platform-changelog | Kimi 开放平台更新日志 | official_product | single_page_changelog |
| 12 | tencent-hunyuan-product-updates | 腾讯混元产品动态 | official_product | single_page_changelog |
| 13 | tencent-hunyuan-product-announcements | 腾讯混元产品公告 | official_product | single_page_changelog |
| 14 | caict-special-reports | 中国信通院专题报告 | report_hub | document_hub |
| 15 | caict-aihub-cases | 鲸智社区案例展示 | official_case_hub | case_hub |
| 16 | caict-aiia-agent-working-group | AIIA 智能体工作组 | opportunity_and_award_hub | custom |
| 17 | xinhua-tech | 新华科技 | media_discovery | html_list |
| 18 | cls-ai-subject | 财联社人工智能专题 | media_discovery | api |
| 19 | infoq-ai-llm | InfoQ AI 与大模型 | media_discovery | api |
| 20 | zhidx-news | 智东西快讯 | media_discovery | html_list |
| 21 | qbitai | 量子位 | media_discovery | rss |
| 22 | 36kr-newsflashes | 36 氪快讯 | media_discovery | html_list |
| 23 | leiphone-ai | 雷锋网 AI | media_discovery | rss |
| 24 | geekpark-ai | 极客公园 | media_discovery | custom |
| 25 | ithome-ai | IT之家 AI | media_discovery | html_list |
| 26 | huxiu-ai | 虎嗅 AI | media_discovery | custom |

---

## 7. 各来源 lifecycle

### Active（18 个）

**原有 active（11 个）**: nda-news, cac-policy-regulations, isc-notices, baidu-cloud-news, deepseek-api-updates, zhipu-research, baidu-qianfan-model-updates, kimi-platform-changelog, cls-ai-subject, qbitai, 36kr-newsflashes

**第一轮激活（6 个）**: qwen-official-blog, minimax-news, tencent-hunyuan-product-updates, tencent-hunyuan-product-announcements, xinhua-tech, infoq-ai-llm

**新增后激活（1 个）**: ithome-ai

### Candidate（8 个）

leiphone-ai, huxiu-ai, geekpark-ai, caict-aihub-docs, caict-special-reports, caict-aihub-cases, caict-aiia-agent-working-group, zhidx-news

其中 leiphone-ai 和 huxiu-ai 虽然 `implementation_status: ready` 且 preview 可用，但 accepted 均不足 5 条（分别为 2 和 2），未达到激活门槛。geekpark-ai 因 WAF 阻断，`implementation_status: blocked_by_javascript`。其余 5 个仍为 `needs_custom_collector` 或 `research_needed`。

---

## 8. 完整测试结果

```
uv run pytest -q
510 passed, 10 deselected, 1 warning in 39.03s
```

- **510 passed**: 全部通过
- **10 deselected**: network marker 测试（需真实网络连接），正确跳过
- **0 failed**

---

## 9. Ruff 结果

```
uv run ruff check .
All checks passed!
```

---

## 10. Pyright 结果

```
uv run pyright
0 errors, 0 warnings, 0 informations
```

---

## 11. Alembic head

```
d4e5f6a7b8c9 — add source catalog lifecycle and taxonomy v2
```

单一 head，无分叉。迁移链完整：

```
db0caa03a995 → 8df43a9b1c2e → a51f8e8d29c4 → c94d2a1f7e3b → f2c7a93d1b44
  → 7a8b9c0d1e2f → b6f4e2d9a731 → d4e5f6a7b8c9
```

---

## 12. 每个正式来源的 preview 指标

所有数据来自 `docs/research/preview_results_stage9.txt`（`--no-persist`，临时库）。extracted=从来源抽取的原始条目数，accepted=通过 admission 准入的条目数，rejected=被拒绝数，failed=采集/解析失败数。

| slug | extracted | accepted | rejected | failed | title% | date% | link% | duplicate% |
|---|---|---|---|---|---|---|---|---|
| nda-news | 20 | 0 | 20 | 0 | 100% | 100% | 100% | 0% |
| cac-policy-regulations | 20 | 12 | 8 | 0 | 100% | 100% | 100% | 0% |
| isc-notices | 20 | 3 | 17 | 0 | 100% | 100% | 100% | 0% |
| baidu-cloud-news | 10 | 5 | 5 | 0 | 100% | **0%** | 100% | 0% |
| deepseek-api-updates | 18 | 18 | 0 | 0 | 100% | 100% | 100% | 0% |
| zhipu-research | 15 | 14 | 1 | 0 | 100% | 100% | 100% | 0% |
| baidu-qianfan-model-updates | 20 | 20 | 0 | 0 | 100% | 100% | 100% | 0% |
| qwen-official-blog | 20 | 20 | 0 | 0 | 100% | 100% | 100% | 0% |
| minimax-news | 12 | 12 | 0 | 0 | 100% | 100% | 100% | 0% |
| kimi-platform-changelog | 8 | 8 | 0 | 0 | 100% | 100% | 100% | 0% |
| tencent-hunyuan-product-updates | 20 | 20 | 0 | 0 | 100% | 100% | 100% | 0% |
| tencent-hunyuan-product-announcements | 2 | 2 | 0 | 0 | 100% | 100% | 100% | 0% |
| xinhua-tech | 8 | 7 | 1 | 0 | 100% | 100% | 100% | 0% |
| cls-ai-subject | 20 | 15 | 5 | 0 | 100% | 100% | 100% | 0% |
| infoq-ai-llm | 19 | 13 | 6 | 0 | 100% | 100% | 100% | 0% |
| qbitai | 10 | 7 | 3 | 0 | 100% | 100% | 100% | 0% |
| 36kr-newsflashes | 2 | 1 | 1 | 0 | 100% | 100% | 100% | 0% |
| ithome-ai | 9 | 6 | 3 | 0 | 100% | 100% | 100% | 0% |

### nda-news accepted=0 专项说明

nda-news extracted=20, accepted=0, rejected=20。rejection 分布：`source.exclude_term: 8`（座谈会/培训班触发）、`role.official_industry.ai_relevance_missing: 10`（新闻报道/数据治理通稿等非 AI 核心内容）、`content.ordinary_meeting: 2`（普通会议/论坛致辞）。

**这是准入规则正确行为的体现**，而非缺陷。国家数据局新闻动态包含大量培训、座谈会、地方动态和非 AI 通稿，`include_terms/exclude_terms` 配置与 `BasicAdmissionPolicy` 正确过滤，确保只进入真正与 AI/大模型/数据要素相关的内容。

### baidu-cloud-news valid_date=0% 说明

百度智能云新闻列表页标题与正文文本混排，date selector 抽取到混合文本而非纯日期。需后续修复 selector 或改用详情页日期字段。

---

## 13. 每个新增来源的 preview 指标

| slug | extracted | accepted | rejected | failed | lifecycle |
|---|---|---|---|---|---|
| leiphone-ai | 2 | 2 | 0 | 0 | candidate（accepted 不足 5） |
| geekpark-ai | 0 | 0 | 0 | 1 | candidate（WAF 阻断） |
| ithome-ai | 9 | 6 | 3 | 0 | **active** |
| huxiu-ai | 12 | 2 | 10 | 0 | candidate（accepted 不足 5） |

geekpark-ai 的 1 条 failed 原因：`no collector registered for 'custom'` — 无专用 Collector 注册，且 WAF 阻断所有已知 URL。leiphone-ai 和 huxiu-ai 的 collected 数足够但 accepted 数不足（需至少 5 条 accepted 才能激活），保持 candidate。

---

## 14. 真实抓取样例（每来源最多 5 条）

### nda-news（accepted=0，展示 rejected 样例）

| # | 标题 | 日期 | rejected 原因 |
|---|---|---|---|
| 1 | 全国数据资源开发利用培训班在大连成功举办 | 2026-07-17 | source.exclude_term |
| 2 | 国家数据局召开网络安全、数据安全研究机构和企业座谈会 | 2026-07-15 | source.exclude_term |
| 3 | 刘烈宏出席2026中国数字经济发展和治理学术年会并开展学术交流 | 2026-07-14 | role.ai_relevance_missing |

### cac-policy-regulations

| # | 标题 | 日期 | 分类 |
|---|---|---|---|
| 1 | 网络数据安全风险评估办法 | 2026-06-18 | policy_standard |
| 2 | 以"小快灵"立法规范人工智能拟人化互动服务 | 2026-06-03 | policy_standard |
| 3 | 一图读懂《智能体规范应用与创新发展实施意见》 | 2026-05-08 | policy_standard |
| 4 | 专家解读｜以风险评估为制度牵引 构建数据安全治理新格局 | 2026-06-18 | policy_standard |

### deepseek-api-updates

| # | 标题 | 日期 |
|---|---|---|
| 1 | DeepSeek-V4：DeepSeek API 已支持 V4-Pro 与 V4-Flash | 2026-04-24 |
| 2 | DeepSeek-V3.2：deepseek-chat 和 deepseek-reasoner 都已升级 | 2025-12-01 |
| 3 | DeepSeek-V3.1-Terminus：模型升级 | 2025-09-22 |
| 4 | API 上线硬盘缓存技术 | 2024-08-02 |

### baidu-qianfan-model-updates

| # | 标题 | 日期 |
|---|---|---|
| 1 | ERNIE 5.0 — 正式发布 | 2025-11-13 |
| 2 | DeepSeek-V4-Pro — 正式发布 | 2026-04-24 |
| 3 | GLM-5.2 — 正式发布 | 2026-06-17 |
| 4 | Kimi-K2.5 — 退役 | 2026-07-09 |
| 5 | MiniMax-M2.5 — 退役 | 2026-07-09 |

### qwen-official-blog

| # | 标题 | 日期 |
|---|---|---|
| 1 | Qwen3.6-Max-Preview：更强知识，更强编程，持续进化 | 2026-04-18 |
| 2 | Qwen3.6-Plus：走向现实世界智能体 | 2026-04-01 |
| 3 | Qwen3.6-35B-A3B：智能体编程利器，现已开源 | 2026-04-15 |
| 4 | Qwen3.5：迈向原生多模态智能体 | 2026-02-15 |
| 5 | Qwen-Image-2.0: 专业信息图，细腻真实感 | 2026-02-10 |

### minimax-news

| # | 标题 | 日期 |
|---|---|---|
| 1 | 华为云与MiniMax最新模型M3完成适配 | 2026-06-16 |
| 2 | Day0适配丨壁仞科技率先支持MiniMax M3大模型 | 2026-06-16 |
| 3 | 极速适配，生态共赢：昆仑芯高效支持MiniMax M3模型 | 2026-06-16 |
| 4 | 昇腾0Day支持MiniMaxM2.7，共同开启模型自我进化新范式 | 2026-04-11 |
| 5 | 开展"清朗·整治AI应用乱象"专项公告 | 2026-05-15 |

### tencent-hunyuan-product-updates

| # | 标题 | 日期 |
|---|---|---|
| 1 | Tencent HY 文生文旧版本模型下线 | 2026-06-22 |
| 2 | Tencent HY 2.0 Think 上线 | 2025-11-09 |
| 3 | Tencent HY 2.0 Instruct 上线 | 2025-11-11 |
| 4 | Tencent HY Vision 1.5 Instruct 上线 | 2025-12-17 |

### xinhua-tech

| # | 标题 | 日期 |
|---|---|---|
| 1 | 把算力中心搬上天 | 2026-07-21 |
| 2 | 推动人工智能嵌入日常生活 | 2026-07-21 |
| 3 | 拓宽新兴领域人工智能就业新空间 | 2026-07-21 |
| 4 | AI产业链携手推动词元降本增效 | 2026-07-20 |
| 5 | 中国企业发布全球最大规模的开源模型Kimi K3 | 2026-07-17 |

### infoq-ai-llm

| # | 标题 | 日期 |
|---|---|---|
| 1 | Hugging Face遭攻击后，只能靠GLM 5.2救场？ | 2026-07-21 |
| 2 | 微软跟进谷歌支持 Go 语言开发 AI 智能体 | 2026-07-21 |
| 3 | DoorDash 如何打造了一款不完全依赖 LLM 的 AI 购物助手 | 2026-07-21 |
| 4 | 国产GPU分水岭时刻：摩尔线程早已训练出了世界模型 | 2026-07-20 |
| 5 | 边端AI不只缺算力：安谋科技重做CPU、NPU、VPU与AI操作系统 | 2026-07-19 |

### ithome-ai

| # | 标题 | 日期 |
|---|---|---|
| 1 | 百时美施贵宝采购英伟达最新 Vera Rubin 架构计算系统 | 2026-07-21 |
| 2 | 淘宝天猫对"AI 批量套图"进行专项治理 | 2026-07-21 |
| 3 | 英伟达推出合成视频检测器 NIM：准确率可达 92% | 2026-07-21 |
| 4 | YouTube 明确打击 AI 垃圾内容，三类视频将不能变现 | 2026-07-21 |
| 5 | AI 浪潮推动全球半导体需求，韩国出口额同比增 62.9% | 2026-07-21 |

### leiphone-ai（candidate）

| # | 标题 | 日期 |
|---|---|---|
| 1 | 姚卯青、张正友、徐丹飞等七位大佬同席，这届 WAIC 把具身未来聊透了 | 2026-07-20 |
| 2 | SoulAgent亮相WAIC 2026：智能参会重塑前沿知识传播范式 | 2026-07-20 |

### huxiu-ai（candidate）

| # | 标题 | 日期 |
|---|---|---|
| 1 | AI产业链条上最大的"伪命题"：锁定万亿订单就能躺赚？ | 2026-07-21 |
| 2 | 在下一个模型发布之前 | 2026-07-21 |

---

## 15. 36kr 与国家数据局专项结果

### 36kr-newsflashes

此前阶段八中抽取 0 条（站点改版导致 selector 失效）。本轮恢复后：

- **extracted=2, accepted=1, rejected=1**
- Rejected 原因: `source.include_term_missing`（AI 关键词缺失）
- Accepted 条目: `"腾讯智慧零售、腾讯地图携手Chinagoods平台打造的'Chinagoods AI导航'上线"`（industry_signal）
- 时效性: 2026-07-21 当天数据
- 结论: 来源采集功能已恢复，但 36kr 快讯中 AI 相关内容占比较低

### nda-news

- **extracted=20, accepted=0, rejected=20**
- 全部 20 条被准入正确拒绝
- Rejection 分布:
  - `source.exclude_term`: 8 条（培训班、座谈会触发 exclude_terms）
  - `role.official_industry.ai_relevance_missing`: 10 条（非 AI 核心内容）
  - `content.ordinary_meeting`: 2 条（普通会议/论坛致辞）
- 结论: 准入规则正确运行。NDA 新闻流以培训/座谈会/非 AI 通稿为主，`include_terms/exclude_terms` 正确过滤

---

## 16. 分类修改前后同样本指标

基于 `docs/research/classification_post_evaluation.md`（W5 第一轮后评估）。

### 评测设置

- 样本集: 11 个稳定来源的 **103 条真实 accepted 样本**（同一样本集用于基线与 W5 评测）
- 规则基线: `app/config/classification_rules.yaml`（303 行）
- W5 规则: 来自 `agent/round1-classification-quality` 分支（343 行），已整合为 `6d9162f`

### 总体对比

| 指标 | 基线 | W5 | 变化 |
|---|---|---|---|
| 准确率 | 43.69% (45/103) | **80.58%** (83/103) | **+36.89pp** |
| 正确数 | 45 | 83 | +38 |
| 错误数 | 58 | 20 | -38 |
| Unclassified 率 | 64.1% (65/103) | 20.4% (21/103) | -44 |

### 各类别准确率

| 类别 | 基线 | W5 | 提升 |
|---|---|---|---|
| model_technology | 40.68% (24/59) | **91.53%** (54/59) | +50.85pp |
| agent_product | 10.00% (1/10) | 30.00% (3/10) | +20.00pp |
| enterprise_case | 33.33% (1/3) | 33.33% (1/3) | 持平 |
| solicitation | 100.00% (1/1) | 100.00% (1/1) | 持平 |
| policy_industry | 43.75% (7/16) | **81.25%** (13/16) | +37.50pp |
| unclassified | 78.57% (11/14) | 78.57% (11/14) | 持平 |

### 回归情况

**W5 规则未引入新回归错误。** 所有 20 条 W5 仍错误的样本在基线下也均错误。1 个 fixture 测试失败为非回归（歧义样本在 W5 规则下变得清晰）。

### 样本差异说明

当前评测样本 103 条 vs W5 报告中的 106 条存在时序差异（因 nda-news 样本缺失和部分来源采集数变化），但来源分布一致。

---

## 17. 尚存风险

### 已知缺陷

1. **baidu-cloud-news valid_date=0%**: 百度智能云新闻标题文本混入日期格式导致 date selector 抽取混合文本。需后续修复 selector 或改用详情页日期字段。
2. **geekpark-ai WAF 阻断**: 全站 403/404，`no collector registered for 'custom'`。当前无可合规采集通道，保持 candidate。
3. **leiphone-ai/huxiu-ai accepted 不足**: 分别仅 accepted=2 和 2，未达 5 条激活门槛，保持 candidate。两来源技术可用，仅受实时内容中 AI 占比限制。
4. **hunyuan 公告页仅 2 条**: `tencent-hunyuan-product-announcements` 的 extracted/accepted 均为 2，页面内容总量小，可能偶现 0 结果。
5. **评测样本与真实数据时序差异**: 103 条测评样本与第一轮 W5 报告的 106 条存在时序差异。后续评测应固化样本集（已通过 `eval_samples.yaml` 完成）。

### 长期关注项

- **Classifier agent_product 召回低（30%）**: Kimi API 功能更新、36kr 产品上线等标注为 agent_product 的样本多数被错分为 model_technology 或 unclassified。
- **GLM 子模型（OCR/TTS/ASR）**: 未被 model_technology 规则覆盖。
- **enterprise_case 召回不足（33%）**: 仅 1/3 正确，qbitai 的产业案例未被有效识别。

---

## 18. 用户可执行的真实测试命令序列

### 环境准备

```bash
# 同步 Python 依赖
uv sync

# 数据库迁移到最新版本
uv run alembic upgrade head

# 同步来源目录到数据库
uv run python -m app.cli sources sync-catalog
```

### 执行全量更新

```bash
# 对全部 active 来源执行一轮完整采集管线
uv run python -m app.cli update
```

### 预览单个来源

```bash
# 可选，预览某个来源的最新内容（不持久化）
uv run python -m app.cli sources preview <slug> --max-items 20 --no-persist
```

替换 `<slug>` 为实际来源 slug（如 `qwen-official-blog`、`ithome-ai`、`xinhua-tech`）。

### 查看运行记录

```bash
# 查看最近采集运行记录
uv run python -m app.cli runs --limit 5
```

### 启动 Web UI

```bash
uv run uvicorn app.web.app:app --host 127.0.0.1 --port 8000
```

或:

```bash
uv run python -m app.web
```

建议先用 `uv run uvicorn` 方式，支持 reload 热更新。

### 运行完整测试套件

```bash
uv run pytest -q                    # 全部非网络测试
uv run pytest -m network -s -q      # 网络测试（需真实网络）
uv run ruff check .                 # 代码风格检查
uv run pyright                      # 类型检查
```
