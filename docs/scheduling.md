# 运行设置与轻量定时更新

## 能力与边界

阶段七为本地单进程应用提供内置定时更新。它不是系统服务、守护进程或分布式调度器，不使用
Celery、Redis、消息队列或任意 cron 字符串。应用必须保持运行，计划才会触发；电脑关机、休眠
导致应用不可运行或应用退出期间错过的任务全部跳过。再次启动只计算下一次未来运行，不补跑
历史任务。

Windows 计划任务、桌面启动器、系统托盘和 exe 打包不在本阶段实现。

## 网页配置

打开 `/settings`，可设置定时开关、`HH:MM` 执行时间、周一至周日、IANA 时区，并查看下一次
计划运行、最近一次计划触发和当前状态。保存使用 POST。任一字段无效时返回 400，事务不会改写
原设置。关闭后立即取消未来等待；开启或修改后立即按新设置计算未来时间。页面不接受 cron。

## CLI

CLI 与网页使用同一个 `ScheduleSettingsService`：

```bash
uv run python -m app.cli schedule show
uv run python -m app.cli schedule enable --time 09:00 --days mon,tue,wed,thu,fri
uv run python -m app.cli schedule enable --time 09:00 --days mon,tue,wed,thu,fri --timezone Asia/Shanghai
uv run python -m app.cli schedule disable
uv run python -m app.cli schedule run
```

`schedule run` 是开发验证用前台进程，要求计划已开启，按 `Ctrl+C` 会停止调度器并释放资源。它
不会安装全局命令、创建守护进程或注册系统服务。不要与 Web 进程同时运行两个调度器；单进程
唯一性只在各自进程内成立。

## 持久化

Alembic revision `f2c7a93d1b44` 新增单例 `schedule_settings` 表和 `crawl_runs.trigger`：

- `schedule_enabled` 默认关闭；
- `schedule_hour` / `schedule_minute` 受数据库检查约束；
- `schedule_days_mask` 是七位星期位图，范围 1–127，不保存通用 JSON 或表达式；
- `timezone` 是经 `zoneinfo.ZoneInfo` 校验的 IANA 名称；
- `updated_at` / `last_scheduled_trigger_at` 以 UTC 保存；
- `trigger` 为 `legacy_manual`、`manual_web`、`manual_cli` 或 `scheduled`。

首次读取创建默认行：计划关闭、09:00、每天、系统本地 IANA 时区。若操作系统无法提供可校验
名称，安全回退为 `UTC`。迁移不会创建或执行计划，也不会访问公网。

## 调度与互斥

`SchedulerService` 与 FastAPI 路由解耦，通过注入获得设置服务和共享更新执行服务：

```text
网页手动更新 ─┐
              ├→ UpdateExecutionService → UpdateLock → UpdatePipeline
定时更新 ─────┘
```

定时触发遇到手动更新时安全跳过且不创建虚假 CrawlRun；定时更新持锁时网页请求沿用 409。锁在
`finally` 释放。Pipeline 异常被记录后，循环继续等待下一个计划。定时调用不传 `source_id` 或
`allow_disabled`，因此仍由现有流水线只选 enabled 来源，并创建 `trigger=scheduled` 的 CrawlRun。

## 时间和夏令时

持久化和比较使用 aware UTC datetime，页面按配置时区显示。下一次运行从当前时刻之后严格计算，
所以启动不会补跑过去的本地日历时刻。

夏令时采用保守策略：本地墙上时间不存在（春季跳时）时跳过该日；本地时间重复（秋季回拨）
时只选择较晚的第二次，避免执行两次。同一计划时刻写入 `last_scheduled_trigger_at` 后不会重复
触发。修改设置会唤醒旧等待并重新计算；关闭会取消未来触发。当前不支持多进程或跨机器协调。
