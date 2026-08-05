---
name: ls
category: 文件浏览
syntax: "ls [options] [path...]"
tags: ["浏览", "目录"]
aliases: []
level: 入门
popularity: 100
---

列出目录内容。常用 `-l` 显示详情、`-a` 包含隐藏文件、`-h` 人类可读大小、`-R` 递归、`-t` 按时间排序。GNU coreutils 提供的 ls 几乎每个 Linux 用户每天都在用。

## 示例

```bash
ls -la
ls -lh
ls -ltr
ls -R /var/log
ls -F
```
