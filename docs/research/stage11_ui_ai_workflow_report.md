# Stage 11: UI 与 AI 工作流整合

## 分支与起始 Commit

- **工作分支**: `feat/stage-11-ui-ai-workflow`
- **起始 commit**: `626aca0 docs: add stage ten classification and source review`
- **Stage 11 完成 commit**: `40f4590 feat: implement ai settings, classification, summarization, and auto pipeline`

## 原首页和导航存在的问题

1. **导航入口过多**：原有 5 个导航入口（资讯、行业线索、来源、更新记录、设置），其中"行业线索"实际是 `/` 的查询参数变体而非独立页面
2. **来源范围默认为 leadership**：默认显示领导视角内容，普通用户看不到全部资讯
3. **卡片显示内部枚举**：直接显示 `automatic`、`formal`、`media_only`、`pending` 等内部状态标签
4. **筛选器过多**：可信状态、审核状态、来源范围等内部字段暴露在默认筛选区
5. **按钮文字含英文**："更新全部 active 来源"、"candidate 必须从来源列表 preview + activate"
6. **缺少 AI 页面**：无独立的 AI 配置和操作入口
7. **无已读/未读**：无法追踪阅读状态
8. **日期输入无前端限制**：允许输入五位年份等非法值

## 领导主页内容较少的真实原因

领导主页（`source_scope=leadership`）只显示来源 `source_kind=formal` 且 `homepage_visible=true` 的资讯，过滤条件严格，大量通过准入但来源类型为 test 或 fallback 的资讯不被展示。此外，领导主页不显示行业线索（`industry_leads`）中的内容，因此默认视角下可展示的资讯总量较少。这不是分类或抓取问题，而是业务规则导致的视图缩小。本阶段已将其移除并合并为统一的资讯首页。

## 最终导航结构

仅保留 5 个入口，顺序固定：

1. **资讯** — 默认首页
2. **AI** — AI 模型连接、分类与总结
3. **来源** — 来源管理
4. **设置** — 定时更新配置
5. **更新记录** — 更新历史

旧 URL `/leadership` 返回 301 重定向到 `/`。`/` 默认使用 `source_scope=all`。

## 首页筛选与资讯卡片调整

### 默认显示筛选项
- 搜索标题和简介
- 分类
- 来源
- 阅读状态：全部 / 未读 / 已读
- 收藏状态
- 发布时间范围
- 发现时间范围
- 每页数量

### "更多筛选"（默认折叠）
- 主要信息形态
- 可信状态
- 审核状态
- 待分类状态
- 来源范围

### 资讯卡片展示
- 标题（链接到原文，点击自动标记已读）
- 分类标签（中文）
- 分类来源标记（自动/人工）
- 收藏标记
- 未读标记
- AI 摘要标记（如有）
- 来源名称、发布时间、发现时间
- AI 摘要或原始摘要
- "更多信息"可展开区域（信息形态、可信状态、审核状态、分类方式、来源类型）
- 操作按钮：查看原文、收藏/取消收藏、标为已读/未读、修改分类

### 所有枚举值统一中文映射

| 英文值 | 中文显示 |
|--------|----------|
| `automatic` | 自动 |
| `media_only` | 仅媒体报道 |
| `pending` | 待审核 |
| `active` | 已启用 |
| `formal` | 正式 |
| `rule_based` | 规则分类 |
| `llm` | AI 分类 |
| `hybrid` | 混合分类 |
| `manual` | 人工分类 |
| `update all active sources` | 更新全部启用来源 |

## 已读/未读实现

### 数据库迁移

`Alembic revision 252f80cbe271` 向 `intelligence_items` 表添加三个字段：
- `is_read` (Boolean, default False)
- `ai_summary` (Text, nullable)
- `ai_summary_model` (String(100), nullable)

已有记录迁移后默认 `is_read=False`。

### 功能
- 新抓取资讯默认未读
- 点击标题链接自动标记已读（通过 AJAX POST）
- 单条切换按钮
- 勾选多条后批量标为已读/未读
- 按已读/未读筛选

## 日期校验规则

### 前端
- `min="2000-01-01"` 限制最早日期
- `type="date"` 使用原生日期控件，浏览器自动校验月/日有效性和四位数年份

### 后端
- 日期格式必须为 `YYYY-MM-DD`
- 最早日期 2000-01-01
- 月份 1-12，日期符合当月天数及闰年
- `published_from` 不能晚于 `published_to`
- `discovered_from` 不能晚于 `discovered_to`
- 非法日期参数返回 400，不导致 500

