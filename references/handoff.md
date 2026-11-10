# 上下文交接

长会话换成新 session 时使用本文件。Conductor 和 Master 都适用。记忆靠交接文件，不靠旧对话。

1. 触发要两条都满足。上下文过长：被自动压缩过至少一次，或估计已过该模型上下文上限的一半。时机安全：没有改到一半的文件，自己的 commit 已 push，没有未回复的 `ask`，自己派的 Worker 都已结算并释放，接下来是等待或新阶段。只满足前一条时，先把手上的事做完。
2. 交接文件由旧 session 写，放在 Ticket 的 git 外目录这类持久位置，不放会话的临时目录。内容：身份（Run、Task、Dispatch、终端 handle）；硬约束的要点；现状（数字和完整绝对路径）；进行中的事；怎么等；未完成项（按顺序）；最终报告要求；坑。旧 transcript 的路径写进去，新 session 只按需 grep。
3. 新 session 只读交接文件、Ticket 和规则文件。模型按 `models.json` `routing`：以监督和等待为主的 session 用"续跑 Conductor"项。
4. Master 交接：
   1. Master 写交接文件，在子票进度里加一行"交接：<路径>"，然后 `send --type status --subject handoff_request`，正文是交接文件的绝对路径和正在跑的后台任务（pid、日志）。之后保持空闲。后台任务照跑。
   2. Conductor 用 `worker-start --spec "<身份段 + 读 <路径> 接手>" --worktree path:<工作区绝对路径>` 起新 Master。
   3. 新 Master 第一次 heartbeat 或 `check` 成功后，Conductor 关旧 Master 的终端。先起新、确认接上、再关旧。
5. Conductor 交接：
   1. 写交接文件，用 `agent launch` 在同一工作区起新 session，prompt 是"你是 Conductor，读 <交接文件绝对路径> 接手"。
   2. 一个 Run 只能有一个 waiter。旧 session 先停自己的 waiter；新 session `run-use`、读 inbox、挂上 waiter。
   3. 旧 session 用 `terminal read` 确认新 session 已挂上 waiter，才算交接完成。之后新 session 关旧终端。旧 session 不再 `run-use`。
6. 新 session 没有确认接上之前，不向用户报交接完成。接上后告诉用户一句：谁换的、交接文件路径、新 session 的 handle。
