---
name: nohup
category: 后台运行
syntax: "nohup command [arg]..."
tags: ["后台", "守护", "进程"]
aliases: []
level: 入门
popularity: 80
---

让命令忽略 SIGHUP 信号，终端关闭/用户退出后进程继续运行。常与 `&` 配合放后台，默认输出到 `nohup.out`（可用 `> file 2>&1` 重定向）。需要长期运行的服务通常 `nohup ... &` 或用 systemd/supervisor。

## 示例

```bash
nohup python train.py &
nohup python train.py > out.log 2>&1 &
nohup ./server.sh &
nohup java -jar app.jar > app.log 2>&1 &
```