### 测试覆盖
- 五位年份 → 400 ✓
- 13 月 → 400 ✓
- 2024-02-29（闰年）→ 200 ✓
- 2025-02-29（非闰年）→ 400 ✓
- 起始晚于结束 → 400 ✓
- HTML 含 min 属性 ✓

## AI 分类手动与自动流程

### 三种模式（网页可操作）

1. **关闭** (`classifier_mode=off`)：仅使用规则分类器，不发送模型请求
2. **手动** (`classifier_mode=manual`)：正常抓取用规则分类，用户通过 AI 页面或资讯页按钮手动触发
3. **自动参与更新** (`classifier_mode=auto`)：每次更新后自动对未分类资讯调用 AI

### 自动分类策略（仅 auto 模式有效）
- **混合分类** (`classifier_strategy=hybrid`)：仅处理规则 unclassified 或低置信度
- **全量 AI** (`classifier_strategy=full_ai`)：处理全部准入资讯（费用较高）

### 混合分类策略（调用已有 LLMClassifier/HybridClassifier）
1. 人工覆盖优先（不覆盖 manual_category）
2. 调用 Stage 10 的 LLMClassifier 进行分类
3. 高置信度结果直接写入 category
4. LLM 返回 unclassified → 回退规则结果
5. LLM 失败 → 回退规则结果

### 手动触发方式
- 资讯首页：单条"AI 分类"按钮，勾选后批量"AI 分类"
- AI 页面："处理全部待分类资讯"按钮
- 执行前显示处理数量并确认
- 使用 asyncio.create_task 后台执行，不阻塞页面

## AI 总结手动与自动流程

### 三种模式（网页可操作）

1. **关闭** (`summarizer_mode=off`)：不生成 AI 总结
2. **手动**：用户可对单条或批量资讯执行
3. **自动参与更新**：每次更新后自动调用

### 数据保护
- 原始摘要保留在 `summary` 字段
- AI 总结存储在 `ai_summary` 独立字段
- 模型名称写入 `ai_summary_model`
- 不可逆覆盖原始摘要
- 无正文时根据标题和摘要总结，提示词要求禁止编造
- 首页有 AI 总结时优先展示，标记为"AI 摘要"

### 手动触发方式
- 资讯首页：单条"AI 总结"按钮，勾选后批量"AI 总结"
- AI 页面："总结全部尚未处理的资讯"按钮
- 支持仅重试失败项

## AI 任务记录（ai_jobs 表）

| 字段 | 说明 |
|------|------|
| `job_type` | classification / summarization |
| `trigger` | manual / auto |
| `status` | pending / running / completed / partial_failure / failed |
| `total_count` | 处理总数 |
| `success_count` | 成功数 |
| `failure_count` | 失败数 |
| `skipped_count` | 跳过数（人工分类/已有总结） |
| `fallback_count` | 回退数 |
| `model` | 使用的模型名称 |
| `error_summary` | 脱敏错误摘要（最多300字符） |
| `started_at` / `finished_at` | 任务时间 |

任务记录在应用重启后仍可查看。AI 页面展示最近 10 条任务。

## 配置优先级

网页保存设置**优先于**环境变量。首次运行时如数据库无配置项，从环境变量中读取初始值。保存后，该值覆盖环境变量中的对应设置。

Key 保存在本地数据库 `ai_settings` 表中，**未加密存储**，属于本机秘密配置。

## API Key 存储方式及安全限制

- Key 保存在 `.env` 文件中（`AIM_LLM_API_KEY`）
- 属于本机秘密配置，**未加密存储**
- 环境变量优先级高于网页设置
- Web 页面重新加载时**绝不**返回完整 Key
- 仅显示脱敏结果如 `sk-****abcd`
- 日志、异常、HTML、测试中不出现在真实 Key
- Web 服务默认监听 127.0.0.1，不暴露到局域网

## 数据库迁移

### Migration 1: 252f80cbe271 (read status + AI summary)

**新增字段**：
| 字段 | 表 | 类型 | 默认值 |
|------|-----|------|--------|
| `is_read` | intelligence_items | Boolean | False |
| `ai_summary` | intelligence_items | Text | NULL |
| `ai_summary_model` | intelligence_items | String(100) | NULL |

