---
name: mkdir
category: 文件操作
syntax: "mkdir [<drive>:]<path> [...]"
tags: ["文件", "目录", "创建"]
aliases: ["md"]
level: 入门
popularity: 85
---

创建目录。cmd 的 mkdir 会自动创建中间目录（如 `mkdir a\b\c` 在 a 已存在时会创建 a\b 和 a\b\c）。`md` 是同义命令。

## 示例

```cmd
mkdir new_folder
mkdir C:\Users\me\projects\app
mkdir app\src\test
md backup
```
