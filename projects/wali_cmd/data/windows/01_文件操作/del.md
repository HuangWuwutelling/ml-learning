---
name: del
category: 文件操作
syntax: "del [/p] [/f] [/s] [/q] [/a[:<attributes>]] <names>"
tags: ["文件", "删除"]
aliases: []
level: 入门
popularity: 90
---

删除一个或多个文件。在 PowerShell 中 `del` 是 `Remove-Item` 的别名，本说明针对 cmd 版本。`/p` 删除每个文件前确认，`/f` 强制删除只读文件，`/s` 从当前目录和所有子目录删除匹配项，`/q` 静默模式（不提示）。

## 示例

```cmd
del file.txt
del *.log
del /p *.txt
del /s *.tmp
del /f /q *.bak
```
