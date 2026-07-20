# Taxonomy v2

v2 将“内容是什么形态”与“内容谈什么”拆开。`primary_type` 每条最多一个；`topic_tags` 和 `industry_tags` 是经过枚举校验、按枚举顺序稳定输出的多选维度。

## 字段

- `primary_type`: `unclassified`、`product_update`、`policy_standard`、`application_opportunity`、`award_result`、`report_release`、`case_analysis`、`industry_signal`。
- `topic_tags`: `model`、`agent`、`agent_platform`、`api`、`open_source`、`industry_application`、`policy`、`standard`、`award`、`case`、`safety_governance`、`data_and_compute`。
- `industry_tags`: `government`、`finance`、`manufacturing`、`energy`、`transport`、`healthcare`、`education`、`telecom`、`internet`、`retail`、`general`。当前实现没有明确场景时使用空列表，不根据企业所属行业猜测。
- `verification_status`: `official_confirmed`、`official_linked`、`multi_source_confirmed`、`media_only`、`rumor_or_prediction`。
- `review_status`: `not_required`、`pending`、`approved`、`rejected`。
- `case_completeness`: `not_case`、`case_lead`、`partial_case`、`full_case`。
- `taxonomy_version`: 当前为 `v2`；`taxonomy_matched_rules` 保留稳定 rule id。

`verification_status` 回答“证据来自哪里、可信到什么程度”；`review_status` 回答“是否需要及是否已经完成人工审核”。两者不得合并。

## 会议不再是分类

普通会议、演讲、参展、亮相和嘉宾介绍由 BasicAdmission 拒绝。会上正式发布模型、政策、征集、名单或报告时，按实质动作分别进入 product、policy、opportunity、award 或 report。没有实质成果的会议不进入信息流。

## 案例完整度

检查 A 背景/痛点、B 方案、C 实施、D 结果、E 量化成效。`full_case` 至少满足三个维度且包含 D 或 E，并要求详情正文抓取成功；标题和摘要的上限是 `case_lead`。`award_result` 出现“案例”不等于 `case_analysis`。

## 机会字段

`organizer`、`application_name`、`application_target`、`deadline_at`、`application_method`、`application_url` 都可为空。只在文本明确给出截止日期时提取；开放/关闭状态按当前时间动态计算。

## 迁移

Migration 保留旧 `category` 和 `manual_category`。旧 model/agent/award/case/policy 分类只安全推导 topic tag；primary type 还必须有确定动作词，否则进入 `unclassified`。旧通知不会一律变成机会，旧会议不会映射为新 primary type。人工覆盖保留。可先运行：

```bash
uv run python -m app.cli taxonomy reclassify --dry-run
uv run python -m app.cli taxonomy reclassify --confirm
```

默认不覆盖人工 primary type、人工标签或人工验证/审核状态。规则位于 `app/config/classification/`，Schema 拒绝重复键、未知字段、重复 rule id、非法枚举；同优先级冲突安全回退 `unclassified`。
