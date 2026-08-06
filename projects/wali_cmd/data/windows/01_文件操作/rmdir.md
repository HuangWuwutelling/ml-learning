---
name: rmdir
category: 文件操作
syntax: "rmdir [/s] [/q] [<drive>:]<path>"
tags: ["文件", "目录", "删除"]
aliases: ["rd"]
level: 入门
popularity: 75
---

删除目录。在 PowerShell 中 `rmdir` 是 `Remove-Item` 的别名，本说明针对 cmd 版本。`/s` 同时删除目录中的所有文件和子目录，`/q` 静默模式（与 `/s` 配合避免每项确认）。注意：默认 `rmdir` 只能删除空目录。

## 示例

```cmd
rmdir empty_folder
rmdir /s old_project
rmdir /s /q temp
rd cache
```
