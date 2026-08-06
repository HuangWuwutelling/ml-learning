---
name: dir
category: 文件操作
syntax: "dir [<drive>:][<path>][<filename>] [/p] [/q] [/w] [/d] [/a[[:]<attributes>]] [/o[[:]<sortorder>]] [/s] [/b]"
tags: ["文件", "列出", "目录"]
aliases: []
level: 入门
popularity: 90
---

列出目录中的文件和子目录。Windows cmd 的 ls 等价命令。不带参数时显示当前盘的卷标、序列号和文件列表，附带大小、最后修改时间和文件/目录总数。

## 示例

```cmd
dir
dir /w
dir /s *.txt
dir /a
dir /b
dir /o:d
```
