# ceo-orchestration

基于 Orca 的三层编排：用户只和 Conductor 对话；Conductor 经 Orca 派发 Master；Master 经 Orca 派发 Worker。本仓库是一个 skill（`SKILL.md` = `/conductor` 入口），所有规则、本机配置和工具都在这里。

本文件只用于安装和维护本仓库。你若是 Orca 派发的 session，按你的 Spec 执行，不按本文件做事。

## 安装

1. 先确认用户在用 Orca（`orca status` 或 `orca-ide status` 可用）。不用 Orca 时不要安装：告诉用户本仓库依赖 Orca 的 orchestration，没有 Orca 无法运行。
2. 确认 Orca 的 `orchestration` skill 已装（`orca skills installed` 里有）；没有就 `orca skills install --skill orchestration`。
3. 把本仓库 clone 到一个固定位置，例如 `~/codes/ceo-orchestration`。
4. 按 Orca 的 skill 布局链接，不复制：
   - `ln -s <clone 路径> ~/.agents/skills/conductor`
   - `ln -s ../../.agents/skills/conductor ~/.claude/skills/conductor`
   其他不读 `~/.agents/skills` 的 agent 若要当 Conductor，只给它放一层指向本目录 `SKILL.md` 的薄引用。
5. `models.json` 不存在时：`cp models.example.json models.json`，再和用户一起按本机订阅填写。精确 ID 用 `agents.<agent>.list_models` 的命令查，不凭记忆写。
6. 验证：`orca skills installed` 里出现 `conductor`。用法：在 Orca 里开一个 Claude session，输入 `/conductor <启动输入>`。

## 布局

| 路径 | 内容 | git |
| --- | --- | --- |
| `SKILL.md` | `/conductor` 入口和身份门 | 是 |
| `roles/conductor.md` | Conductor 规则 | 是 |
| `roles/master.md` | Master 规则 | 是 |
| `references/` | 按需读取的规则：Spec、Review、Orca、断线、交接、夜间休眠、实验类工作；`claude-*.md` 只适用于 Claude | 是 |
| `models.example.json` | 模型配置模板 | 是 |
| `models.json` | 本机订阅与偏好（模型 ID、effort、限制）、各角色的派发顺序、agent 和 Orca 的坑 | 否 |
| `tools/` | 规则引用的只读检查：`spec_check.py`（派发前查 Spec）、`verify.py`（commit 在目标分支、CI 通过、改动范围）、`ticket_check.py`（关票前查票）；`claude_usage.py` 读 Claude 订阅额度 | 是 |
| `audit/` | 审计说明（`README.md`）和只读脚本（`audit.py` 取数，`lint.py` 查规则文本）；用户说"做 audit"时读 `audit/README.md` | 是 |
| `audit/findings.md` | 历次审计的发现（日期、模型配置、预期与实测）。只在做 audit 或改规则时读，其他情况忽略 | 是 |
| `audit/reports/` | 历次审计报告 | 否 |

Worker 没有规则文件：它只读 Master 写的 Spec（模板在 `references/spec.md`）。

## 改规则

规则文件是 `SKILL.md`、`roles/`、`references/`。它们被每个 session 读，所以只写现行做法。

1. 写目标、不变量和什么算证据，不写步骤。只为弥补某类模型的不足而存在的做法，放进 `references/` 并写明适用条件。
2. 正文不写日期、项目或 Ticket 编号、事故经过、单次测得的数字、用户原话。这些写进 `audit/findings.md`；commit message 引用发现的编号（如 `F-006`）。
3. 更正就地改写，不保留旧条，不并列两个互相修正的条款。编号顺延，不用 `3a` 这类补丁编号；改编号时同步改引用它的地方。
4. 同一件事只写一处。Orca 命令的事实写 `references/orca.md`；模型 ID、时区、时刻这类本机配置写 `models.json`。
5. `roles/` 和通用 reference 不假设某个 agent。只适用于一个 agent 的做法写进以它命名的 reference（如 `references/claude-usage.md`）或 `models.json` 的 `agents`；只适用于一类工作的写进对应 reference（如 `references/experiments.md`）。
6. 一次事故不直接变成规则。先记成发现；重复出现或后果严重时再改规则，并优先改成 `tools/` 里的检查或审计检查项。工具只做只读检查、不过就非零退出，规则里引用它；不写替 session 做决定的工具。
7. 被派发的 session 和 Conductor 不改规则文件。规则在维护本仓库的 session 里改，改完跑 `python3 audit/lint.py`，由用户看过再 commit。
