---
name: ver
category: 系统信息
syntax: "ver"
tags: ["系统", "版本"]
aliases: []
level: 入门
popularity: 75
---

显示当前 Windows 或 MS-DOS 版本号。无参数，直接打印内核版本字符串（如 `Microsoft Windows [Version 10.0.22631.4391]`）。比 `systeminfo` 更轻量，但要查看完整构建号（如 Win11 23H2 等）应继续用 `systeminfo` 或 `ver` 配合 `findstr`。

## 示例

```cmd
ver
ver | findstr "Windows"
```
