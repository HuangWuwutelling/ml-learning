---
name: mv
category: 文件移动
syntax: "mv [options] source... dest"
tags: ["移动", "重命名", "文件"]
aliases: []
level: 入门
popularity: 92
---

移动或重命名文件与目录。当目标不是已存在目录时为重命名；目标是已存在目录时把源放进去。`-i` 覆盖前提示，`-f` 强制覆盖不提示，`-n` 不覆盖已存在文件。同一文件系统内 mv 是 rename 系统调用，瞬时完成。

## 示例

```bash
mv old.txt new.txt
mv file.txt /target/
mv -i src/* dst/
mv file1 file2 file3 /dst/
mv -n latest.log archive/
```
