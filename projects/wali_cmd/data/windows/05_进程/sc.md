---
name: sc
category: 进程
syntax: "sc [<server>] <query|start|stop|create|delete|config|...> [service_name] [options]"
tags: ["服务", "进程", "系统"]
aliases: []
level: 进阶
popularity: 50
---

与服务控制管理器（SCM）和 Windows 服务通信。`query` 查询服务状态（不带服务名列出所有），`start`/`stop` 启停服务，`create` 创建服务（必须指定 `binpath=`），`delete` 删除服务，`config` 修改服务配置（如 `type=`、`start=`）。注意 `binpath=` 后必须有空格，等号后也要空格。

## 示例

```cmd
sc query
sc query Spooler
sc start Spooler
sc stop Spooler
sc create MyService binPath= C:\my\service.exe
sc delete MyService
```
