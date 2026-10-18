# Spec

写 Spec 时使用本文件。

## 规则

1. Spec 必须自包含。前置结论、接口、路径、基线 SHA 和验收命令都写进 Spec。
2. Spec 只写本任务需要的信息。不写记忆路径、其他 Ticket 或个人信息。
3. Spec 不留设计决定给 Worker。有选择时，由你选好写进 Spec。
4. Orca 会在 Spec 前面注入 preamble，包含 Task ID、Dispatch ID 和生命周期命令。不要在 Spec 中另写这些内容。

## 模板

```markdown
【角色】
你是 <Implementation | Research | Bounded Repair> Worker。只执行本 Spec。
不派发子代理。不读取工作区外的文件。不做 Spec 没写的设计决定。
遇到歧义时，用 preamble 中的 ask 提问，然后等待回答。

【目标】
- 工作区：<绝对路径>
- 基线：<branch @ SHA>

【步骤】
1. <具体到文件、函数和接口的改动>
2. <要新增或修改的测试>

【约束】
- 可写：<文件白名单。Research 写“无”或一个报告路径>
- 禁止：修改白名单外的文件；修改全局配置；提交密钥；伪造输出
- Git：<不提交 | 按 Spec 中的 message 提交>

【验收】
1. <命令>：<通过条件>
2. <边界或负向检查>

【结束】
用 preamble 中的命令发送一次 worker_done。
正文写三句：改了什么、实测结果、剩余事项。
--files-modified 只填写真实修改过的文件。发送后保持空闲。
```

## Bounded Repair

只写三项：Review 发现的缺陷、能复现缺陷的测试、允许修改的文件。不重新开放原任务的范围。
