---
name: move
category: 文件操作
syntax: "move [/y | /-y] [<drive>:][<path>]<source> [<destination>]"
tags: ["文件", "移动", "重命名"]
aliases: []
level: 入门
popularity: 80
---

移动或重命名文件和目录。在 PowerShell 中 `move` 是 `Move-Item` 的别名，本说明针对 cmd 版本。`/y` 不询问直接覆盖现有文件，`/-y` 即使权限允许也强制确认。

## 示例

```cmd
move file.txt D:\backup\
move report.doc final-report.doc
move /y old.log archive\
move C:\data\*.csv D:\csv\
```
