# Orca

执行 Orca 命令前，遵守本文件。本机遇到的其他 Orca 坑在 `models.json` 的 `orca_notes`。

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

## 消息

1. `send` 必须带 `--subject`。正文含反引号或 `$(...)` 时先写进文件，再 `--body "$(cat <文件>)"`。
2. 给正在等 Worker 的 session 发 `send` 之后，再用 `terminal send --terminal <handle> --text "inbox 有 msg <id>，请不带 --types 读" --enter` 推一下；它的 `check --types` 会漏掉别的类型。
3. `run-use --id <run>` 把 Run 绑到执行者的终端，原先的 waiter 会以 `consumer_fenced` 退出。只有该 Run 的协调者执行它。
4. 被派发的 session 读自己的 inbox 用不带 `--run` 的 `check`；`ask` 也不带 `--run`。要派 Worker 时先 `run-create` 自己的 Run。
5. `ask` 默认不阻塞，发完结束回合；要在同一回合拿到答案用 `ask --resume <msg_id> --wait`。
6. 给已结算的 Worker `send` 会生成一个新的 follow-up Dispatch，返工用它。

## Worktree

1. `--worktree current` 绑的是主仓库的 Orca 文件夹上下文，在 worktree 目录下执行也一样。要让 session 在已有 worktree 里干活，用 `--worktree path:<绝对路径>`，或起来后让它 `cd` 到绝对路径做全部操作。
2. 新 worktree 用 `--worktree new-top-level --name <name>`。它可能从旧 commit 建，也没有被 gitignore 的依赖目录：Spec 要求开工先对齐基线、装依赖。

## 定时与自动续跑

1. `automations create --name <name> --trigger daily --time <HH:MM> --timezone <时区> --workspace path:<主工作区> --provider <agent> --extra-agent-args="--model <模型>" --missed-run-grace-minutes <分钟> --enabled --prompt "<prompt>" --json`。agent 和模型按 `models.json` `routing` 的"续跑 Conductor"项。automation 是 Orca 自己的调度器，机器恢复后按墙钟在宽限期内补跑一次。
2. 用现有工作区时不能带 `--setup`。`--reuse-session` 复用的是 automation 自己的旧 session，不是当前 session，不用它。
3. 建完用 `automations show --id <id>` 核对 `rrule`、`nextRunAt`、`enabled`；`automations runs --id <id>` 看每次的 `scheduledFor`（epoch 毫秒）和 `status`。
4. `daily` 每天都触发。只要一次就在用完后 `automations edit --id <id> --disabled`，id 以 `automations list` 里的为准。

## 判活与 429

1. transcript 静默不等于挂起。用 `terminal read --terminal <handle> --screen` 看渲染帧；默认模式会去掉 TUI 重绘，看不到错误。
2. 渲染帧里出现带 `retry-after` 的 429（如 `prefill_cap_refused`）是上游容量，不是账号额度。这时 `send` 和 `terminal send` 只把消息入队，退避结束后才执行；`terminal send --interrupt` 无效。
3. `worker-read` 用 `--dispatch` 指定对象，用 `--limit <n>` 限制条数。
