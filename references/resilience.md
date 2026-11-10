# 断线与额度耗尽

请求失败（429、rate limit、API Error），或 Master 没有动静时，遵守本文件。Orca 命令的细节见 `references/orca.md`。

1. 额度耗尽的信号是请求失败。不另设周期自检：靠 waiter 超时检查点，以及 Orca 在额度恢复后的唤醒。
2. 每个检查点（waiter 超时、被唤醒后）看四件事：waiter 是否在挂，不在就重挂；`worker-list --run` 里每个 live / ready Dispatch 的 liveness；对 `stale_status` / `unverifiable` 的 Dispatch，用 `worker-read` 看最后一条 agent 消息和它的时间；输出目录、日志和计算资源是否仍在推进。
3. 判活看终端的渲染帧（`orca.md`"判活与 429"），不只看 transcript。transcript 静默可能是挂起，也可能只是在重试。
4. Master 的最后一条消息是 API Error / rate limit / 429 / Connection lost，且之后没有动作：这是断线闲置，不是 stop 条件。按序处置，每步等 5 分钟：
   1. `orchestration send --to dispatch:<id>` 发 Follow-up，写清它已完成到哪（commit、CI、写回）和下一步。
   2. 仍无新消息：`terminal send` 往它的终端输入同一段 Follow-up。
   3. 仍无动作，且进程已退出：先 `worker-read` 确认没有 worker_done，再按 `references/handoff.md` 第 4 条起新 Master 接手。进程仍在但不动：等下一个检查点，不 stop。
5. 终端显示上游容量类的 429（带 `retry-after`）时，它在自动退避。只发一次 Follow-up 入队，不反复推、不重启；退避结束后队列里的消息会被执行。
6. 任何一步都不 release、不 retry 状态未确认的 Dispatch。
7. 区分账号额度与网络。Conductor 和所有 Master 同时 429：账号额度，不新开 Master、不换模型绕过，等重置。所有 Master 同时 stale 而本机断网：网络恢复后统一推一遍。
8. 每次推醒，在汇报里写一句：谁、停了多久、断在哪、怎么续上的。
