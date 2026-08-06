---
name: ipconfig
category: 系统信息
syntax: "ipconfig [/all] [/renew [<adapter>]] [/release [<adapter>]] [/flushdns] [/displaydns]"
tags: ["网络", "IP", "DNS", "接口"]
aliases: []
level: 入门
popularity: 90
---

显示并管理 Windows 的网络配置。`/all` 显示详细信息（含 MAC、DNS、DHCP 服务器），`/release` 释放 IP、`/renew` 续约，`/flushdns` 清空本地 DNS 解析缓存（修改 hosts 后常用）。带 `<adapter>` 参数时只操作指定网卡（如 `Ethernet` 或 `Wi-Fi`）。

## 示例

```cmd
ipconfig
ipconfig /all
ipconfig /release
ipconfig /renew
ipconfig /flushdns
```
