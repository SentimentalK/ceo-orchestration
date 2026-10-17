# Autonomous Engineering Master Skill

本仓库是通用、全中文的 **Autonomous Engineering Master Skill**。

上层 Architect 与用户确定目标、技术路线、架构约束、Roadmap 和 High-level Tickets 之后，本地 Agent 阅读 [`SKILL.md`](SKILL.md)，在获准的 Parent / Child Ticket 范围内担任 Autonomous Master：补全详细设计，用 Orca 编排 Worker，独立验收，并连续推进下一项获批任务。

这不是 LongCat Gateway，不是调度服务，也不是默认亲自编码的 Worker。本仓库不实现 Runtime、数据库或任务状态机。

## 入口

唯一主入口是 [`SKILL.md`](SKILL.md)。`references/` 只在主入口写明的场景加载。Orca 命令以本机已安装的 orchestration Skill 为准，不在本仓库复制。

## 使用

启动本地 Agent 时同时提供：

- 阅读并遵循本仓库 `SKILL.md`。
- 一个 Parent Ticket。
- 允许读取的 Child Ticket 列表。
- 本轮允许执行的 Child Ticket 列表。
- 目标代码仓库。
- 必要的架构与安全约束。

可读与可执行是两项独立授权。未列入的 Ticket 不得读取或执行。
