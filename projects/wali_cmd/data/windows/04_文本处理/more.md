---
name: more
category: 文本处理
syntax: "more [/c] [/e] [/t<n>] [/p] [+<line>] [<drive>:][<path>]filename"
tags: ["文本", "分页", "查看"]
aliases: []
level: 入门
popularity: 50
---

按屏幕分页显示 stdin 或一个/多个文件的内容。Linux 中 `more`/`less` 的等价命令。`/c` 显示前清屏，`+n` 从第 n 行开始显示，`/t<n>` 把 tab 替换为 n 个空格，`/e` 启用扩展交互模式（用更多键翻页）。`type big.log | more` 是常用的查看大日志文件方式。

## 示例

```cmd
more readme.txt
type big.log | more
more +100 app.log
more /c big.txt
```
