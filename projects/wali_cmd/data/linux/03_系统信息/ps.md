---
name: ps
category: 进程查看
syntax: "ps [options]"
tags: ["进程", "查看", "系统"]
aliases: []
level: 入门
popularity: 88
---

快照式查看当前进程。常用组合：`ps aux` 列出所有进程（user/BSD 风格），`ps -ef` 完整格式列出所有进程。配合 `grep` 过滤具体程序；`ps -L` 看线程；`--sort` 按字段排序。

## 示例

```bash
ps aux
ps aux | grep python
ps -ef
ps -u $USER -F
ps -eo pid,pcpu,pmem,comm --sort=-pcpu | head
```
