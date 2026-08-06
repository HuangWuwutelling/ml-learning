---
name: robocopy
category: 文件操作
syntax: "robocopy <source> <destination> [<file>[ ...]] [<options>]"
tags: ["文件", "复制", "同步", "目录"]
aliases: []
level: 进阶
popularity: 70
---

Robust File and Folder Copy，Windows 内置的可靠文件复制工具。默认仅在源和目标的修改时间或大小不同时复制（即差异复制），比 `xcopy` 更稳健，支持断点续传、重试、镜像同步等。`/E` 包含空目录，`/MIR` 镜像同步（删除目标中源没有的文件），`/Z` 可恢复模式，`/R:n /W:n` 控制重试次数和等待秒数。返回码：0=无变化，1=复制成功，>=8 视为失败。

## 示例

```cmd
robocopy C:\src D:\dst *.txt
robocopy C:\src D:\dst /E
robocopy C:\src D:\dst /MIR
robocopy C:\src D:\dst /E /Z /R:3 /W:5
```
