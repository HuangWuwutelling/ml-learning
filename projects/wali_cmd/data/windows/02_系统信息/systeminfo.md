---
name: systeminfo
category: 系统信息
syntax: "systeminfo [/s <computer> [/u <domain>\\<user> [/p <password>]]] [/fo {table | list | csv}] [/nh]"
tags: ["系统", "信息", "远程"]
aliases: []
level: 入门
popularity: 70
---

显示本地或远程计算机的操作系统配置信息，包含 OS 版本、安装日期、内存、网卡、补丁等。`/s` 指定远程主机，配合 `/u` 用户名和 `/p` 密码使用；`/fo` 控制输出格式（table/list/csv）。

## 示例

```cmd
systeminfo
systeminfo /fo list
systeminfo /s 192.168.1.10 /u admin /p P@ssw0rd
systeminfo | findstr /i "OS Name"
```
