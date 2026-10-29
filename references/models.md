# Worker 模型

选择 Worker 模型时使用本文件。只调用本表中的模型。每组内按行序优先。

## Plan

| Plan | Agent | 模型 |
| --- | --- | --- |
| OpenCode Go | opencode | `opencode-go/*` |
| Claude Max | claude | `claude-haiku-5-5`、`claude-sonnet-5-5`、`claude-opus-5-5` |
| Cursor（用户 2026-10-28：订阅分两类模型，Grok 自家的与 other；other 里可跑 GLM） | cursor | Grok 系列、other 中的 GLM（具体 id 以 `--model` 可用列表为准） |
| ~~Antigravity（Google 会员 2026-10-28 到期，不再可用）~~ | — | — |

一个 Plan 额度用完时，跳过该 Plan 的所有模型。
Claude Max 与 Master 共用额度。

## 优先级

| 用途              | 顺序                                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| 编码、测试、脚本        | **`opencode-go/glm-5.3-flash`（主力，用户 2026-10-28 定）** → Cursor（other 里的 GLM，或 Grok）→ `claude-haiku-5-5` |
| 看图              | `claude-sonnet-5-5` → `claude-haiku-5-5`（Gemini 已不可用；8 图对比 Sonnet 区域 F1 0.78 vs Gemini 0.82 vs Haiku 0.72） |
| 困难实现、高风险 Review | `claude-opus-5-5` → `claude-sonnet-5-5`                                                                                                |
| 自主 Worker（AGENT.md R4.8，带设计） | `claude-sonnet-5-5` → `claude-opus-5-5`；与 Master 共用额度，只在能省 Master 注意力时用 |
| 兜底              | `opencode-go/longcat-2.5-preview-free` → `opencode-go/beam-free` |

Effort：`claude` 用 `--effort`；`agy` 的档位写在模型 ID 后缀中，print 模式必须 `-p='<prompt>'`（`-p` 后直接跟 flag 会把 flag 当 prompt），`--output-format json` 带 usage；`gemini-3.8-flash-*` 写在 ID 后缀中；`opencode` 不传。


## 2026-10-28 用户更新
- Worker 编码主力 = OpenCode 的 `opencode-go/glm-5.3-flash`（agent `opencode`）。Google 会员已到期，Antigravity 的 Gemini / Claude 池都不再用。第二梯队 = Cursor（agent `cursor`），订阅内两类模型：Grok 自家的，和 other（可继续用 GLM）。兜底 = `claude-haiku-5-5`（与 Master / Conductor 共用 Claude Max，留 20 % 余量）。
- 教训（2026-10-25）：经 Orca 起的 OpenCode worker 曾 15 分钟零模型调用。Master 派 OpenCode worker 后 10 分钟内核实它有输出（文件变动或 transcript），没有就 stop 并按本表下一档重派；Orca 的 OpenCode 模型选择要求已有 worktree + 可用模型。
