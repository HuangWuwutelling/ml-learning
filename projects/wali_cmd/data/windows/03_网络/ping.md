---
name: ping
category: 网络
syntax: "ping [-t] [-a] [-n <count>] [-l <size>] [-w <timeout>] <target>"
tags: ["网络", "诊断", "ICMP"]
aliases: []
level: 入门
popularity: 90
---

向目标主机发送 ICMP ECHO_REQUEST 包并显示往返时间。与 Unix-like 系统不同，Windows `ping` 默认只发 4 个包。`-t` 持续 ping 直到 Ctrl+C 停止，`-n <count>` 指定发送次数，`-l <size>` 设置包大小，`-a` 反向解析 IP 到主机名。

## 示例

```cmd
ping 8.8.8.8
ping -n 5 example.com
ping -t google.com
ping -l 1024 1.1.1.1
ping -a 192.168.1.1
```
