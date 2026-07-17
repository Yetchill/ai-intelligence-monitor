# Collector 与来源配置开发

## 边界

Collector 的职责是从一个已确认来源发现列表项并返回 `CollectedItem`。它不保存数据库、不分类、不执行更新流水线、不进入详情页，也不处理登录、验证码或浏览器渲染。

每个实现接收一个 `Fetcher`，并实现：

```python
class ExampleCollector:
    name = "example"

    def __init__(self, fetcher: Fetcher) -> None:
        self._fetcher = fetcher

    async def collect(self, context: CollectContext) -> list[CollectedItem]:
        response = await self._fetcher.fetch(context.source_url)
        # 只解析当前列表响应
        return []
```

返回的有效记录必须有非空标题，以及经过 `canonicalize_url()` 或 `resolve_url()` 验证的 HTTP(S) 原始/规范链接。单条坏数据应跳过，不应使同一来源的其他记录丢失。

## 注册新 Collector

内置注册表由 `default_collector_registry()` 创建。应用组合层可以注册新实现，无需修改采集主流程：

```python
registry = default_collector_registry()
registry.register("example", ExampleCollector)
collector = registry.create(source, fetcher)
```

`Source.collector_name` 是稳定注册名；为空时才回退到 `Source.source_type.value`。重复注册默认报错，开发期明确替换可使用 `replace=True`。新增 Collector 应同时增加固定样本单元测试，并更新本文件和架构文档。

## RSS / Atom

配置通常可以为空：

```json
{}
```

`RSSCollector` 只读取 Feed 自带标题、链接、发布时间和摘要，不访问 entry 详情页。Feed 中单条缺少标题或链接时会跳过该条。

## GitHub Releases

入口可使用仓库地址、Releases 地址或 `owner/repository`：

```text
https://github.com/QwenLM/Qwen-Agent
https://github.com/QwenLM/Qwen-Agent/releases
QwenLM/Qwen-Agent
```

可选配置：

```json
{
  "max_releases": 30,
  "include_prereleases": false,
  "summary_max_chars": 500
}
```

Collector 优先调用不需要 Token 的公开 GitHub API。API 配额耗尽时转用公开 `releases.atom`；draft 不会出现在结果中，prerelease 默认排除。release assets 不读取、不抓取、不下载。

## HTML selector 模式

适合结构稳定的列表页：

```json
{
  "allowed_domains": ["example.com"],
  "allow_subdomains": false,
  "keep_query_params": ["page"],
  "discovery": {
    "mode": "selectors",
    "max_pages": 2,
    "max_depth": 1,
    "pagination_selector": "a.next"
  },
  "extraction": {
    "item_selector": ".news-list li",
    "title_selector": "a.title",
    "link_selector": "a.title",
    "date_selector": "time, .date",
    "summary_selector": ".summary"
  }
}
```

只有 `pagination_selector` 明确选出的列表翻页链接会继续请求；候选文章详情链接不会请求。未配置分页选择器时仍只取入口页；默认上限为 20 页/深度 1，硬上限为 100 页/深度 3。

部分服务端渲染页面把标题/日期放在 DOM 中，但把点击 URL 放在页面内嵌 JSON 数据。此时可配置标题关联键：

```json
{
  "extraction": {
    "item_selector": ".news-list .item",
    "title_selector": "h3",
    "date_selector": "span.date",
    "embedded_title_key": "title",
    "embedded_link_key": "external_url"
  }
}
```

这只解析已获取 HTML 中的公开文本，不执行网页脚本。如果页面必须执行 JavaScript、登录或通过验证码才能获得列表数据，应标记为需要专用/浏览器采集器，而不是在阶段二绕过限制。

## HTML link-filter 模式

适合简单首页和栏目页：

```json
{
  "allowed_domains": ["example.com"],
  "discovery": {
    "mode": "link_filter",
    "max_pages": 1,
    "max_depth": 0,
    "include_text": ["通知", "征集", "发布", "成果"],
    "exclude_text": ["登录", "注册", "联系我们", "活动日历"],
    "include_url_patterns": ["/news/", "/notice/"],
    "exclude_url_patterns": ["/login", "/calendar"]
  }
}
```

当任一 include 规则存在时，标题或 URL 至少命中一项才保留；exclude 规则优先。非允许域名、非 HTTP(S)、静态资源、纯数字和过短标题会被排除。link-filter 不会自动递归文章链接。

## 测试

固定样本放在 `tests/fixtures/`，单元测试不得依赖公网：

```bash
uv run pytest
```

实时来源测试带 `network` 标记，默认跳过：

```bash
uv run pytest -m network -s
```

集成测试只断言纯采集结果，不创建或写入正式数据库。网络状态、站点结构和公共 API 配额会变化，失败时应先确认错误类别，再更新来源配置或固定样本。
