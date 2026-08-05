---
name: uname
category: 系统信息
syntax: "uname [options]"
tags: ["内核", "系统信息"]
aliases: []
level: 入门
popularity: 70
---

打印系统与内核信息。`-a` 全部信息（内核名/主机名/内核版本/架构等），`-r` 内核 release，`-m` 机器架构（x86_64/aarch64），`-s` 内核名（Linux），`-o` 操作系统。`uname -a` 在排查环境时几乎是必敲命令。

## 示例

```bash
uname -a
uname -r
uname -m
uname -s
uname -n
```
