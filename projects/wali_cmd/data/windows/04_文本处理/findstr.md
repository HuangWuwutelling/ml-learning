---
name: findstr
category: 文本处理
syntax: "findstr [/s] [/i] [/r] [/v] [/n] [/m] [/c:\"<string>\"] [/off[line]] <strings> [<drive>:][<path>]filename[ ...]"
tags: ["文本", "搜索", "正则"]
aliases: []
level: 进阶
popularity: 70
---

在文件中查找文本，支持多个字符串和基本正则（`/r`）。`/s` 递归搜索子目录，`/i` 不区分大小写，`/c:"string"` 把含空格的字符串当成一个字面量（否则空格会分隔为多字符串），`/m` 只列出匹配的文件名，`/n` 加行号。Linux 中 `grep -E` 的等价命令（语法接近 grep 但参数风格是 cmd 的）。

## 示例

```cmd
findstr "error" *.log
findstr /s "ERROR" *.log
findstr /i "warning" *.txt
findstr /r "[0-9]+" data.txt
findstr /m "TODO" *.md
```
