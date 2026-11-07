# Orca

执行 Orca 命令前，遵守本文件。

## 命令来源

1. 在 Linux 上，Orca 受管终端以外的环境使用 `orca-ide`。不运行 `/usr/bin/orca`。
2. 第一次执行命令前，运行 `orca-ide skills get orchestration` 读取紧凑手册。
3. 只使用手册中有的 flag。手册不够用时，按手册的指引加载对应的 reference。
4. 选定的可执行文件失败时，记录原始错误，然后按 roles/master.md R8 结束。不换成另一个二进制文件。

## 结构

1. 一个目标 Ticket 对应一个 Run。不新建 Run 来绕过失败。
2. 一个任务对应一个 Task。一次尝试对应一个 Dispatch。
3. 只为真实存在的顺序关系设置依赖。依赖链不超过 3 到 4 层。
4. 合法的 `worker_done` 会结算 Task。结算后不再补写完成状态。
5. Worker 的普通提问用 `ask` 和 `reply` 处理，不建 Gate。

## 安全

1. 状态变更命令只执行一次。没有收到响应时，先只读检查，不重发。
2. `check` 超时或返回空结果只是检查点，不代表失败。
3. 只有确认 `failed` 或 `stopped` 后，才能重试同一个 Task。重试时指向旧的尝试。
4. 状态是 `unverifiable` 或缺席时，不执行 stop、retry 或 release。
5. Orca 熔断触发后，按 roles/master.md R8 结束。

## 终端

1. 每个已结算的 Worker 终端只有三种去向：复用于返工、保留、释放。
2. 只在结算被接受之后释放终端。
3. 结束 session 前，清点并处置所有终端。

## 定时与自动续跑（automations）

1. `orca-ide automations create --name <name> --trigger daily --time 08:05 --timezone America/New_York --workspace path:<主工作区> --provider omp --extra-agent-args="--model opencode-go/deepseek-v4.1-flash" --missed-run-grace-minutes 240 --enabled --prompt "<读交接文件 + run-use <run> + 按顺序派票>" --json`。CronCreate 不可用；automation 是 Orca 自己的调度器，机器恢复时按墙钟补跑。
2. 现有工作区模式**不能带 `--setup`**；omp 的 extra args 只接受 `--model`（`--effort` 被拒）。`--reuse-session` 复用 automation 自己的 session，不是当前 Conductor，不要用。
3. `automations show --id <id>` 核对 `rrule` / `nextRunAt` / `enabled`；`automations runs --id <id>` 看每次 `scheduledFor` / `status`（`dispatched` 即已起 session）。`automations list` 的 id 才是关闭时用的 id（create 输出的 id 可能因重建而变）。
4. 每天触发：只想要一次就 `automations edit --id <id> --disabled`，否则每天多一个 Conductor 抢同一个 Run。
5. 新 Conductor 起来后会 `run-use`，把旧 session 的 waiter 以 `consumer_fenced` 顶掉——正常。旧 session 此后不再 `run-use`。
6. 排查调度器：`orca-ide automations runs --id <id>` 的 `scheduledFor` 用 epoch 毫秒，直接和 RTC 闹钟 epoch 对照。

## 判活与 429

1. transcript 静默 ≠ 挂起。先 `terminal read --terminal <handle> --screen` 看渲染帧；默认模式 strip 掉 TUI 重绘，看不出错误。
2. `prefill_cap_refused` / `retry-after-ms=30000` 是上游 cell 容量，不是账号额度；`send` + `terminal send` 只把消息入队（屏幕 `Steering · 1`），退避期内不执行，18 分钟内可自动恢复。`terminal send --interrupt` 无效；进程活着就不 stop / retry。
3. `orchestration send` 必须带 `--subject`，否则 `Missing required --subject`。