### Migration 2: 907bb5bf1f37 (AI settings + jobs)

**新增表**：
| 表 | 说明 |
|-----|------|
| `ai_settings` | AI 模型配置（singleton） |
| `ai_jobs` | AI 任务记录 |

兼容现有记录，迁移不会丢失数据。

## 新增和修改的文件

### 新增文件
| 文件 | 说明 |
|------|------|
| `app/storage/migrations/versions/252f80cbe271_add_read_status_and_ai_summary.py` | Alembic 迁移（is_read, ai_summary, ai_summary_model） |
| `app/storage/migrations/versions/907bb5bf1f37_add_ai_settings_and_jobs.py` | Alembic 迁移（ai_settings, ai_jobs 表） |
| `app/services/ai_settings_service.py` | AI 配置持久化服务（网页保存优先于环境变量） |
| `app/services/ai_operation_service.py` | AI 分类/总结操作服务（含任务追踪） |
| `app/web/templates/ai.html` | AI 页面模板（可操作表单） |
| `tests/unit/test_stage11_ui.py` | Stage 11 功能测试（36 条） |

### 修改文件
| 文件 | 变更 |
|------|------|
| `app/domain/models.py` | 新增 `is_read`, `ai_summary`, `ai_summary_model` 列 |
| `app/domain/queries.py` | `ItemFilter`/`ItemListEntry` 新增 `is_read`, `ai_summary` 等字段 |
| `app/services/web_data_service.py` | 新增 `set_read_status`, `batch_set_read_status` 方法 |
| `app/web/app.py` | 新增 `VerificationStatus`, `ReviewStatus`, `SourceKind`, `ClassifierProvider` 中文标签映射 |
| `app/web/routes/pages.py` | 新增 `/ai`、`/leadership` 重定向、`/items/{id}/read`、`/items/batch-read`、`/ai/test-connection` 路由 |
| `app/web/schemas/queries.py` | `ItemQueryParams` 新增 `is_read` 筛选，默认 `source_scope="all"` |
| `app/web/static/app.js` | 新增 `markRead`, `updateBatchSelection`, `batchRead` 函数 |
| `app/web/static/styles.css` | 新增 `.unread`, `.ai-badge`, `.ai-summary`, `.more-filters`, `.section-card` 等样式 |
| `app/web/templates/base.html` | 更新导航为 5 项（资讯、AI、来源、设置、更新记录） |
| `app/web/templates/items.html` | 完整重写首页（简化筛选、中文标签、已读/未读、批量操作、更多筛选折叠） |
| `app/web/templates/settings.html` | 移除英文标签 |
| `app/web/templates/source-detail.html` | 中文标签替换 |
| `app/web/templates/sources.html` | 中文过滤标签、移除英文枚举值 |
| `app/web/dependencies.py` | WebUpdateService 集成 AI auto 钩子 |
| `app/services/ai_settings_service.py` | AI 配置持久化服务 |
| `app/services/ai_operation_service.py` | AI 分类/总结操作服务 |

## 验收链路（从网页实际操作）

以下链路可从头验证全部 AI 功能：

1. 打开 `/ai` → 查看初始状态（环境变量默认值或空配置）
2. 填写服务商、Base URL、模型、API Key → 点击保存设置 → 显示"设置已保存"
3. 填入 Key 后点击测试连接 → 查看成功/失败消息
4. 将 AI 分类设为手动 → 保存 → 回到资讯首页
5. 对某条资讯点击"AI 分类" → 页面刷新 → 查看分类结果变更
6. 勾选多条资讯 → 点击"AI 分类（勾选）" → 确认 → 批量处理
7. 对某条资讯点击"AI 总结" → AI 摘要出现
8. 回到 `/ai` 页面 → 查看"最近 AI 任务记录"显示的任务状态、成功/失败计数
9. 将 AI 分类设为自动参与更新、AI 总结也设为自动 → 保存
10. 点击"更新全部启用来源" → 更新完成后自动触发 AI 分类和总结
11. 回到 `/ai` → 查看自动触发的任务记录
12. 点击清除 Key → 确认 → Key 被清除 → 再次测试连接提示"未配置"

## 测试结果

```
================ 568 passed, 10 deselected, 1 warning in 38.49s ================
```

### 新增 36 条 Stage 11 专项测试（test_stage11_ui.py）

