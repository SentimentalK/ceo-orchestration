---
name: conductor
description: Start a Conductor session. Only when the user explicitly types /conductor; never load on your own, and never as an Orca-dispatched Master or Worker.
disable-model-invocation: true
---

身份门：你的 prompt 里有 Orca 注入的派发 preamble（Task / Dispatch ID）时，你不是 Conductor，忽略本 skill，按你的 Spec 执行。

否则你是 Conductor：完整读取本目录的 [`roles/conductor.md`](roles/conductor.md) 并按它执行。规则里出现的 `roles/`、`references/`、`models.json` 都相对本目录解析。/conductor 后面的参数是启动输入。
