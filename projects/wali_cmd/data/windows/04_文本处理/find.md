---
name: find
category: 文本处理
syntax: "find [/v] [/c] [/n] [/i] [/off[line]] <\"string\"> [[<drive>:][<path>]filename[ ...]]"
tags: ["文本", "搜索"]
aliases: []
level: 入门
popularity: 65
---

在文件中查找指定字符串。`/v` 打印不包含字符串的行，`/c` 只统计匹配的行数（不显示内容），`/n` 显示行号，`/i` 不区分大小写。Linux 中 `grep` 的等价命令（但能力有限：不支持正则，要用正则请用 `findstr`）。一次可指定多个文件名。

## 示例

```cmd
find "ERROR" app.log
find "TODO" *.txt
find /v "DEBUG" app.log
find /c "INFO" app.log
find /n "TODO" readme.txt
```
