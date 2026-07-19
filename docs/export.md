# Excel 与 Word 导出

## 范围与入口

阶段六提供 Excel 和 Word 两种只读导出。导出不会创建更新运行、修订记录，也不会修改资讯、
收藏或分类。当前不支持 PDF、自动邮件发送、定时导出或外部图片嵌入。

资讯首页的“导出当前筛选结果”区域显示匹配条数和范围。先使用首页筛选，再点击“导出 Excel”
或“导出 Word”；当前关键词、最终分类、来源、收藏、发布时间、发现时间和待分类条件会随 POST
请求提交。多个条件按 AND 组合，导出全部匹配记录，不受当前页码和每页条数影响。没有匹配项时
不会生成空文件。

首页与导出共用 `ItemFilter`、Repository 条件构造器和稳定排序：

```text
coalesce(published_at, discovered_at, updated_at) DESC, id DESC
```

最终分类始终为 `manual_category or category`，因此人工分类优先于自动分类。

阶段八起默认正式导出还要求 Source 为 enabled + formal + `export_visible=true`；准入 rejected
内容从未进入 item 表。用户在首页显式选择全部、非正式、备用或停用来源后可以导出相应历史，
但来源性质会随文件明确标记。CLI 默认同样使用 formal_export 范围。

## Excel 文件

Excel 使用 `openpyxl` 生成，默认工作表为：

- `资讯列表`：序号、标题、最终分类、分类来源、来源名称、发布时间、发现时间、简介、原文链接、
  收藏状态、自动分类分数、自动分类原因和来源性质；
- `导出说明`：生成时间、筛选条件、条数、分类规则和内部参考提示。

资讯表首行加粗、冻结在 `A2`、开启自动筛选，并设置列宽和自动换行。时间统一显示为
`YYYY-MM-DD HH:MM`。有效 HTTP(S) 原文地址以“查看原文”可点击链接展示，不写入冗长 URL。

所有来源文本均视为不可信。写入文本前会移除 XML 1.0 不允许的控制字符、限制单元格长度；以
`=`、`+`、`-`、`@` 开头，或在前导空白、制表符、换行、控制/格式字符后出现这些前缀的内容会
加文本前缀，防止 Excel 公式注入；普通负数保持原样。加前缀后的总长度仍不超过 Excel
单元格 32,767 字符上限。文件不包含外部图片、网页内容、附件或宏。

## Word 报告

Word 使用 `python-docx` 生成，标题为“AI行业动态与成果申报情报汇总”，并包含生成时间、筛选
摘要和条目总数。报告按最终分类分组，默认顺序为：

1. 大模型与技术；
2. 智能体与产品；
3. 企业成果与案例；
4. 奖项与优秀案例；
5. 征集与申报；
6. 政策、标准与行业；
7. 待分类。

没有内容的分类不生成章节。每条资讯包含标题、来源及来源性质、发布时间、人工/自动分类标记、可选简介
和可点击原文链接；没有简介时不生成空简介段落。文档设置中文字体、页边距、段落间距、标题
层级和分类分页，不嵌入图片或原始 HTML，不调用 LibreOffice，也不生成 PDF。

## CLI

CLI 与 Web 使用同一个 `ExportService`：

```bash
uv run python -m app.cli export excel --output output/report.xlsx
uv run python -m app.cli export word --output output/report.docx
```

筛选和限制示例：

```bash
uv run python -m app.cli export excel \
  --category solicitation \
  --source-id 1 \
  --favorite \
  --published-from 2026-07-01 \
  --published-to 2026-07-18 \
  --discovered-from 2026-07-01 \
  --discovered-to 2026-07-18 \
  --query 征集 \
  --unclassified \
  --limit 1000 \
  --output output/solicitation.xlsx
```

日期格式为 `YYYY-MM-DD`，结束日期按该自然日包含处理。未提供 `--output` 时，文件写入项目
`output/`，名称包含生成日期。显式路径的父目录会安全创建；文件已存在时命令返回非零且不覆盖，
只有指定 `--force` 才原子替换普通目标文件。目标路径本身是目录或符号链接时明确拒绝；临时
文件与目标文件位于同一目录。Excel 路径必须以 `.xlsx` 结尾，Word 路径必须以 `.docx` 结尾。

`output/*` 被 Git 忽略，只保留 `output/.gitkeep`，导出文件不会堆积在项目根目录。

## 数量与资源限制

- Excel 默认及硬上限为 10,000 条；
- Word 默认及硬上限为 2,000 条；
- CLI `--limit` 可以进一步降低本次上限，不能突破格式硬上限；
- 结果超过本次上限时拒绝生成，并提示缩小筛选范围，不静默截断；
- Repository 只执行一次带 `LIMIT hard_limit + 1` 的联表查询，不读取全库后由 Python 筛选；
- Web 文件使用 `BytesIO` 返回，不创建服务器临时文件；CLI 临时文件在成功和异常路径都会清理。

## 安全边界

Web 请求不能指定输出路径或文件名。响应使用固定安全文件名、ASCII 回退名和 UTF-8 中文名，
并拒绝响应头控制字符。只有无控制字符的 HTTP(S) 地址会写成 Office 外部超链接。文本始终按
纯文本写入，不解释 HTML 或脚本。错误页面和 CLI 错误会经过现有净化边界，不显示数据库路径、
临时路径、网页内容或堆栈。
