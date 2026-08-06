---
name: tasklist
category: 系统信息
syntax: "tasklist [/s <computer> [/u <domain>\\<user> [/p <password>]]] [/m <module> | /svc | /v] [/fo {table | list | csv}]"
tags: ["进程", "列表", "远程"]
aliases: []
level: 入门
popularity: 75
---

显示本地或远程机器上当前运行的进程。Linux 中 `ps -ef` 的等价命令。`/svc` 显示每个进程承载的服务，`/m` 列出使用特定 .dll 的进程（找占用某库的进程），`/v` 显示详细信息（含窗口标题）。

## 示例

```cmd
tasklist
tasklist /fo table
tasklist /fi "imagename eq chrome.exe"
tasklist /m mshtml.dll
```
