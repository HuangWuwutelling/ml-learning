---
name: xcopy
category: 文件操作
syntax: "xcopy <source> [<destination>] [/options]"
tags: ["文件", "复制", "目录"]
aliases: []
level: 进阶
popularity: 60
---

复制文件和目录树。相较 `copy`，`xcopy` 支持递归、保留属性、过滤等，更适合目录级复制。`/e` 复制所有子目录（包括空的），`/t` 只复制目录结构，`/y` 目标存在时不提示覆盖，`/z` 可恢复模式（网络中断后可续传）。

## 示例

```cmd
xcopy src dest /e
xcopy C:\data D:\backup /e /y
xcopy *.log D:\logs /y
xcopy C:\app D:\app /e /h /o
```
