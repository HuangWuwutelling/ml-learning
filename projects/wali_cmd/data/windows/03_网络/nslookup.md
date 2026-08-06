---
name: nslookup
category: 网络
syntax: "nslookup [exit | finger | help | ls | lserver | root | server | set | view] [options] <host> [<server>]"
tags: ["网络", "DNS", "诊断"]
aliases: []
level: 进阶
popularity: 65
---

查询 DNS 信息，用于诊断 DNS 解析问题。支持两种模式：非交互式（直接给参数查一个主机）和交互式（单独 `nslookup` 进入 `>` 提示符多次查询）。第二参数可指定 DNS 服务器（如 `1.1.1.1`），不带时用默认 DNS。`-type=A+AAAA` 查询指定记录类型，`-debug` 开启调试模式。

## 示例

```cmd
nslookup example.com
nslookup example.com 1.1.1.1
nslookup -type=AAAA example.com
nslookup -debug example.com
```
