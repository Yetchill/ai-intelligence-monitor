# 更新流水线

## 入口与执行过程

`UpdatePipeline` 是 UI、最小 CLI 和未来任务调度唯一应调用的更新入口。它不硬编码来源或具体
Collector，执行顺序为：

```text
查询 Source
→ CollectorRegistry 创建 Collector
→ 网络采集
→ 标准化 CollectedItem
→ canonical URL / 同来源 fingerprint 去重
→ RuleBasedClassifier 分类
→ 保存或更新 IntelligenceItem
→ 内容变化时创建 ItemRevision
→ 更新 Source 状态
→ 汇总并完成 CrawlRun
```

默认更新全部 enabled 来源。指定 `source_id` 时只更新该来源；不存在会抛出清晰错误，disabled
来源会拒绝执行，只有显式 `allow_disabled=True` 才允许。`UpdateMode.incremental` 与
`UpdateMode.history` 共用同一流水线；历史模式只传递受限的页数、条数和时间范围，不承诺所有
Collector 都实现多年翻页，也不能突破 Collector 自身硬上限。

## 标准化与分类

入库前重新压缩标题/简介空白，以采集结果的 `original_url` 重新生成 canonical HTTP(S) URL，
将时间统一解释为 UTC，并通过 JSON 编解码验证 `extra`。空标题、非法 URL 或不可序列化 extra
只跳过当前记录。来源返回多条记录时单条失败不影响其他记录；非空结果全部无效时该来源失败。
`source_id` 始终取当前数据库 Source，Collector 返回结构没有覆盖它的入口。

`extra._source_discoveries` 是系统保留键。Collector 提交的同名字段一律丢弃，不能伪造或覆盖
内部发现记录；业务 `extra` 必须是可递归 JSON 编解码的对象。数据库中若遗留非对象 extra 或
损坏的内部发现列表，流水线会将其按空对象/有效记录子集安全清洗，而不是让整个来源失败。

每条有效记录调用 `RuleBasedClassifier`。新增条目保存自动类别、分数、原因和 provider。
已有条目的自动分类字段可以刷新，但 `manual_category` 与收藏永远不被流水线覆盖；有效展示分类
为 `manual_category or category`。最终有效分类为 `unclassified` 的发现会进入运行统计。

## 幂等、去重与跨来源 URL

匹配顺序是：

1. 全局 `canonical_url` 完全匹配；
2. `(source_id, fingerprint)` 匹配；
3. fingerprint 使用版本化的规范化标题 SHA-256，因查询和唯一约束都带 source_id，不会仅凭
   常见短标题跨来源合并。

重复内容只更新 `last_seen_at` 并计为 skipped。标题、简介、发布时间或业务 extra 改变时计为
updated。last_seen 或自动分类字段单独变化不计 updated。新插入位于数据库保存点内；若并发任务
先写入并触发 canonical URL 或 source/fingerprint 唯一约束，保存点回滚后重新查询已有记录，
不会破坏整个来源事务。

`discovered` 是 Collector 返回的原始记录数，包含之后被拒绝或批内折叠的记录。标准化失败的
每条原始记录计入 skipped；同一批次中映射到同一持久化条目的多个有效结果只处理首个，不重复
进入 new、updated、skipped 或 unclassified。因此这四个结果计数是互斥的持久化决策，不要求
与原始 discovered 相加相等。该首个有效结果优先规则避免同一条目在一次运行中既 new 又 updated，
也避免同批重复产生多条 Revision。

canonical URL 当前全局唯一。另一来源发现相同 URL 时不创建第二条记录，不覆盖首条记录的来源、
内容、人工分类、自动分类或收藏，只更新 last_seen，并在 `extra._source_discoveries` 保存额外来源
的 id、名称和首次/最近发现时间。未来需要完整的多来源生命周期时，新增 Alembic 迁移和
`ItemSource` 关联表；阶段四不引入复杂多对多模型。

内部发现列表按 `source_id` 稳定排序并按来源去重；重复发现只更新该来源的 `last_seen_at`，保留
`first_seen_at`。它不参与业务 extra 比较，不触发自动重分类、updated 或 ItemRevision。

## Revision

只有 `title`、`summary`、`published_at` 和业务 `extra` 的有效变化创建 `ItemRevision`。old_data
和 new_data 仅含变化字段，时间以 UTC ISO 字符串保存，内部 `_source_discoveries` 不属于业务
extra。Revision 关联产生它的 CrawlRun。last_seen 和自动分类变化不创建 Revision；分类审计与
内容修订保持分离。

业务 extra 的 JSON 对象键顺序没有语义；数组顺序有业务语义，顺序变化会产生 Revision。摘要的
空字符串和纯空白统一为 `None`；naive 时间按 UTC 解释，aware 时间转换为 UTC，因此同一时刻的
不同时区表达不会产生虚假 Revision。

## 事务与故障隔离

流水线先用短只读 UoW 选择来源，再立即用独立 UoW 创建并提交 running CrawlRun。网络采集期间
没有数据库 UoW 或写事务。每个来源采集完成后，使用独立短事务完成条目、Revision 和 Source
成功状态写入；一个来源失败不会回滚之前来源。失败状态使用另一个短事务更新 `last_checked_at`
和净化后的 `last_error`。

来源事务提交失败时，该来源的条目、Revision 和成功状态整体回滚，new/updated 不进入 CrawlRun；
随后以独立短事务尽力保存失败状态并继续后续来源。如果失败状态本身无法保存，只记录净化后的
内部错误，不递归重试或覆盖原始来源错误。CrawlRun 的最终完成同样使用独立事务；最终保存首次
失败会进入一次 failed 收尾尝试，第二次失败只记录日志并重新抛出原始异常，避免递归。
若数据库在两次收尾时都持续不可写，系统无法物理更新该行，可能保留 running；调用方会收到
首次异常，后续可据日志和 running 记录人工恢复。这是持久存储完全不可用时的已知边界。

用户可见错误会去掉 HTML、URL 查询串和常见密钥值并限制长度。crawler 日志保留异常类型、
净化消息和 traceback 文件/行号，不写完整响应 HTML 或秘密值。Repository/UoW 对服务隐藏
SQLAlchemy Session，UI 和 CLI 只接触应用服务和结果对象。

## CrawlRun 状态

每次有效更新选择完成后立即创建 `status=running` 的 CrawlRun，写入 started_at 和 source_total。
结束时写入 finished_at、来源成功/失败数、discovered/new/updated/skipped/unclassified 及错误摘要：

- 所有来源成功（包括没有 enabled 来源）：`success`；
- 至少一个成功且至少一个失败：`partial_success`；
- 所有来源失败：`failed`；
- 流水线级未捕获异常：尽力完成为 `failed`，随后把异常重新抛给调用方。

正常返回路径不会留下 running。来源不存在或显式请求 disabled 来源的校验发生在创建 CrawlRun
之前，因此无效请求本身不会产生伪运行记录。

`unclassified` 按本次互斥持久化决策涉及条目的最终有效分类统计，即
`manual_category or category`；已有人工分类的条目不计入待确认。独立 `reclassify_item` 在分类
网络/异步边界外关闭读取 Session，再用短事务写自动分类字段且不覆盖人工分类；`reclassify_all`
逐条调用该入口，失败前已成功条目保持提交，失败会向调用方抛出。
