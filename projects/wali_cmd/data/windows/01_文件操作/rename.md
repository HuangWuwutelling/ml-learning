---
name: rename
category: 文件操作
syntax: "rename [<drive>:][<path>]<filename1> <filename2>"
tags: ["文件", "重命名"]
aliases: ["ren"]
level: 入门
popularity: 75
---

重命名文件或目录。与 `ren` 命令功能完全相同。不能跨驱动器或目录移动文件，目标名（filename2）也支持通配符以批量重命名。

## 示例

```cmd
rename report.txt final.txt
rename *.txt *.doc
rename chap10 part10
ren old.log new.log
```
