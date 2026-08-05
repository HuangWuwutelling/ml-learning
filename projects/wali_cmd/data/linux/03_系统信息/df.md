---
name: df
category: 磁盘信息
syntax: "df [options] [file...]"
tags: ["磁盘", "空间", "系统"]
aliases: []
level: 入门
popularity: 85
---

报告各文件系统的磁盘空间使用情况。`-h` 人类可读（K/M/G），`-T` 显示文件系统类型，`-i` 看 inode 使用，`--total` 汇总。指定文件路径则只显示包含该文件的文件系统。

## 示例

```bash
df -h
df -T
df -h /home
df -i
df -h --total
```
