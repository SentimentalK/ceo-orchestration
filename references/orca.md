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
