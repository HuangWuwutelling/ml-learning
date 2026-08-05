---
name: rm
category: 文件删除
syntax: "rm [options] file..."
tags: ["删除", "文件"]
aliases: []
level: 入门
popularity: 90
---

删除文件或目录。删除后无法恢复（无回收站）。`-r` 递归删除目录，`-f` 强制删除不提示，`-i` 每次删除前询问。`rm -rf` 是高危操作，使用前务必确认路径。

## 示例

```bash
rm file.txt
rm -i *.log
rm -rf /tmp/build
rm -rf --preserve-root /
rm -v *.tmp
```
