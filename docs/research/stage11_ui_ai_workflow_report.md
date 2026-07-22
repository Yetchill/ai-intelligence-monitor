# Stage 11: UI 与 AI 工作流整合

## 分支与起始 Commit

- **工作分支**: `feat/stage-11-ui-ai-workflow`
- **起始 commit**: `626aca0 docs: add stage ten classification and source review`

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

### 三种模式
1. **关闭** (`AIM_CLASSIFIER_MODE=rule`)：仅使用规则分类器
2. **手动**：正常抓取时使用规则分类，用户可对单条或批量资讯执行 AI 分类
3. **自动参与更新** (`AIM_CLASSIFIER_MODE=hybrid`)：资讯通过准入后自动进入混合分类流程

### 混合分类策略
1. 人工覆盖优先
2. 规则高置信度且非 unclassified → 跳过 LLM
3. 规则 unclassified、ambiguous 或低置信度 → 调用 LLM
4. LLM confidence ≥ threshold → 采用 LLM 结果
5. LLM 低置信度或失败 → 回退规则结果

### 回退保证
- AI 失败不回写、不覆盖人工分类
- 不把准入拒绝的资讯发送给模型
- 规则分类在无 API Key 时完全正常

## AI 总结手动与自动流程

AI 总结目前与 AI 分类共享模型配置。模式同分类：
1. **关闭**：不生成 AI 总结
2. **手动**：用户可对单条或批量资讯执行
3. **自动参与更新**：仅总结本次新抓取的资讯

### 数据保护
- 原始摘要保留在 `summary` 字段
- AI 总结存储在 `ai_summary` 独立字段
- 不可逆覆盖原始摘要
- 无正文时根据标题和摘要总结，提示词要求避免编造
- 首页有 AI 总结时优先展示，标记为"AI 摘要"

## API Key 存储方式及安全限制

- Key 保存在 `.env` 文件中（`AIM_LLM_API_KEY`）
- 属于本机秘密配置，**未加密存储**
- 环境变量优先级高于网页设置
- Web 页面重新加载时**绝不**返回完整 Key
- 仅显示脱敏结果如 `sk-****abcd`
- 日志、异常、HTML、测试中不出现在真实 Key
- Web 服务默认监听 127.0.0.1，不暴露到局域网

## 数据库迁移

```
Revision ID: 252f80cbe271
Revises: d4e5f6a7b8c9
```

**新增字段**：
| 字段 | 表 | 类型 | 默认值 |
|------|-----|------|--------|
| `is_read` | intelligence_items | Boolean | False |
| `ai_summary` | intelligence_items | Text | NULL |
| `ai_summary_model` | intelligence_items | String(100) | NULL |

**新增索引**：`ix_items_is_read` on `is_read`

兼容现有记录，迁移不会丢失数据。

## 新增和修改的文件

### 新增文件
| 文件 | 说明 |
|------|------|
| `app/storage/migrations/versions/252f80cbe271_add_read_status_and_ai_summary.py` | Alembic 迁移 |
| `app/web/templates/ai.html` | AI 页面模板 |
| `tests/unit/test_stage11_ui.py` | Stage 11 功能测试（23 条） |

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

## 测试结果

```
================ 555 passed, 10 deselected, 1 warning in 37.70s ================
```

### 新增 23 条 Stage 11 专项测试

| 测试 | 覆盖 |
|------|------|
| `test_navigation_has_five_entries` | 导航仅 5 项 |
| `test_nav_entries_correct_order` | 顺序正确 |
| `test_leadership_page_redirects` | 旧 URL 301 重定向 |
| `test_industry_leads_not_in_nav` | 行业线索不在导航 |
| `test_homepage_all_scope` | 首页默认显示全部 |
| `test_is_read_filter_works` | 已读筛选正常工作 |
| `test_read_status_endpoint_rejects_invalid` | 非法 is_read 值 → 400 |
| `test_batch_read_rejects_empty` | 空 ID 批量操作 → 400 |
| `test_date_*` (8 条) | 日期所有边界与非法参数 |
| `test_no_internal_english_display` | 页面无 `automatic`、`media_only` 等原始英文枚举 |
| `test_ai_page_*` (3 条) | AI 页面加载、Key 状态显示、测试连接按钮 |
| `test_*_page_loads` (4 条) | 资讯/设置/来源/更新记录页面正常加载 |
| `test_update_button_uses_chinese_label` | 按钮文字使用中文 |

### Ruff
```
All checks passed!
```

### Pyright（修改文件）
```
0 errors (test_stage11_ui.py 有 24 项 pytest fixture 参数类型推断问题，与现有 test_web_ui.py 模式一致，为 pyright/pytest 交互已知问题)
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

1. **AI 分类/总结当前仅支持 Web 配置查看**，实际触发需通过改变 `AIM_CLASSIFIER_MODE` 环境变量或 CLI；Web 界面的手动 AI 分类/总结按钮尚未完整实现
2. **AI 分类模式切换需重启应用**，通过环境变量控制
3. **测试连接按钮功能存在**，但页面返回旧数据后测试结果显示需刷新
4. **pyright 警告 24 项**全部为 pytest fixture 类型推断，与项目现有模式一致
5. **批量操作使用传统表单提交**，大规模（>100 条）时可能有延迟
6. **数据库字段 `ai_summary_model`** 尚未在更新流水线中自动填充
7. "更多筛选"区域中的来源范围仍保留 `leadership` 选项作为内部值，但已从默认筛选中移除

## 后续建议

1. 实现 Web 界面的手动 AI 分类/总结按钮完整功能（需要后台任务支持）
2. 将 `AIM_CLASSIFIER_MODE` 支持 Web 界面实时切换（不重启）
3. 更新流水线集成 `ai_summary` 自动填充逻辑
4. 增加 PJAX/HTMX 局部刷新以减少大批量操作延迟
5. 添加 AI 分类/总结的任务记录页面
