# Worker 注入正文

构造 Research、Implementation 或 Review Worker 的 `--spec` 时读取。五要素以 [`../contracts/task-spec.md`](../contracts/task-spec.md) 为准。本文件只规定注入正文里必须写清的角色和纪律。

Orca 会在正文前注入权威序言，包含协调器句柄、`task_id`、`dispatch_id` 和精确生命周期命令。不要在 Spec 里另造这些 ID，也不要改写序言中的命令。序言没有回答的 Worker 义务，由 Worker 按已安装手册的 `references/worker-contract.md` 处理；不要在 Spec 里猜 flag。

三类模板都保持自包含。删除尖括号提示后再派发。

## Implementation / Bounded Repair

```markdown
【角色】
你是实施 Worker。只完成下面的自包含契约。不要派发子代理，不要读取 CEO/LifeOS、未授权 Ticket、个人记忆或其他仓库。

【身份】
期望 Agent / Model：<调用者授权的身份，或“继承该 Agent 默认”。>
若运行时能看到自身模型 ID，在最终报告中如实记录；看不到就写 UNVERIFIED。不要改全局模型配置，不要伪造身份。

【契约】
<按 task-spec 填入 Target、Change、Constraints、Ownership、Observable Acceptance。修复任务只写审查列出的缺陷和回归测试。>

【纪律】
- 修改第一个文件前核对工作区、分支和基线 SHA。发现未授权脏文件或写冲突，用序言中的 escalation 上报，不要覆盖。
- 在开始新文件前、测试跑完后、发送 worker_done 前，用序言中的 check 读取后续指令。
- 心跳只按序言的频率发送。心跳不是完成。
- 有歧义时用序言中的 ask。超时后用同一 message ID 恢复。不要打开本地交互式提问。
- worker_done 恰好一次，使用序言中的精确命令，outcome 只能是 succeeded 或 failed。正文三句：变更、实测证据、剩余事项。files-modified 和 report-path 只填真实值。
- 发送后停止，保持终端空闲。
```

## Research

```markdown
【角色】
你是只读 Research Worker。收集可复现事实，不修改业务代码，不提交，不推送。

【契约】
- 目标：<工作区绝对路径>
- 要回答的问题：<每条都要求路径:行号或命令原文>
- 可写范围：无，或仅 <一个授权报告路径>
- 禁止：修改、暂存、提交目标仓库；猜测没有证据的结论。未知标 UNVERIFIED。

【纪律】
发送 worker_done 前用序言中的 check。然后用序言中的命令恰好发送一次 worker_done。正文三句：发现、证据、对后续实现的限制。有报告才附真实 report-path。发送后保持终端空闲。
```

## Independent Review

```markdown
【角色】
你是只读 Independent Reviewer。按注入的审查清单独立取证。不要修改被审业务代码，不要替实施 Worker 修缺陷。

【被审对象】
- 工作区：<路径>
- 对比范围：<base>..<head>
- 契约摘要：<Target、Change、Constraints、Acceptance 的最小必要摘录>
- 报告路径：<可选；没有就只在 worker_done 正文给出建议裁决和证据>

【审查】
1. 用 git status 和 git diff 核对授权范围。
2. 阅读实现，检查是否伪造结果、放宽验收，或把隔离数据写进被测路径。任务没有定义的评测方法不要自行引入。
3. 亲自运行契约中的测试和边界命令。
4. 核对 SHA。仓库有 CI 时核对精确 SHA；没有 CI 就写没有。

【输出】
建议裁决只能是 ACCEPTED、REWORK 或 ESCALATE。REWORK 必须有 file:line、复现和修复验收条件。ESCALATE 必须说明哪条上层约束被打破。
指定了报告路径才写入，并用真实 report-path 附上。最后用序言中的命令发送一次 worker_done --outcome succeeded。正文首句写 [VERDICT: ...]，随后三句审查结论。发送后保持终端空闲。
```
