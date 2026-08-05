---
name: top
category: 系统监控
syntax: "top [options]"
tags: ["进程", "监控", "系统"]
aliases: []
level: 入门
popularity: 80
---

动态实时显示系统中进程的资源占用（CPU、内存、负载等）。`q` 退出，`P` 按 CPU 排序，`M` 按内存排序，`k <pid>` 给进程发信号，`1` 展开多核 CPU。`htop` 是更友好的替代品。

## 示例

```bash
top
top -u www-data
top -p 1234,5678
top -bn1 | head -20
top -o %MEM
```
