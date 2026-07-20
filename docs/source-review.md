# 来源与内容审核

处理链为：

`Collector -> normalize -> BasicAdmissionPolicy -> ClassificationService -> VerificationService -> PublicationPolicy -> persistence`

BasicAdmission 负责结构、URL、登录/导航、招聘培训促销、普通会议、来源 include/exclude 与基础质量，不决定 primary type。Classification 决定 taxonomy v2 和机会字段，不决定发布。Verification 根据来源角色、官方链接及传闻词确定可信和默认审核状态，不持久化。PublicationPolicy 在分类之后检查 lifecycle、角色、allowed types、可信/审核状态和首页/导出开关。

## 媒体发现

media_discovery 默认生成 `industry_signal + media_only + pending`，保留媒体链接为 `discovery_url`。找到并验证 HTTP(S) 官方原文后可设 `official_linked` 和 `official_url`；实际发布主体使用 `origin_publisher`，不得把转载域名伪装为官方主体。含“据悉、消息称、知情人士、或将、预计、传闻、可能推出、计划发布、市场消息”时为 `rumor_or_prediction`，即使人工保留也不进领导首页和正式导出。

人工审核通过设 approved，拒绝设 rejected。Web 人工修改写入 `item_review_events`，记录时间、操作来源及前后 JSON；人工 verification/review 锁不会被后续更新静默覆盖。本阶段不引入用户系统，actor 使用系统操作来源语义。

## 视图

领导首页和正式导出要求 active、准入通过、trusted verification、not_required/approved、非 unclassified/industry_signal，并满足来源开关和 allowed primary types。行业线索视图展示 industry_signal、media_only、rumor 或 pending；active media 会采集到这里。
