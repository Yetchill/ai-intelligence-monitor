# 来源采集方式复审（2026-07-20）

本轮只复审采集层，不改变数据库模型、taxonomy、分类规则、PublicationPolicy 或 UI 架构。调查顺序固定为：官方 RSS/Atom → RSSHub 已有 route → sitemap → 页面内嵌 JSON → 无需认证的公开接口 → 静态 HTML 站点 adapter → JavaScript 浏览器采集。

RSSHub 当前仓库以 AGPL-3.0 发布。本项目可以消费网站官方 Feed 或未来自建 RSSHub 输出，但不逐行复制 route 源码。下表中的 RSSHub route 只用于核实公开入口和技术可行性。

| slug | 官方 Feed | RSSHub route | sitemap/公开数据 | 推荐方式 | 专用 Collector | 浏览器与注意事项 |
|---|---|---|---|---|---|---|
| caict-aihub-docs | 无 | 无对应 route | sitemap 索引的分片当前 404；docs GET 尚未确认 | document adapter | 是 | 暂不引浏览器 |
| qwen-official-blog | 无 | `/qwen/blog` | 官方公开 `/api/v2/article/retrieval` 实测 200 | public JSON | 是 | 单响应约 4 MB，先解决有界读取；不需浏览器 |
| minimax-news | 无 | 无 | sitemap 不含新闻；SSR 只有少量链接且缺日期 | HTML site adapter + 详情元数据 | 是 | 暂不需浏览器 |
| tencent-hunyuan-product-updates | 无 | 无 | 服务端 HTML 有正文和月份目录 | changelog adapter | 是 | 不需浏览器 |
| tencent-hunyuan-product-announcements | 无 | 无 | 同上 | changelog adapter | 是 | 与产品动态保持独立 |

| caict-special-reports | 无 | 无对应 route | 列表 HTTP 412、sitemap 404 | candidate | 待访问恢复 | 浏览器不得绕过访问限制 |
| caict-aihub-cases | 无 | 无 | 公开 `/internal_api/cases` 实测 200 JSON | public JSON / case adapter | 是 | 不需浏览器 |
| caict-aiia-agent-working-group | 无 | 无 | Vite 壳，尚未确认公开列表 GET | candidate | 待定 | 暂不引浏览器 |

| xinhua-tech | 无 | 无 | 全程 HTTPS 的静态列表入口可用 | HTML site adapter | 是 | 不需浏览器，本轮停止扩展 |
| cls-ai-subject | 无 | `/cls/subject/:id` | `__NEXT_DATA__` 含文章 ID、标题和 Unix 时间 | embedded public JSON | `cls_topic` | 不复制 RSSHub 的签名实现；已 active |
| infoq-ai-llm | 无 | `/infoq/topic/:id` | 官方公开 POST API 实测 200 | public JSON | 是 | 不需浏览器 |
| zhidx-news | 无 | 无 | sitemap 有文章 URL/lastmod；快讯直连只给 Nuxt 壳 | sitemap（文章）/ candidate（快讯） | 是 | 不能依赖代理侧偶发 SSR |
| qbitai | `/category/资讯/feed` | `/qbitai/category/:category` | 官方 WordPress RSS 实测 200 | RSS | 否 | 不依赖 RSSHub 实例；已 active |


## 本轮限定实现结果

- `qbitai`：直接使用官方资讯 Feed；真实 preview 10 条，标题、日期、链接有效率 100%，重复率 0%，已通过激活命令。
- `deepseek-api-updates`：静态 changelog adapter；真实 preview 18 条，三项有效率 100%，重复率 0%。
- `kimi-platform-changelog`：静态 changelog adapter；真实 preview 8 条，三项有效率 100%，重复率 0%。
- `cls-ai-subject`：独立解析公开 `__NEXT_DATA__`；真实 preview 20 条，三项有效率 100%，重复率 0%，已通过激活命令。

媒体来源即使 active 也只表示定时采集。量子位和财联社仍为 `media_discovery`、`always_review`、首页隐藏、正式导出隐藏；条目默认 `media_only`、`pending`，传闻继续标记为 `rumor_or_prediction`。

## Trafilatura 评估

Trafilatura 2.1.0 支持 Python 3.10+ 与 Windows，当前版本使用 Apache-2.0；1.8.0 以前版本为 GPLv3+。其 wheel 约 135 KB，但会增加正文抽取相关依赖。它适合在来源 adapter 已确定详情链接后抽取正文和通用元数据，不应替代 Feed、sitemap、列表或公开 JSON 发现。

本轮五个来源均可仅靠 Feed、内嵌 JSON或单页 changelog 完成列表采集，没有新增详情页抓取点，因此暂不引入 Trafilatura、也不增加无实际调用方的包装层。后续首次接入详情正文时，应固定 Apache-2.0 版本、记录完整传递依赖和 Windows 打包体积，并使用固定 HTML fixture 验证正文、标题、日期与导航噪声排除。

## 浏览器影响

本轮不引入 Crawlee Python 或 Playwright。若后续确认火山方舟、工信部平台等不存在 Feed、RSSHub route、有效 sitemap、公开内嵌 JSON或无需认证接口，再单独评估。引入会增加 Crawlee/Playwright Python 依赖，需要额外下载 Chromium，显著增加 Windows 安装包、首次安装时间、启动和内存成本，因此不能作为通用 HTML 失败后的默认回退。