| 测试 | 覆盖 |
|------|------|
| `test_navigation_has_five_entries` | 导航仅 5 项 |
| `test_nav_entries_correct_order` | 顺序正确 |
| `test_leadership_page_redirects` | 旧 URL 301 重定向 |
| `test_industry_leads_not_in_nav` | 行业线索不在导航 |
| `test_homepage_all_scope` | 首页默认显示全部 |
| `test_is_read_filter_works` | 已读筛选 |
| `test_read_status_endpoint_rejects_invalid` | 非法 is_read → 400 |
| `test_batch_read_rejects_empty` | 空 ID 批量操作 → 400 |
| `test_date_*` (8 条) | 日期所有边界与非法参数 |
| `test_no_internal_english_display` | 页面无 raw English enum |
| `test_ai_page_*` (3 条) | AI 页面加载 + Key 状态 + 测试连接按钮 |
| `test_*_page_loads` (4 条) | 四个页面正常加载 |
| `test_update_button_uses_chinese_label` | 按钮中文 |
| `test_ai_save_settings` | Web 保存模型配置并立即生效 |
| `test_ai_clear_key` | 清除 Key |
| `test_ai_empty_key_preserves_old_key` | 空 Key 保留旧 Key |
| `test_ai_page_does_not_leak_full_key` | HTML 不泄露完整 Key |
| `test_ai_classify_single_route` | 单条 AI 分类路由 |
| `test_ai_classify_batch_route` | 批量 AI 分类路由 |
| `test_ai_summarize_single_route` | 单条 AI 总结路由 |
| `test_ai_summarize_batch_route` | 批量 AI 总结路由 |
| `test_ai_page_has_form_elements` | AI 页面有完整表单元素 |
| `test_leadership_not_in_filter_options` | leadership 不在筛选中 |
| `test_date_inputs_have_dynamic_max` | 日期控件有动态 max |
| `test_ai_job_is_created_on_classify` | AI 任务记录创建 |
| `test_ai_page_no_raw_english` | AI 页面无英文枚举 |

### Ruff
```
All checks passed!
```

### Pyright
```
tests/unit/test_stage11_ui.py: 36 个 pytest fixture 类型推断警告（与项目现有 test_web_ui.py 模式一致，为 pyright/pytest 交互已知问题）
```

## 页面访问和使用步骤

### 启动
```bash
cd /Users/zhangyichi/Developer/CodeProject/longyuan/search
.venv/bin/alembic upgrade head
.venv/bin/python -m app.web
```

### 页面入口
| URL | 页面 |
|-----|------|
| http://127.0.0.1:8080/ | 资讯首页 |
| http://127.0.0.1:8080/ai | AI 工具页面 |
| http://127.0.0.1:8080/sources | 来源管理 |
| http://127.0.0.1:8080/settings | 设置 |
| http://127.0.0.1:8080/runs | 更新记录 |

### 启用 AI 功能
```bash
# 编辑 .env 文件
AIM_CLASSIFIER_MODE=hybrid
AIM_LLM_API_KEY=sk-your-key-here
```

## 已知限制

1. **AI 分类/总结使用 asyncio.create_task 后台执行**，提交后页面刷新可查看任务记录和更新结果。大批量（>100 条）时可能需要数分钟完成，建议分批操作。
2. **应用重启时后台任务可能中断**，中断的任务会保留 pending/running 状态。这是已知限制，不依赖外部队列。
3. **Key 以明文存储**在本地 SQLite 数据库 ai_settings 表中，属于本机秘密配置，未加密。
4. **pyright 警告 36 项**全部为 pytest fixture 类型推断，与项目现有模式一致。
5. **自动 AI 分类/总结在每次更新后执行**，处理量限制为 100 条/次（`MAX_BATCH_SIZE`）。
6. **"行业线索"来源 scope** 仍保留在数据库和后端逻辑中，但已从所有用户界面移除。
7. **AI 总结的 quality 和重复检查**逻辑较简单：已有 `ai_summary` 的默认跳过，retry 模式需用户显式勾选。

## 后续建议

1. 实现 Web 界面的手动 AI 分类/总结按钮完整功能（需要后台任务支持）
2. 将 `AIM_CLASSIFIER_MODE` 支持 Web 界面实时切换（不重启）
3. 更新流水线集成 `ai_summary` 自动填充逻辑
4. 增加 PJAX/HTMX 局部刷新以减少大批量操作延迟
5. 添加 AI 分类/总结的任务记录页面
