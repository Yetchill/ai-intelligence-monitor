# 来源生命周期

来源技术运行状态与内容发布状态严格分离。

- `candidate`: 已登记、已入库、可 preview，但技术尚未验收；不参加 update all 和调度。
- `active`: Collector、配置和 preview 达到抓取门槛；参加批量更新和调度。
- `paused`: 曾可用但由用户暂停、结构变化或质量下降；历史内容保留，目录同步不自动恢复。

`enabled` 保留为运行开关，但必须与 lifecycle 一致：active 才能为 true；candidate 不能通过普通 enabled 表单绕过激活；关闭 active 会进入 paused。

## Preview 与激活

```bash
uv run python -m app.cli sources preview <slug> --max-items 20 --no-persist
uv run python -m app.cli sources activate <slug> --confirm
```

Preview 不写 Item、不创建正式 CrawlRun，输出 fetch/parse、数量、三类状态分布、标题/日期/链接比例、拒绝/失败原因及最多 20 个样本。激活命令内部先执行 preview，并要求 Collector 已注册、无技术阻断、至少一条有效内容、标题/链接有效率至少 80%、无处理失败及明确 `--confirm`。结果写入 `last_preview_at`、`preview_item_count`、`preview_result` 和激活依据。

低频政府来源可以用受控 fixture、历史列表和人工证据证明解析能力，不能因当天无新内容误判。登录、验证码不会绕过；JavaScript 阻断不会通过引入 Playwright 解决。

## 更新选择

CLI 默认更新、Web 更新全部和 scheduler 只选择 active。显式 preview 可读取 candidate；显式普通更新 candidate 会失败。媒体可以 active，这只说明会采集行业线索，不意味着可以正式发布。
