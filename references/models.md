# Worker 模型

选择 Worker 模型时使用本文件。只调用本表中的模型。每组内按行序优先。

## Plan

| Plan | Agent | 模型 |
| --- | --- | --- |
| OpenCode Go | opencode | `opencode-go/*` |
| Claude Max | claude | `claude-haiku-5-5`、`claude-sonnet-5-5`、`claude-opus-5-5` |
| Antigravity Gemini | antigravity | `gemini-3.8-flash-*`、`gemini-4-argon-*` |
| Antigravity Claude（用户报告 2026-10-25：额度小，约 2 h 重置；走 Google 计划，不占 Claude Max） | antigravity（CLI `agy`） | `claude-opus-5-5-{low,medium,high}`、`claude-sonnet-5-5-{low,medium,high}` |

一个 Plan 额度用完时，跳过该 Plan 的所有模型。
Claude Max 与 Master 共用额度。

## 优先级

| 用途              | 顺序                                                                                                                                |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| 编码、测试、脚本        | `opencode-go/deepseek-v4.1-flash` → `opencode-go/glm-5.3-flash` → `gemini-3.8-flash-high`→ `claude-haiku-5-5` |
| 看图              | `claude-sonnet-5-5` → `claude-haiku-5-5` → `gemini-3.8-flash-high`（Gemini 额度 2026-10-18 用尽；8 图对比 Sonnet 区域 F1 0.78 vs Gemini 0.82 vs Haiku 0.72） |
| 困难实现、高风险 Review | `claude-opus-5-5` → `claude-sonnet-5-5`                                                                                                |
| 自主 Worker（AGENT.md R4.8，带设计） | `claude-sonnet-5-5` → `claude-opus-5-5`；与 Master 共用额度，只在能省 Master 注意力时用 |
| 兜底              | `opencode-go/longcat-2.5-preview-free` → `opencode-go/beam-free` |

Effort：`claude` 用 `--effort`；`agy` 的档位写在模型 ID 后缀中，print 模式必须 `-p='<prompt>'`（`-p` 后直接跟 flag 会把 flag 当 prompt），`--output-format json` 带 usage；`gemini-3.8-flash-*` 写在 ID 后缀中；`opencode` 不传。
