---
name: jobs
category: 任务管理
syntax: "jobs [options] [job_spec]"
tags: ["shell", "任务", "后台"]
aliases: []
level: 入门
popularity: 65
---

显示当前 shell 会话中的后台任务（job）状态。`-l` 同时显示 PID，`-p` 只显示 PID，`-n` 只显示自上次通知后状态变化的任务。`%n` 引用第 n 个任务，配合 `fg %n` 调回前台、`bg %n` 在后台继续运行、`kill %n` 终止。shell 内置命令，无独立二进制。

## 示例

```bash
jobs
jobs -l
jobs %1
sleep 100 &
jobs
```
