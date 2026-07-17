# 分类系统

## 当前范围

阶段三当前只实现纯逻辑分类子系统。它消费阶段二不可变的 `CollectedItem`，返回
`ClassificationResult`，不访问数据库、不修改采集结果，也不调用外部 API 或大模型。
更新流水线、网页人工改分类和分类结果持久化尚未实现。

一级分类严格限定为：

```text
model_technology
agent_product
enterprise_case
award_case
solicitation
policy_industry
unclassified
```

## 接口与优先级

`Classifier` 是异步 Protocol。当前可用实现为 `RuleBasedClassifier`；
`ManualClassifier` 和 `FinalCategoryResolver` 负责解析人工值并合成最终结果。
最终优先级为：

```text
manual_category
> 规则分类的明确结果
> 来源默认分类
> unclassified
```

人工分类只要非空且属于上述分类，就直接返回 `provider=manual`，包括人工明确选择
`unclassified` 的情况。无效人工值会产生清晰异常，不会悄悄回退。当前没有 AI 分类结果，
因此 AI 优先级尚未进入运行路径。

`ClassificationResult` 包含：

- `category`：最终 `Category`；
- `score`：所选规则候选的原始得分，人工覆盖固定为 1.0；
- `reason`：阈值、分差、命中和回退原因；
- `provider`：`rule_based`、`source_default` 或 `manual`；
- `matched_rules`：命中的字段、规则类型、词和分值；
- `is_ambiguous`：是否因前两名分差不足而待确认。

## 规则文件

规则位于 `app/config/classification_rules.yaml`。结构为：

```yaml
settings:
  minimum_score: 10
  minimum_margin: 3
  title_weight: 2
  summary_weight: 1
  phrase_weight: 1.5
  source_default_weight: 2

categories:
  solicitation:
    priority: 100
    phrases:
      案例征集: 10
    keywords:
      征集: 5
    negative_phrases:
      申报上市: -12
```

所有六个业务分类都必须存在；`unclassified` 不是打分候选，不配置业务关键词。加载时会校验
根节点、字段、分类名称、优先级、数值是否有限、正向规则是否为正分、排除规则是否为负分，
并要求 `title_weight > summary_weight`。未知分类、未知字段、缺失字段和错误 YAML 都会抛出
`RuleConfigError`，错误消息包含具体配置位置。

## 计分与判定

文本先进行 Unicode NFKC 宽度统一、英文大小写折叠、中文基础标点转换和空白压缩。
该过程保留 `V2.1` 等版本号，不做分词、词干化或会丢失中文语义的清洗。每条配置规则在
标题和简介中各最多计分一次，避免重复出现同一个词造成无限累加。

计分公式为：

```text
标题词组 = 规则分 × title_weight × phrase_weight
简介词组 = 规则分 × summary_weight × phrase_weight
标题关键词 = 规则分 × title_weight
简介关键词 = 规则分 × summary_weight
排除词 = 负分 × 对应字段权重
来源默认分类 = 对应候选额外加 source_default_weight
```

因此标题证据强于简介，完整词组强于同分关键词。来源默认分类只提供较弱先验，不能单独越过
当前阈值。候选先按总分降序排列，同分时按 `priority` 降序排列，然后：

1. 第一名低于 `minimum_score`：使用非空来源默认分类；没有默认分类则 `unclassified`；
2. 第一名达到阈值，但与第二名分差小于 `minimum_margin`：返回 `unclassified`，并设置
   `is_ambiguous=true`；
3. 其余情况采用第一名，并在 `reason` 和 `matched_rules` 中说明证据；
4. 最后由 `FinalCategoryResolver` 应用人工分类，人工值始终覆盖自动结果。

规则特别区分机会发生阶段与结果阶段：征集、申报启动、参评通知归 `solicitation`；入选、
获奖、名单和公示结果归 `award_case`；标准、政策、办法、规划和征求意见归
`policy_industry`。`参编单位征集` 作为可参与机会归 `solicitation`。`negative_phrases`
负责抵消“申报上市”“征集结果公布”等表面词导致的误判。

## 添加关键词与处理误判

添加规则时只编辑 YAML：

1. 优先添加语义明确的 `phrases`，分值可以高于宽泛 `keywords`；
2. 单个关键词应避免“发布”这类没有业务上下文就无法分类的词；
3. 某词只在特定上下文误判时，向错误分类加入 `negative_phrases`，不要在 Python 中写标题特判；
4. 运行固定样本、全套测试和静态检查，检查总体准确率与 `solicitation`、`award_case` 指标；
5. 对确实同时指向两类的内容保留待确认，不要用过大的分值掩盖歧义。

固定标注集位于 `tests/fixtures/classification_cases.yaml`。测试会计算总体准确率、各类别正确数
和混淆项；新增规则时应先补充具有代表性的人工标注样本。

## AI 未来接入点

`LLMClassifier` 与 `HybridClassifier` 目前只是会明确报“未实现”的空实现，不依赖 SDK、
API Key 或外部服务。未来 Hybrid 的预期路由是：

```text
规则结果置信度高且不模糊
→ 直接使用规则结果

规则分数低、分差不足或待确认
→ 才调用 LLMClassifier

LLM 未配置或不可用
→ 保持 unclassified
```

未来 Provider 必须继续实现 `Classifier` 边界，不能嵌入 Collector，也不能在分类器内直接写数据库。
