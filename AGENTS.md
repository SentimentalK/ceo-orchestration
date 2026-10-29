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
| `references/` | Spec、Review、Orca 规则 | 是 |
| `models.example.json` | 模型配置模板 | 是 |
| `models.json` | 本机订阅与偏好（模型 ID、effort、坑）、agent 传参方式、派发顺序 | 否 |
| `audit/` | 审计说明（`README.md`）和只读取数脚本；用户说"做 audit"时读 `audit/README.md` | 是 |
| `audit/reports/` | 历次审计报告 | 否 |

Worker 没有规则文件：它只读 Master 写的 Spec（模板在 `references/spec.md`）。
