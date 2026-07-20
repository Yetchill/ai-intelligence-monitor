# 运行设置与轻量定时更新

## 来源生命周期

调度触发与手工 update all 使用同一 active 来源选择。candidate 和 paused 永不被默认调度；目录同步不会把 paused 重新启用。active media 可被调度采集，但发布仍受 Verification、review 和 PublicationPolicy 控制。

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
数据库提交成功后才唤醒调度器；若提交已成功但进程内重载失败，页面返回明确的 503 提示，已保存
数据不会回滚。再次保存或重启应用会按持久化设置恢复。

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

首次读取只返回默认值而不写数据库；首次保存才按需创建唯一行。默认值为计划关闭、09:00、
每天、系统本地 IANA 时区。若操作系统只提供 `EST`、`CST` 等模糊缩写或无法提供可校验名称，
安全回退为 `UTC`。迁移不会创建设置行、执行计划或访问公网。

## 调度与互斥

`SchedulerService` 与 FastAPI 路由解耦，通过注入获得设置服务和共享更新执行服务：

```text
网页手动更新 ─┐
              ├→ UpdateExecutionService → UpdateLock → UpdatePipeline
定时更新 ─────┘
```

定时触发遇到手动更新时安全跳过且不创建虚假 CrawlRun；该次跳过不写
`last_scheduled_trigger_at`，也不会在同一分钟重试。实际取得锁后才写最近触发时间并进入流水线，
因此流水线构造、执行或提交失败均不会让同一计划时刻再次触发。定时更新持锁时网页请求沿用
409。锁由持有者凭据在 `finally` 释放。Pipeline 异常被记录后，循环继续等待下一个计划。定时
调用不传 `source_id` 或 `allow_disabled`，因此仍由现有流水线只选 enabled 来源，并创建
`trigger=scheduled` 的 CrawlRun。

锁仅在进程内共享。Web 进程中的网页与调度器使用同一实例；普通 CLI `update` 也复用同一执行
服务，但独立 CLI 进程无法与已运行的 Web 进程跨进程互斥。不要同时运行 Web 调度器和
`schedule run`。

## 时间和夏令时

持久化和比较使用 aware UTC datetime，页面按配置时区显示。下一次运行从当前时刻之后严格计算，
所以启动不会补跑过去的本地日历时刻。

夏令时采用保守策略：本地墙上时间不存在（春季跳时）时跳过该日；本地时间重复（秋季回拨）
时只选择较晚的第二次，避免执行两次。同一计划时刻写入 `last_scheduled_trigger_at` 后不会重复
触发。调度循环只在计划分钟内开始执行；事件循环阻塞、休眠或时钟前调后恢复时已经离开该分钟
的旧时刻会跳过，不补跑多个任务。时钟后调时会重新等待目标，并由最近触发时间阻止重复。
修改设置会唤醒旧等待并重新计算；关闭会取消未来触发。

应用关闭会取消正在执行的定时更新，流水线在已创建 CrawlRun 时尽力将其收尾为 `failed`，随后
释放更新锁、HTTP 资源和数据库连接；取消发生在 CrawlRun 创建前时不会产生记录。当前不支持
多进程或跨机器协调。
