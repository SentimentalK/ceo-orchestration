# Audit

用户说"做 audit"时按本文件执行。目标：评估某版规则（本仓库某个 commit）之后，Conductor / Master / Worker 是否按规则工作、花了多少。你是审计方，不是 Conductor；不派发、不改 Orca 状态。

## 1. 定窗口

- 用户给了 commit 或时间：`--since` 用它；给了两个就再加 `--until`。
- 用户只说"最近这次改动之后"：用本仓库最新一个改规则的 commit（`git log --oneline -10`）。
- 要前后对比：跑两次，`--since <上一个 commit> --until <该 commit>` 和 `--since <该 commit>`。
- `models.json` 不进 git，模型配置变更没有 commit；用户说"某次换模型之后"时用时间。

## 2. 取数

先跑 `python3 audit/lint.py`，把规则文本的问题记进报告。

`tools/` 里的检查可以对历史重放，得到不靠判断的遵守率：`tools/ticket_check.py` 逐个跑窗口内归档的票，`tools/spec_check.py` 逐个跑从 transcript 首条消息里取出的 Spec。

```bash
python3 audit/audit.py --since <commit|ISO 时间> [--until <commit|ISO 时间>] > <scratch>/audit.json
```

只读，几秒。输出一个 JSON，先只看 `window`、`summary`、`flags`，不要整份读入。

| 字段 | 内容 |
| --- | --- |
| `summary` | 派发数（按角色 / 状态 / agent+模型）、重试数、消息数（heartbeat、question、worker_done…）、token（按角色、按 agent+模型）、无 transcript 数、未释放终端数 |
| `flags` | 机械可判的问题：`depth>=3`（Worker 再派发）、`heartbeat_too_frequent`（Master 心跳中位间隔 < 30 分钟，master R12.1）、`failed`、`terminal_not_released` |
| `conductor_sessions` | Conductor 的会话路径（Claude 或 omp）、模型、token（整个会话，可能含窗口外工作） |
| `dispatches` | 每个 Master / Worker：标题、agent、请求 / 生效 / 实际看到的模型、状态、耗时、心跳、提问数、transcript 路径、token |

拿不到的就是 `null` 或空：Cursor 本地没有 token；旧 `opencode` agent 找不到 transcript；Orca 未记录的模型以 transcript 里看到的为准（`model_seen`）。如实写"无数据"，不估。

## 3. 判断（需要读 transcript）

只打开需要的 transcript，用 `grep` / `jq` 定位，不整份读。Claude transcript 是 JSONL，工具调用在 `message.content[].type == "tool_use"`。omp transcript 也是 JSONL，消息在 `type == "message"` 的行，工具调用是 `message.content[].type == "toolCall"`（`name` 为 `bash` / `read` / `edit` / `write`）。各 agent 的 transcript 位置见 `models.json` 的 `agents`。

| 查什么 | 规则 | 怎么查 |
| --- | --- | --- |
| Conductor 自己干活（写代码、跑实验、逐行读 diff） | conductor C1.4 | Conductor transcript 里 `Edit` / `Write` 工具调用（Ticket / 记忆仓库以外）、跑训练或采集的 `Bash` |
| Master 自己实现却没有声明，或 Conductor 没按自实现核验 | master R4.10，conductor C5.8 | Master transcript 里对目标仓库的写入；对照它派的 Worker 数、`worker_done` 正文有没有"自实现"、Conductor 有没有看 diff 范围并跑验收 |
| Master 用宿主 subagent | master R1.3 | Master transcript 里宿主的 subagent 工具调用（Claude 是 `Agent` / `Task`） |
| Spec 缺段或与规则相反 | conductor C3.2、C3.3 | Master 的首条 user 消息（Spec）：第一句是否指向 `roles/master.md`，七段是否齐，有没有与 master.md 相反的要求 |
| Conductor 合并分支、解冲突 | conductor C1.4、C4.11 | Conductor transcript 里的 `git merge`、`git commit` 和对目标仓库的写入 |
| 界面改动没给用户看就合并 | conductor C1.7 | 合并时间对照 Conductor 给用户发截图或预览的时间 |
| 记录缺失 | conductor C2.2、C2.4、C5.5，master R7 | 票有没有验收段；用户做取舍后 `decision/` 有没有新条目；待审核项是不是清单；写回有没有 SHA |
| L 级没走设计检查点 | conductor C3.7 | Master 的 `question` 数为 0 且 Spec 标规模 L |
| 派发模型不在 `routing` 里或 effort 不对 | master R4.4，`models.json` | `dispatches[].agent / model_*` 对照 `models.json` |
| 没核验就 release、关票 | conductor C5、C4.10 | Conductor transcript 里 `worker-release` 之前有没有 `merge-base --is-ancestor`、CI 查询、复跑测试 |
| 汇报不合契约 | conductor C7 | Conductor 发给用户的最后几条汇报 |
| Worker 越权（做设计、改白名单外文件、派发） | spec.md、master R5 | `flags` 的 `depth>=3`；Master 的 Review 记录 |
| 坑有没有回写、写对地方 | master R5.8 | Worker `worker_done` 里的"坑："与 `models.json` 的 `notes` / `orca_notes`；有没有混进目标仓库的细节 |

样本多时：所有 Master 和 Conductor 都查；Worker 只查 `flags` 里的和失败 / 重试的。

## 4. 报告

回复用户，同时存一份到 `audit/reports/<YYYY-MM-DD>-<since>.md`（不进 git，供以后对比）：

1. 一句结论：这版规则下系统是否按设计运转，最大的问题是什么。
2. 数字表：派发数、按角色和模型的分布、成功 / 失败 / 重试、耗时、token（按角色、按模型）。token 说明：cache read 占大头；Claude 走订阅，token 不是账单；没有数据的写"无数据"。有前后两个窗口时并排对比。
3. 问题清单：每条写规则编号、证据（transcript 路径 + 行或 dispatch ID）、影响。
4. 建议的规则修改：写成要改哪条、怎么改的草案。不直接改规则，等用户决定。

没有记录不等于没做：用户会在体系外测试和决定。遗留、未测、未决这类结论在报告里标"无记录"，并先和用户核对。

## 5. 记发现

开始前读 `audit/findings.md`，看以前的发现这次是否重现、是否被推翻。报告写完并和用户核对后，把新的发现按该文件的字段追加进去；已有的发现重现时，在原条下加一行"后续"，不新开一条。
