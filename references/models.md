# 本机模型注册表

在 Step 3 选择 Worker 的 Agent/Model 时读取。用 `grep` 只取需要的行，不必通读。

- 这是本机快照，不是通用前提。调用者钉死的模型优先于本表。
- 本表与实时列表冲突时，以实时列表为准：`agy models`、`opencode models --verbose`、`ORCA account list --json`（额度用量）。
- 只调用 `opencode-go/*`（订阅池）。不要用 `opencode/*`（按量 Zen 通道）。
- 同组内行序即优先级，能力由高到低。免费模型只作最后兜底。
- 核验日期：`2026-10-17`。

## 检索

```bash
cd <本 Skill 目录>
grep '^\[ROLE:WORKER_' references/models.md        # 全部编码 Worker，按 T1 → T2 → 免费
grep '^\[ROLE:WORKER_T1\]' references/models.md    # 主力编码
grep '^\[ROLE:FRONTIER\]' references/models.md     # 攻坚 / 独立 Review
grep '^\[ROLE:.*vision:yes' references/models.md   # 能看图的
grep '^\[ROLE:DO_NOT_CALL\]' references/models.md  # 禁止自动调用
```

## 配额池

| Agent | 池 | 模型 | 说明 |
| --- | --- | --- | --- |
| antigravity | Gemini 4 Argon（周限额） | `gemini-4-argon-*` | 独立池 |
| antigravity | Claude and GPT（5h + 周） | `claude-*`、`gpt-oss-*` | 共享池，只用 Opus |
| antigravity | Gemini Models（5h + 周） | `gemini-3.8-flash-*` | 独立池，额度充裕 |
| opencode | OpenCode Go 订阅（5h / 周 / 月） | `opencode-go/*` | 按 token 单价消耗同一池 |

Antigravity 的 effort 写在模型 ID 后缀里（`-low/-medium/-high`）。OpenCode 的 effort 见 `effort:` 列；为 `-` 的模型不要传 effort。

## 注册表

```text
# === MASTER：启动 Autonomous Master 的候选 ===
[ROLE:MASTER]          | pref:1 | agent:antigravity | model:gemini-4-argon-high                  | vision:yes | pool:argon
[ROLE:MASTER]          | pref:2 | agent:antigravity | model:claude-opus-5-5-high                  | vision:yes | pool:claude_gpt
[ROLE:MASTER]          | pref:3 | agent:antigravity | model:gemini-4-argon-medium                | vision:yes | pool:argon

# === FRONTIER：困难实现攻坚、独立 Review（与实施者不同的模型）===
[ROLE:FRONTIER]        | pref:1 | agent:antigravity | model:claude-opus-5-5-high                  | vision:yes | pool:claude_gpt
[ROLE:FRONTIER]        | pref:2 | agent:opencode    | model:opencode-go/grok-4.7                  | vision:yes | cost:$2/$6      | effort:low..xhigh
[ROLE:FRONTIER]        | pref:3 | agent:opencode    | model:opencode-go/kimi-k3                   | vision:yes | cost:$3/$15     | effort:max
[ROLE:FRONTIER]        | pref:4 | agent:opencode    | model:opencode-go/qwen3.8-max               | vision:yes | cost:$2/$6      | effort:low,medium,xhigh

# === WORKER_T1：日常编码默认首选 ===
[ROLE:WORKER_T1]       | pref:1 | agent:opencode    | model:opencode-go/step-5-preview            | vision:yes | cost:$1/$2.7    | effort:low..high
[ROLE:WORKER_T1]       | pref:2 | agent:opencode    | model:opencode-go/glm-5.3                   | vision:no  | cost:$1.4/$4.4  | effort:low,high,max
[ROLE:WORKER_T1]       | pref:3 | agent:opencode    | model:opencode-go/glm-5.2                   | vision:no  | cost:$1.4/$4.4  | effort:high,max
[ROLE:WORKER_T1]       | pref:4 | agent:opencode    | model:opencode-go/deepseek-v4-pro           | vision:no  | cost:$0.66/$1.98| effort:high,max | out:384K
[ROLE:WORKER_T1]       | pref:5 | agent:opencode    | model:opencode-go/kimi-k2.7-code            | vision:yes | cost:$0.95/$4   | effort:-        | ctx:256K

# === WORKER_T2_FLASH：并发、写测试、脚本、T1 降级 ===
[ROLE:WORKER_T2_FLASH] | pref:1 | agent:opencode    | model:opencode-go/glm-5.3-flash             | vision:yes | cost:$0.15/$0.5 | effort:-
[ROLE:WORKER_T2_FLASH] | pref:2 | agent:opencode    | model:opencode-go/deepseek-v4.1-flash       | vision:yes | cost:$0.15/$0.6 | effort:low,high,max
[ROLE:WORKER_T2_FLASH] | pref:3 | agent:opencode    | model:opencode-go/qwen3.8-flash             | vision:yes | cost:$0.15/$0.47| effort:low,medium,xhigh
[ROLE:WORKER_T2_FLASH] | pref:4 | agent:opencode    | model:opencode-go/gpt-6-luna                | vision:yes | cost:$0.1/$0.5  | effort:none..max
[ROLE:WORKER_T2_FLASH] | pref:5 | agent:opencode    | model:opencode-go/claude-haiku-5-5          | vision:yes | cost:$0.1/$0.5  | effort:low..max

# === WORKER_VISION：看图 / 多模态解析，独立池，不占 Argon/Opus ===
[ROLE:WORKER_VISION]   | pref:1 | agent:antigravity | model:gemini-3.8-flash-high                 | vision:yes | pool:gemini
[ROLE:WORKER_VISION]   | pref:2 | agent:antigravity | model:gemini-3.8-flash-medium               | vision:yes | pool:gemini

# === WORKER_FREE：付费池耗尽后的最后兜底 ===
[ROLE:WORKER_FREE]     | pref:1 | agent:opencode    | model:opencode-go/longcat-2.5-preview-free  | vision:yes | cost:$0         | effort:low..high
[ROLE:WORKER_FREE]     | pref:2 | agent:opencode    | model:opencode-go/beam-free                 | vision:no  | cost:$0         | effort:low..max

# === DO_NOT_CALL ===
[ROLE:DO_NOT_CALL]     | agent:antigravity | model:claude-sonnet-5-5-*                  | reason:与 Opus 共池，只调 Opus
[ROLE:DO_NOT_CALL]     | agent:antigravity | model:gpt-oss-120b-medium                  | reason:与 Opus 共池
[ROLE:DO_NOT_CALL]     | agent:opencode    | model:opencode-go/gemini-4-argon-contributor | reason:$4/$20，Argon 走 antigravity
[ROLE:DO_NOT_CALL]     | agent:opencode    | model:opencode-go/longcat-2.0              | reason:收费旧版，已被免费 2.5 取代
[ROLE:DO_NOT_CALL]     | agent:opencode    | model:opencode/*                           | reason:按量 Zen 通道，统一用 opencode-go
```

未排序（池里存在，能力未核实，不自动调度）：`gpt-5.6-luna`、`qwen3.7-plus`、`minimax-m3`、`mimo-v2.5*`、`mimo-v2.6-*`、`hy3`、`hy4-preview`、`space-bunny`、`muse-spark-*-contributor`。需要使用时先核实，再写入上表。
