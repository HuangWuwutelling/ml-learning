---
name: arp
category: 网络
syntax: "arp -a [inet_addr] [-N if_addr] | arp -s inet_addr eth_addr [if_addr] | arp -d inet_addr [if_addr]"
tags: ["网络", "ARP", "MAC"]
aliases: []
level: 进阶
popularity: 50
---

显示和修改 ARP（地址解析协议）缓存表，存储 IP 与物理 MAC 地址的映射。`-a` 显示当前 ARP 条目（可指定 IP 或接口过滤），`-s` 添加静态 ARP 条目（IP-MAC 绑定，TCP/IP 重启后失效），`-d` 删除条目。排查 ARP 欺骗攻击时常需要查看。

## 示例

```cmd
arp -a
arp -a -N 10.0.0.99
arp -s 10.0.0.80 00-AA-00-4F-2A-9C
arp -d 10.0.0.80
```
