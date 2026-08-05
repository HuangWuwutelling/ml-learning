---
name: kill
category: 进程控制
syntax: "kill [options] <pid>..."
tags: ["进程", "信号", "终止"]
aliases: []
level: 入门
popularity: 90
---

向进程发送信号（默认 SIGTERM）。`-l` 列出所有信号名/编号；常见信号：`1 HUP`（重载配置）、`2 INT`（Ctrl+C 中断）、`9 KILL`（强制终止，不可拦截）、`15 TERM`（优雅终止，可被进程捕获处理）、`19 STOP`（暂停）。PID 可用 `ps`/`pgrep` 查到。

## 示例

```bash
kill 1234
kill -9 1234
kill -TERM 1234
kill -l
kill -HUP $(pidof nginx)
```
