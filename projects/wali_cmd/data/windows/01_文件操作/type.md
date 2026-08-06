---
name: type
category: 文件操作
syntax: "type [<drive>:][<path>]  filename"
tags: ["文件", "查看", "内容"]
aliases: []
level: 入门
popularity: 70
---

显示文件内容。在 PowerShell 中 `type` 是 `Get-Content` 的别名，本说明针对 cmd 版本。Windows cmd 的 type 等价于 Linux 的 `cat`，会把整个文件输出到控制台，适合查看小文件，大文件应该用 `more` 分页。

## 示例

```cmd
type readme.txt
type config.ini
type C:\logs\app.log
type *.txt
```
