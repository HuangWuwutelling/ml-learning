---
name: sort
category: 文本处理
syntax: "sort [/r] [/+<N>] [/m <kilobytes>] [/l <locale>] [/rec <characters>] [<input>] [/t [<tempdir>]] [/o <output>]"
tags: ["文本", "排序"]
aliases: []
level: 入门
popularity: 55
---

读取输入并按行排序，结果输出到屏幕、文件或管道。默认从每行第一个字符开始排序，`/+3` 表示从第 3 个字符开始比较，`/r` 倒序，`/o <file>` 写入文件（比 `>` 重定向更快更省内存）。不区分大小写。常与 `find`/`findstr` 通过管道组合：`find ... | sort`。

## 示例

```cmd
sort data.txt
sort /r expenses.txt
sort /+3 names.txt
find "Jones" maillist.txt | sort
sort /r /o sorted.txt data.txt
```
