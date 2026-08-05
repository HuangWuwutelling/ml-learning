---
name: ifconfig
category: 网络配置
syntax: "ifconfig [interface] [options]"
tags: ["网络", "接口", "配置"]
aliases: []
level: 进阶
popularity: 60
---

net-tools 套件中的网络接口配置工具，可查看/配置网卡 IP、掩码、MTU、启停接口。在新发行版中已被 `ip` 命令取代，但许多老脚本仍依赖它。`-a` 显示所有接口（含禁用），`up`/`down` 启停接口，可直接给接口配 IP。

## 示例

```bash
ifconfig
ifconfig -a
ifconfig eth0
ifconfig eth0 up
ifconfig eth0 192.168.1.100 netmask 255.255.255.0
ifconfig eth0 down
```
