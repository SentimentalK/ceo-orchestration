# Task Spec 契约

编写、裁剪或审查 Worker Spec 时读取。并发、恢复和模型规则在 [`../execution.md`](../execution.md)，不要在 Spec 里复述一套调度手册。

Spec 是你和 Worker 之间的约束。Worker 只依赖 Spec 和目标工作区完成本任务。

## 原则

1. **自包含。** 前置结论、接口、路径、基线 SHA 和验收命令写进 Spec。禁止要求 Worker 读取 CEO/LifeOS、未授权 Ticket、个人记忆、父目录说明或其他仓库。
2. **最小信息。** 只写完成本任务所需的内容。不附带无关 Ticket、个人资料或项目背景。
3. **五要素。** Target、Change、Constraints、Ownership、Observable Acceptance 缺一不可。
4. **细节可调，语义不可破。** Worker 可以在 Ownership 内决定局部实现，不能改公开契约、不能放宽验收、不能绕过已批准约束。

## 模板

```markdown
# Task Spec: <任务标题>

## 1. 元数据
- 任务类型：Research | Implementation | Bounded Repair | Independent Review
- 批准范围：<本轮可执行边界，以及明确不包含的后续阶段>
- 前置依赖：<已完成 Task 或已冻结的基线 SHA；没有则写无>
- 执行环境：Worktree <current | isolated>；Agent/Model <调用者授权的身份，或继承该 Agent 默认>

## 2. Target
- 工作区：<绝对路径>
- 基线：<branch @ SHA>；当前验证基线：<命令与结果，或 UNVERIFIED>
- 相关模块：<路径和职责。只列本任务需要的>

## 3. Change
1. <交付项：精确行为、接口或报告。写正常路径，也写证据不足时契约要求的失败关闭行为。>
2. <测试或证据：文件、命令、必须覆盖的边界。>

## 4. Constraints
- 已批准的不变量：<从授权 Ticket 提炼，不要另造业务规则>
- 禁止：修改已验收且本任务未授权的文件；访问工作区外路径；修改全局 Agent 配置；提交密钥
- 诚实性：证据不足时按契约失败关闭或标未知。禁止伪造指标、SHA、测试结果或完整输出

## 5. Ownership
- 可写：<白名单。Research 默认无，或仅一个授权报告路径>
- 只读：<参考文件>
- 禁止访问：<工作区外路径，以及任务明确隔离的数据>
- Git：<不提交 / 允许 Conventional Commit / 允许普通 fast-forward push 并核对该 SHA 的 CI>

## 6. Observable Acceptance
1. <可复现命令和通过条件>
2. <任务要求的负向或边界证据>
3. worker_done：使用注入序言中的精确命令，恰好一次。正文三句：做了什么、实测证据、剩余事项。--files-modified 和 --report-path 只填真实值。
```

## 按类型裁剪

**Research。** 可写范围为无，或单个授权报告文件。验收必须是命令输出、文件行号或实测数据。未证实的判断标 `UNVERIFIED`。

**Implementation。** 可写白名单必须具体到文件。准备并行前，按 [`../execution.md`](../execution.md) 确认写入范围不相交；不相交才可以同时派发。

**Bounded Repair。** 只列审查指出的缺陷、必须新增的失败复现测试，以及允许修改的文件。不要把原任务重新开放成范围扩张。

**Independent Review。** 可写范围只有可选的审查报告路径。禁止修改被审业务文件。

**Decision Gate 记录。** 需要阻断下游任务时，问题里写三件事：前置实证、待决问题、每个选项对应的后续动作。选项不得包含“由 Master 修改上层验收标准”。创建命令以官方 `references/messaging-and-gates.md` 为准。
