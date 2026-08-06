---
name: taskkill
category: 进程
syntax: "taskkill {/pid <processID> | /im <imagename>} [/f] [/t] [/s <computer>]"
tags: ["进程", "终止"]
aliases: []
level: 入门
popularity: 75
---

按进程 ID 或镜像名终止进程。`/pid <id>` 指定 PID，`/im <name>` 指定可执行文件名（如 `chrome.exe`），`/f` 强制终止（不询问），`/t` 同时终止该进程启动的子进程。比资源管理器强行结束更可靠，常用在脚本里清理卡死进程。

## 示例

```cmd
taskkill /pid 1234
taskkill /im notepad.exe
taskkill /im chrome.exe /f
taskkill /pid 1234 /t /f
taskkill /im hung.exe /s 192.168.1.10
```
