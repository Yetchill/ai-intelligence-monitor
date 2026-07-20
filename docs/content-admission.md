# 内容准入策略

## Basic admission 与 taxonomy v2

原 `ContentAdmissionPolicy` 名称仅保留兼容 alias；职责实体为 `BasicAdmissionPolicy`。它不决定 primary type，也不按 `allowed_primary_types` 在分类前做循环判断。普通会议、演讲、参展、招聘、培训、促销、登录/导航、无实质短内容及来源 include/exclude 在这里处理。

分类、可信和发布分别由独立服务处理，详见 [taxonomy-v2.md](taxonomy-v2.md) 与 [source-review.md](source-review.md)。角色包采用不同规则，官方权威不等于所有栏目内容自动通过；媒体只提供线索。

## 所在层级与流程

`ContentAdmissionPolicy` 位于 application service 层，领域结果位于 `app/domain/admission.py`。
通过准入并成功进入持久化阶段的资讯会设置 `admission_accepted=true`。新增 migration 对历史资讯
安全回填 false：历史数据不会删除，仍可在“全部来源”或相应历史范围查看，但不会仅因旧来源被
提升为 formal 就绕过准入进入默认首页或正式导出；再次抓取并实际通过准入后才置 true。
调用顺序为：

`Collector -> normalize_collected_item -> ContentAdmissionPolicy -> Classifier -> persistence`

准入不决定业务分类，分类器也不决定内容是否进入正式信息流。`UpdatePipeline` 只负责编排，
没有站点特例；Collector、Repository、Web 路由和分类器内部均不包含准入规则。

## 决策结构

- `accepted`：是否允许进入分类和持久化阶段；
- `reason`：本次决策的主稳定 rule id，例如 `content.recruitment`、
  `source.exclude_term` 或 `quality.threshold_met`；
- `matched_rules`：结构化 `AdmissionRuleMatch` 元组，每项包含 `rule_id`、`effect`、`field`、
  可选 `value` 和 `score_delta`，可用于测试、日志与后续审计；
- `quality_score`：0 到 100 的整数。硬拒绝为 0；其余由基础分、来源权威度、正文/日期完整度、
  AI 相关性、正式发布/政策/征集/名单/落地信号和来源 include term 累加后截断。

来源的 `minimum_quality_score` 是准入阈值。高分表示“更可能适合领导信息流”，不是分类概率，
也不替代人工判断。

## 全局规则

硬拒绝优先于评分。默认拒绝招聘、培训招生、证书推广、会员招募/服务、促销、招商/售票、
会议日程、嘉宾介绍、活动预热/回顾、领导参观、无实质成果的签约、登录/导航/联系页、空标题、
非法链接、受限外部跳转和无实质信息的短标题。

正向信号包括重大模型发布或升级、智能体产品/平台发布、政策/标准、成果征集和各类申报、
优秀案例与名单、带明确结果的企业落地。准入后才调用现有规则分类器。

## 来源级规则与验证

`Source` 的 typed metadata 包括 kind、tier、audience、首页/导出可见性和最低质量分；
`content_scope`、`include_terms`、`exclude_terms` 是经过验证的字符串列表。组合顺序为：

1. 验证配置类型、枚举范围、分数边界及 include/exclude 冲突；异常时
   `source.configuration_invalid` 安全拒绝；
2. 检查结构、外部链接和全局硬拒绝；
3. 来源 `exclude_terms` 命中立即拒绝；
4. 来源配置 include terms 时，至少命中一项，否则拒绝；
5. 计算质量分并检查检测到的业务范围是否落入 `content_scope`；
6. 检查 title-only、最低分数，最后接受。

排除规则优先于包含规则。列表不得包含空值、超长词或未知 category；最低分数必须有限且位于
0..100。新增规则应使用稳定 rule id、独立测试和清晰 effect，不应只返回描述性文本。

## GitHub Release 规则

GitHub 来源首先经过专用的通用准入规则，而不是 Collector 特例。pre-release、nightly、alpha、
beta、rc、patch/非重大 semver、bug fix、依赖升级、CI/构建/文档维护均拒绝。来源未人工启用
`allow_technical_updates` 时全部技术发布拒绝。只有可证明的 `vN.0.0` 正式大版本、人工允许且
达到来源最低分，才可接受。

## 拒绝项存储与统计

阶段八 A 采用方案 A：新抓取的 rejected 内容不写入 `IntelligenceItem`。原因是现有 item 表
承载首页、导出、收藏和人工分类；不污染该表能以最小改动保护既有业务语义。每个 `CrawlRun`
持久化 fetched/discovered、normalized、accepted、rejected、classified、inserted/new、updated、
duplicate、failed 以及 `rejection_reason_counts`。拒绝项不计 new，不触发新增资讯统计。

迁移不会删除任何历史 item。历史 test/fallback 来源依靠来源可见性从默认首页和正式导出排除；
用户显式选择范围后仍可查看。

## Preview、手动和调度一致性

`SourcePreviewService` 与 `UpdatePipeline` 都调用同一个 `ContentAdmissionPolicy`。网页手动、CLI
手动和定时任务继续共享同一个 `UpdatePipeline` factory，因此没有第二套准入逻辑。预览不落库，
会把主拒绝原因计数加入错误提示；正式运行将同类计数写入 CrawlRun。

## 排查误拒绝和误放行

先查看更新记录中的主 `reason=count`，再使用固定 `CollectedItem` 和对应 Source 配置直接调用
policy，检查 `matched_rules` 的字段、命中值和分数贡献。crawler 日志用 canonical URL 的短
SHA-256 `item_ref` 关联每条 accepted/rejected 决策，不记录标题、URL 查询串或正文。误拒绝优先调整来源 include/exclude、
content scope 或合理阈值；全局规则变更必须补正反例测试。误放行应增加窄而稳定的硬规则，避免
把站点名称或选择器写进 policy。日志只记录来源 id、item ref、rule id、分数和匹配 rule id。
