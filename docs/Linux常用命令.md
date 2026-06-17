# Linux 常用命令（WSL 实战笔记）

## 目录

- [WSL 配置](#wsl-配置)
- [文件与目录](#文件与目录)
- [文件内容查看与处理](#文件内容查看与处理)
- [权限管理](#权限管理)
- [压缩与归档](#压缩与归档)
- [进程管理](#进程管理)
- [网络相关](#网络相关)
- [系统信息](#系统信息)
- [包管理 (apt)](#包管理-apt)
- [Shell 实用技巧](#shell-实用技巧)

---

## WSL 配置

### 代理问题（NAT 模式）

WSL2 默认 NAT 模式，`localhost` 不共享。如果你的 Windows 开了代理（比如 Clash），WSL 里没法直接用。

**现象：**
```
wsl: 检测到 localhost 代理配置，但未镜像到 WSL。
NAT 模式下的 WSL 不支持 localhost 代理。
```

**方案一：.wslconfig 切换 mirrored 模式（推荐）**

在 Windows 用户目录下创建 `C:\Users\<用户名>\.wslconfig`：

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
firewall=false
autoProxy=true
```

然后在 PowerShell（管理员）执行：
```powershell
wsl --shutdown
wsl
```

重启后 WSL 和 Windows 共享 IP，`localhost` 直接通。

**方案二：不改模式，手动设代理（Windows IP 是动态的）**

```bash
# 获取 Windows 主机 IP（WSL 里执行）
host_ip=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
export http_proxy="http://$host_ip:7897"
export https_proxy="http://$host_ip:7897"
```

可以加到 `~/.bashrc` 末尾，每次启动自动生效。

### WSL 常用命令

```bash
# 查看已安装的 Linux 发行版
wsl --list --verbose

# 关闭 WSL（重启用）
wsl --shutdown

# 设置默认发行版
wsl --set-default Ubuntu

# 导出/导入分发版（迁移用）
wsl --export Ubuntu d:\ubuntu.tar
wsl --import Ubuntu d:\wsl\ d:\ubuntu.tar

# 进入 WSL 内部
wsl

# 以指定用户进入
wsl -u root

# 在 WSL 里执行单条命令（不进入交互 shell）
wsl ls -la
```

### WSL 文件互访

```bash
# Windows → WSL: 直接访问 \\wsl.localhost\Ubuntu\home\
# WSL → Windows: /mnt/c/ 挂载 C 盘

# 在 WSL 里访问 Windows 文件
cd /mnt/c/Users/zaoquan/Downloads

# 注意：跨文件系统操作（/mnt/c/ ↔ ~/）很慢！
# 需要 IO 密集操作时，把项目放到 WSL 的 Linux 文件系统里
```

---

## 文件与目录

```bash
# 基本操作
pwd                      # 当前路径
ls -la                   # 列出所有文件（含隐藏文件）
ls -lh                   # 以人类可读大小显示
tree                     # 目录树（需 apt install tree）

cd ~                     # 回 home
cd -                     # 回上一个目录

mkdir -p a/b/c           # 递归创建目录
touch file.txt            # 创建空文件 / 更新修改时间

cp source dest            # 复制
cp -r dir1 dir2           # 递归复制目录
cp file{,.bak}            # 快速备份: cp file.txt file.txt.bak 的简写

mv old new                # 移动 / 重命名
mv file.txt ../           # 移动到上层目录

rm file.txt               # 删除文件（不进回收站！）
rm -rf dir/               # 递归强制删除目录（小心！）

# 查找文件
find . -name "*.py"                 # 按名字查找
find . -name "*.py" -type f         # 只找文件，不找目录
find . -size +10M                   # 找大于 10MB 的文件
find . -mtime -1                    # 最近 1 天修改的文件

locate file.txt          # 更快（需 updatedb 更新索引）

# 软链接
ln -s target link_name   # 创建软链接（类似 Windows 快捷方式）
ln target link_name      # 硬链接（同一文件多个名字）
```

---

## 文件内容查看与处理

```bash
# 查看小文件
cat file.txt
cat -n file.txt          # 显示行号

# 分页查看
less file.txt            # 按 q 退出，/ 搜索，n 下一个，N 上一个
more file.txt            # 更简单的分页（less 更好用）

# 只看头尾
head -n 20 file.txt       # 前 20 行
tail -n 20 file.txt       # 后 20 行
tail -f file.txt          # 实时跟踪文件追加（看日志用）
tail -f --pid=1234        # 进程 1234 结束就自动退出

# 文本处理三剑客
grep "error" log.txt              # 查找包含 error 的行
grep -i "error" log.txt           # 忽略大小写
grep -r "TODO" --include="*.py" . # 递归搜索 .py 文件
grep -v "debug" log.txt           # 排除含 debug 的行
grep -c "error" log.txt           # 只统计出现次数
grep -n "error" log.txt           # 显示行号
grep -A3 -B2 "error" log.txt      # 前后各显示 2-3 行上下文

sed 's/old/new/g' file.txt        # 替换所有 old → new（只输出不改文件）
sed -i 's/old/new/g' file.txt     # 直接修改文件
sed -n '10,20p' file.txt          # 打印 10~20 行

awk '{print $1, $NF}' file.txt    # 打印第一列和最后一列
awk -F: '{print $1}' /etc/passwd  # 以 : 分隔，取第一列
awk '{sum+=$1} END{print sum}'    # 第一列求和

# 排序与去重
sort file.txt
sort -n file.txt                  # 按数字排序
sort -k2 file.txt                 # 按第二列排序
sort -u file.txt                  # 排序并去重

uniq                               # 去重（必须相邻，通常先 sort）
sort file.txt | uniq -c            # 统计每行出现次数

# 行处理
wc -l file.txt                    # 行数
wc -w file.txt                    # 单词数
wc -c file.txt                    # 字节数
```

---

## 权限管理

```bash
# 理解权限
# r=4, w=2, x=1 → 777 = rwxrwxrwx
#      所有者  组    其他人
# chmod 755  = rwx   r-x   r-x

chmod 755 script.sh               # rwxr-xr-x（常用：脚本可执行）
chmod +x script.sh                # 增加执行权限
chmod -R 644 dir/                 # 递归设为 -rw-r--r--

chown user:group file.txt         # 修改所有者和组
chown -R user:group dir/          # 递归修改

# 实际场景
chmod 600 ~/.ssh/id_rsa           # SSH 私钥必须严格权限
chmod 700 ~/.ssh                  # SSH 目录
```

---

## 压缩与归档

```bash
# tar（最常用）
tar czf archive.tar.gz dir/       # 打包 + gzip 压缩
tar cjf archive.tar.bz2 dir/      # bzip2 压缩（更快）
tar xzf archive.tar.gz            # 解压
tar xf archive.tar.gz             # 新版 tar 自动识别格式
tar tf archive.tar.gz             # 查看包内文件列表

# zip
zip -r archive.zip dir/           # 压缩目录
unzip archive.zip                 # 解压
unzip -l archive.zip              # 查看包内容

# 7z（需要安装 p7zip）
7z x archive.7z

# gzip / gunzip（单文件）
gzip file.txt                     # 压缩 → file.txt.gz
gunzip file.txt.gz                # 解压
zcat file.txt.gz                  # 直接查看压缩文件内容
```

---

## 进程管理

```bash
# 查看进程
ps aux                            # 所有进程
ps aux | grep python              # 找 Python 进程
ps -ef                            # 完整格式

top                               # 实时监控（按 q 退出）
htop                              # 更好看的 top（需安装）

# 找进程 ID
pgrep python                      # 通过名字找 PID
pidof python                      # 同上

# 结束进程
kill 1234                         # 优雅终止 PID=1234
kill -9 1234                      # 强制杀死（最后手段）
killall python                    # 杀掉所有 python 进程
pkill -f "train.py"               # 根据完整命令名匹配

# 后台运行
python train.py &                 # 后台运行
nohup python train.py &           # 退出 shell 后继续运行
nohup python train.py > out.log 2>&1 &  # 日志重定向到文件

# 查看后台任务
jobs                              # 当前 shell 的后台任务
fg %1                             # 将 job 1 调回前台
bg %1                             # 将暂停的 job 放到后台

# screen / tmux（断开后不中断）
screen -S my_session              # 创建会话
# Ctrl+A, D                        # 分离（detach）
screen -r my_session              # 重新连接

tmux new -s my_session            # 创建 tmux 会话
tmux ls                           # 列出会话
tmux attach -t my_session         # 连接会话
```

---

## 网络相关

```bash
# 连接测试
ping google.com                   # 测试网络连通性（Ctrl+C 停止）
curl -I https://example.com       # 查看 HTTP 响应头
curl -X POST -d '{"key":"val"}' -H "Content-Type: application/json" url
wget url                          # 下载文件

# 端口相关
ss -tlnp                          # 查看监听端口（替代 netstat）
ss -tulnp                         # 所有 TCP/UDP 监听端口

# 如果 ss 没有，用 netstat
netstat -tlnp

# DNS
nslookup google.com               # DNS 查询
dig google.com                    # 更详细的 DNS

# 检查端口是否通
nc -zv host 80                    # 检测 host 的 80 端口
nc -zv 127.0.0.1 8000            # 检测本地 8000 端口

# SSH
ssh user@host                     # SSH 登录
ssh -i key.pem user@host          # 指定密钥
ssh -p 2222 user@host             # 指定端口
ssh-copy-id user@host             # 上传公钥（免密登录）

# SCP
scp file.txt user@host:/path/     # 复制文件到远程
scp -r dir/ user@host:/path/      # 复制目录到远程
scp user@host:/path/file.txt ./   # 从远程下载

# GPU 监控（WSL2 适用）
nvidia-smi                        # GPU 状态
watch -n 1 nvidia-smi             # 每秒刷新
```

---

## 系统信息

```bash
# 硬件
free -h                           # 内存用量
df -h                             # 磁盘用量
du -sh dir/                       # 查看目录大小
du -sh * | sort -rh | head -10    # 当前目录下最大的 10 个文件/目录

uname -a                          # 内核信息
lsb_release -a                    # 发行版信息
cat /etc/os-release               # 同上（更标准）

# CPU
lscpu                             # CPU 信息
nproc                             # CPU 核心数
uptime                            # 系统运行时间 + 负载

# 当前用户
whoami                            # 我是谁
id                                # 用户 ID 和组 ID
who                               # 谁登录了

# 时间
date                              # 当前时间
date +%Y%m%d-%H%M%S               # 格式化：20260522-143000
cal                               # 日历

# 环境变量
echo $PATH                        # 查看 PATH
env                                # 所有环境变量
export NAME=value                  # 临时设置环境变量
```

---

## 包管理 (apt)

适用于 Ubuntu/Debian（WSL 默认发行版）。

```bash
# 更新源
sudo apt update                    # 更新包列表
sudo apt upgrade -y                # 升级所有已安装包
sudo apt full-upgrade -y           # 升级+处理依赖变更

# 搜索与安装
apt search python                  # 搜索包
apt show python3                   # 查看包详情
sudo apt install python3           # 安装
sudo apt install -y build-essential  # 一键装开发工具链

# 卸载
sudo apt remove python3            # 卸载（保留配置）
sudo apt purge python3             # 卸载（删配置）
sudo apt autoremove                # 清理孤立依赖

# 清理
sudo apt clean                     # 清理下载缓存
sudo apt autoclean                 # 清理过期的缓存
```

### Python 相关（WSL 下推荐）

```bash
# WSL 通常自带 Python3，pip 需要装
sudo apt install python3 python3-pip python3-venv

# 创建虚拟环境（绝对不要 sudo pip install！）
python3 -m venv .venv
source .venv/bin/activate          # 激活
pip install -r requirements.txt    # 安装依赖
deactivate                         # 退出

# 查看已安装包
pip list
pip freeze > requirements.txt      # 导出当前环境
```

### Git 相关

```bash
sudo apt install git

# 配置（Windows 上的 Git 证书可以共享）
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# 代理（如果你的 WSL 与 Windows 共用代理）
git config --global http.proxy http://127.0.0.1:7897
git config --global --unset http.proxy  # 取消代理
```

---

## Shell 实用技巧

### 快捷键

| 快捷键 | 作用 |
|--------|------|
| `Ctrl+A` | 光标到行首 |
| `Ctrl+E` | 光标到行尾 |
| `Ctrl+U` | 删除光标前所有字符 |
| `Ctrl+K` | 删除光标后所有字符 |
| `Ctrl+W` | 删除前一个单词 |
| `Ctrl+L` | 清屏（等同于 `clear`） |
| `Ctrl+R` | 搜索历史命令 |
| `Ctrl+C` | 中断当前命令 |
| `Ctrl+D` | 退出 shell |
| `!!` | 重复上一条命令 |
| `!$` | 上一条命令的最后一个参数 |

### 管道与重定向

```bash
# 管道：前一个命令的输出作为后一个命令的输入
cmd1 | cmd2

# 重定向
cmd > file.txt          # 标准输出 → 文件（覆盖）
cmd >> file.txt         # 标准输出 → 文件（追加）
cmd 2> error.log        # 错误输出 → 文件
cmd > out.log 2>&1      # 标准输出 + 错误输出 → 同一个文件
cmd &> out.log          # 同上（bash 4+ 简写）

# /dev/null 黑洞
cmd > /dev/null 2>&1    # 丢弃所有输出

# 组合命令
cmd1 && cmd2            # cmd1 成功才执行 cmd2
cmd1 || cmd2            # cmd1 失败才执行 cmd2
cmd1 ; cmd2             # 无论成功失败，顺序执行
```

### 别名与补全

```bash
# 常用别名（加到 ~/.bashrc）
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias gp='git push'
alias gl='git log --oneline --graph'
alias gc='git commit'

# 重新加载配置
source ~/.bashrc

# Tab 补全
# - 输入一半路径按 Tab
# - 连续按两次 Tab 显示所有候选
```

### .bashrc 常用配置

```bash
# ~/.bashrc 常用追加内容

# 代理（mirrored 模式下不用，NAT 模式需要）
if grep -qi "microsoft" /proc/version 2>/dev/null; then
    # NAT 模式代理
    host_ip=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
    export http_proxy="http://$host_ip:7897"
    export https_proxy="http://$host_ip:7897"
fi

# 别名
alias ll='ls -alF'
alias gc='git commit'
alias gp='git push'
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline --graph --all --decorate'

# 自定义提示符
PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# 历史命令
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTTIMEFORMAT="%F %T "

# PATH 追加
export PATH="$HOME/.local/bin:$PATH"
```

---

## 快速速查表

| 目的 | 命令 |
|------|------|
| 找文件 | `find . -name "*.py"` |
| 找内容 | `grep -r "keyword" .` |
| 后台跑脚本 | `nohup python train.py > log.txt 2>&1 &` |
| 看日志 | `tail -f log.txt` |
| 看进程 | `ps aux | grep python` |
| 杀进程 | `kill -9 PID` |
| 看端口 | `ss -tlnp | grep 8000` |
| 看磁盘 | `df -h` |
| 看目录大小 | `du -sh * | sort -rh` |
| 看 GPU | `watch -n 1 nvidia-smi` |
| 解压 tar | `tar xzf file.tar.gz` |
| 打包 | `tar czf archive.tar.gz dir/` |
| 搜索历史 | `Ctrl+R` |
| 权限设错修复 | `chmod -R 644 dir/ && chmod -R +X dir/` |
