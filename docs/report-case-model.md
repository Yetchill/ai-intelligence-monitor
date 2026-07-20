# 报告与案例父子模型

`IntelligenceItem.parent_item_id` 是可空自关联。父记录使用 `report_release`；从报告中可靠拆出的子记录使用 `case_analysis`，并拥有独立标题、行业标签、完整度和 fingerprint。删除父记录时数据库将子记录的 parent 置空，避免误删独立业务内容。

Repository 提供按 parent id 查询子项。`DocumentHubCollector` 定义报告/案例嵌套接口，fixture 实现用 `parent_fingerprint` 在持久化时解析父项；`CaseHubCollector` 为案例入口提供接口并只标记 record kind。唯一 `(source_id, fingerprint)` 保证重复运行不重复创建。

本阶段不声称能拆分所有真实 PDF，不使用 OCR 或浏览器自动化。详情、附件或章节边界不可靠时，只保存 report_release，不伪造案例子项。CAICT 报告和案例入口因此仍是 candidate，需要后续专用 Collector。
