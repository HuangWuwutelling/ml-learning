---
name: ping
category: 网络诊断
syntax: "ping [options] destination"
tags: ["网络", "诊断", "ICMP"]
aliases: []
level: 入门
popularity: 85
---

向目标主机发送 ICMP ECHO_REQUEST 包并显示往返时间（RTT），用于检测网络连通性和延迟。`-c` 限制发送次数（默认一直发，`Ctrl+C` 停），`-i` 调整间隔秒数，`-s` 改包大小，`-W` 超时秒数。某些云环境会屏蔽 ICMP，ping 不通不一定代表不可达。

## 示例

```bash
ping example.com
ping -c 5 8.8.8.8
ping -i 0.5 google.com
ping -s 1024 1.1.1.1
ping -c 3 -W 2 192.168.1.1
```
