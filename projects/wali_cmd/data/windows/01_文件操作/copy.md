---
name: copy
category: 文件操作
syntax: "copy [/d] [/v] [/n] [/y] [/-y] [/z] [/l] [/a] [/b] <source> [<destination>]"
tags: ["文件", "复制"]
aliases: []
level: 入门
popularity: 85
---

复制一个或多个文件到指定位置。在 PowerShell 中 `copy` 是 `Copy-Item` 的别名，本说明针对 cmd 版本。`/y` 覆盖现有文件不提示，`/-y` 覆盖前强制确认，`/z` 以可恢复模式复制网络文件。

## 示例

```cmd
copy file.txt backup.txt
copy file.txt D:\backup\
copy *.txt D:\backup\
copy /y src\*.log D:\logs
```
