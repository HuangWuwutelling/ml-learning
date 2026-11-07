"""wali_cmd 命令数据生成器。

统一类目命名 + 扩充到目标条数：
- Linux: 80 条（10 个核心类目，每个 8 条左右）
- Windows: 60 条（5 个核心类目，每个 12 条左右）

数据格式与 cloudImport 兼容（add 接受的字段）。
"""
import json
import os
from collections import defaultdict

OUT_LINUX = os.path.join(os.path.dirname(__file__), '..', 'cloudfunctions', 'cloudImport', 'data', 'linux_commands.json')
OUT_WINDOWS = os.path.join(os.path.dirname(__file__), '..', 'cloudfunctions', 'cloudImport', 'data', 'windows_commands.json')

# ───────────── Linux 命令数据 ─────────────
LINUX_COMMANDS = [
    # 文件操作 (10)
    {
        "name": "ls", "category": "文件操作", "subcategory": "列出目录",
        "syntax": "ls [options] [path...]",
        "example": ["ls", "ls -l", "ls -la", "ls -lh", "ls -lt", "ls *.txt", "ls -R", "ls -d */"],
        "description": "列出目录内容。`-l` 详细列表（权限/大小/时间），`-a` 含隐藏文件，`-h` 人类可读大小，`-t` 按修改时间排序，`-R` 递归子目录，`-d` 只显示目录本身。",
        "tags": ["列出", "目录", "文件"], "aliases": ["dir"], "level": "入门", "popularity": 100
    },
    {
        "name": "cp", "category": "文件操作", "subcategory": "复制",
        "syntax": "cp [options] source... dest",
        "example": ["cp file.txt backup.txt", "cp -r src/ dst/", "cp -i *.txt /target/", "cp -p file.txt /tmp/", "cp -rv /var/log/ ./logs/"],
        "description": "复制文件和目录。`-r` 递归复制目录，`-i` 覆盖前提示，`-v` 显示详情，`-p` 保留权限/时间戳，`-u` 只在源较新时覆盖。批量复制多个文件时 dest 必须是已存在的目录。",
        "tags": ["复制", "拷贝"], "aliases": [], "level": "入门", "popularity": 95
    },
    {
        "name": "mv", "category": "文件操作", "subcategory": "移动",
        "syntax": "mv [options] source... dest",
        "example": ["mv old.txt new.txt", "mv file.txt /target/", "mv -i src/* dst/", "mv file1 file2 file3 /dst/", "mv -n latest.log archive/"],
        "description": "移动或重命名文件与目录。当目标不是已存在目录时为重命名；目标是已存在目录时把源放进去。`-i` 覆盖前提示，`-f` 强制覆盖不提示，`-n` 不覆盖已存在文件。同一文件系统内 mv 是 rename 系统调用，瞬时完成。",
        "tags": ["移动", "重命名"], "aliases": [], "level": "入门", "popularity": 92
    },
    {
        "name": "rm", "category": "文件操作", "subcategory": "删除",
        "syntax": "rm [options] file...",
        "example": ["rm file.txt", "rm -rf dir/", "rm -i *.log", "rm -v tmp/*", "rm -d empty_dir/"],
        "description": "删除文件或目录。`-r` 递归删除目录及其内容，`-f` 强制删除不提示，`-i` 删除前逐个确认，`-v` 显示详情，`-d` 删除空目录。`rm -rf /` 是危险操作，新手请勿尝试。",
        "tags": ["删除", "移除"], "aliases": [], "level": "入门", "popularity": 90
    },
    {
        "name": "mkdir", "category": "文件操作", "subcategory": "创建目录",
        "syntax": "mkdir [options] directory...",
        "example": ["mkdir new_dir", "mkdir -p a/b/c/d", "mkdir -m 755 project", "mkdir dir1 dir2 dir3", "mkdir -v logs/{a,b,c}"],
        "description": "创建目录。`-p` 递归创建多级目录（父目录不存在时一并创建），`-m` 指定权限模式，`-v` 显示创建详情。支持一次创建多个目录，或用花括号展开创建带子目录的多个目录。",
        "tags": ["创建", "目录", "文件夹"], "aliases": [], "level": "入门", "popularity": 88
    },
    {
        "name": "rmdir", "category": "文件操作", "subcategory": "删除目录",
        "syntax": "rmdir [options] directory...",
        "example": ["rmdir empty_dir", "rmdir -p a/b/c", "rmdir --ignore-fail-on-non-empty dir", "rmdir -v tmp/"],
        "description": "删除空目录。`-p` 递归删除空目录链（删除 c 后若 b 也空则一并删除），`--ignore-fail-on-non-empty` 忽略非空错误。要删除非空目录请用 `rm -r`。",
        "tags": ["删除", "目录"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "touch", "category": "文件操作", "subcategory": "创建空文件",
        "syntax": "touch [options] file...",
        "example": ["touch new.txt", "touch -t 202601010000 file", "touch -a file", "touch -m file", "touch file{1..5}.txt"],
        "description": "创建空文件或更新文件时间戳。如果文件不存在则创建空文件；如果存在则更新访问时间和修改时间为当前时间。`-t` 指定具体时间，`-a` 只更新访问时间，`-m` 只更新修改时间。",
        "tags": ["创建", "时间戳", "空文件"], "aliases": [], "level": "入门", "popularity": 70
    },
    {
        "name": "ln", "category": "文件操作", "subcategory": "链接",
        "syntax": "ln [options] target linkname",
        "example": ["ln file.txt hardlink.txt", "ln -s /path/to/file symlink", "ln -sf new_source old_link", "ln -s ~/projects ~/code"],
        "description": "创建链接（默认硬链接）。`-s` 创建符号链接（软链接，类似 Windows 快捷方式，可跨文件系统）。删除源文件后硬链接仍可访问内容，软链接则失效。`ln -sf` 强制覆盖已存在的链接。",
        "tags": ["链接", "软链接", "硬链接", "快捷方式"], "aliases": [], "level": "进阶", "popularity": 65
    },
    {
        "name": "chmod", "category": "文件操作", "subcategory": "权限",
        "syntax": "chmod [options] mode file...",
        "example": ["chmod 755 script.sh", "chmod -R 644 dir/", "chmod u+x file", "chmod +x run.sh", "chmod -R go-w data/"],
        "description": "修改文件权限。数字模式：`755` = rwxr-xr-x，符号模式：`u+x` 给拥有者加执行权限。`-R` 递归修改目录内容。常用场景：脚本加执行权限 `chmod +x script.sh`。",
        "tags": ["权限", "可执行"], "aliases": [], "level": "进阶", "popularity": 80
    },
    {
        "name": "chown", "category": "文件操作", "subcategory": "权限",
        "syntax": "chown [options] user[:group] file...",
        "example": ["chown user file.txt", "chown user:group dir/", "chown -R www-data:www-data /var/www", "chown :group file", "chown --from=old_user new_user *"],
        "description": "修改文件拥有者和所属组。`user:group` 同时修改用户和组，`:group` 只改组，`-R` 递归。常用于 Web 服务器部署后修改文件归属。普通用户只能修改自己拥有的文件。",
        "tags": ["权限", "用户", "归属"], "aliases": [], "level": "进阶", "popularity": 60
    },

    # 文件查看 (5)
    {
        "name": "cat", "category": "文件查看", "subcategory": "输出全文",
        "syntax": "cat [options] [file...]",
        "example": ["cat file.txt", "cat -n file.txt", "cat file1 file2 > combined", "cat file | less", "cat -A file.txt"],
        "description": "连接并输出文件内容到标准输出。`-n` 显示行号，`-A` 显示特殊字符（换行符/制表符）。常用于小文件查看或合并文件；大文件请用 `less` 或 `more` 分页。",
        "tags": ["查看", "输出", "合并"], "aliases": [], "level": "入门", "popularity": 85
    },
    {
        "name": "less", "category": "文件查看", "subcategory": "分页查看",
        "syntax": "less [options] file",
        "example": ["less file.txt", "less -N file.log", "less +F file.log", "less -S wide.txt", "ps aux | less"],
        "description": "分页查看文件，支持前滚/后滚。`/` 搜索，`n` 下一个匹配，`G` 跳末尾，`g` 跳开头，`q` 退出。比 `more` 更强大，是查看大文件和日志的首选。",
        "tags": ["分页", "查看", "日志"], "aliases": [], "level": "入门", "popularity": 78
    },
    {
        "name": "head", "category": "文件查看", "subcategory": "查看开头",
        "syntax": "head [options] [file...]",
        "example": ["head file.txt", "head -n 20 file.log", "head -c 100 file", "head -n 5 *.csv"],
        "description": "显示文件开头部分（默认 10 行）。`-n N` 指定行数，`-c N` 指定字节数。常用于快速查看文件头（CSV 表头、配置开头）。",
        "tags": ["查看", "开头"], "aliases": [], "level": "入门", "popularity": 65
    },
    {
        "name": "tail", "category": "文件查看", "subcategory": "查看末尾",
        "syntax": "tail [options] [file...]",
        "example": ["tail file.log", "tail -n 50 file", "tail -f /var/log/syslog", "tail -F app.log", "tail -n +2 skip_header"],
        "description": "显示文件末尾部分（默认 10 行）。`-f` 实时跟踪文件新增内容（看日志神器），`-F` 同 `-f` 但文件名被替换或文件被重建时继续追踪。`-n +2` 从第 2 行开始输出（跳过表头）。",
        "tags": ["查看", "末尾", "日志", "实时"], "aliases": [], "level": "入门", "popularity": 88
    },
    {
        "name": "file", "category": "文件查看", "subcategory": "识别类型",
        "syntax": "file [options] file...",
        "example": ["file unknown.bin", "file -i file.txt", "file *", "file -z archive.zip"],
        "description": "识别文件类型（通过读取文件头魔术字节）。`-i` 输出 MIME 类型。文件无扩展名或扩展名错误时用于判断真实类型。",
        "tags": ["类型", "识别"], "aliases": [], "level": "进阶", "popularity": 50
    },

    # 文本处理 (8)
    {
        "name": "grep", "category": "文本处理", "subcategory": "搜索文本",
        "syntax": "grep [options] pattern [file...]",
        "example": ["grep 'error' log.txt", "grep -rn 'TODO' src/", "grep -i 'warn' *.log", "grep -v '^#' config", "grep -E '^[0-9]+' data.txt"],
        "description": "在文件中搜索匹配模式的行。`-r` 递归目录，`-n` 显示行号，`-i` 忽略大小写，`-v` 反向匹配（输出不匹配的行），`-E` 扩展正则。`ps aux | grep nginx` 是经典用法。",
        "tags": ["搜索", "过滤", "正则"], "aliases": [], "level": "入门", "popularity": 98
    },
    {
        "name": "sed", "category": "文本处理", "subcategory": "流编辑",
        "syntax": "sed [options] 'script' [file...]",
        "example": ["sed 's/old/new/' file", "sed -i 's/old/new/g' file", "sed -n '1,10p' file", "sed '/^#/d' config", "sed -e 's/a/A/' -e 's/b/B/' file"],
        "description": "流编辑器，按行处理文本。常用：替换 `s/old/new/g`（`g` 全局），删除指定行 `Nd`，打印指定行 `Np`。`-i` 直接修改原文件（谨慎使用）。支持正则。",
        "tags": ["编辑", "替换", "正则"], "aliases": [], "level": "进阶", "popularity": 82
    },
    {
        "name": "awk", "category": "文本处理", "subcategory": "字段处理",
        "syntax": "awk [options] 'program' [file...]",
        "example": ["awk '{print $1}' file", "awk -F: '{print $1}' /etc/passwd", "awk '$3 > 100' file", "awk '{sum+=$1} END {print sum}' data", "awk 'NR>1' skip_header.csv"],
        "description": "强大的文本处理语言，按字段（默认空格分割）处理。`$1` 第一列，`$NF` 最后一列，`NR` 行号，`END` 处理完后执行。常用于日志分析、CSV 处理、报表生成。",
        "tags": ["字段", "处理", "脚本"], "aliases": [], "level": "进阶", "popularity": 75
    },
    {
        "name": "sort", "category": "文本处理", "subcategory": "排序",
        "syntax": "sort [options] [file...]",
        "example": ["sort file.txt", "sort -n numbers", "sort -r file", "sort -u unique_sort", "sort -k2 file"],
        "description": "对文本行排序（默认字典序）。`-n` 数值排序，`-r` 逆序，`-u` 去重（等同 `sort | uniq`），`-k N` 按第 N 列排序。常与 `uniq` 组合去重统计。",
        "tags": ["排序", "去重"], "aliases": [], "level": "入门", "popularity": 70
    },
    {
        "name": "uniq", "category": "文本处理", "subcategory": "去重",
        "syntax": "uniq [options] [input [output]]",
        "example": ["uniq file", "uniq -c file", "uniq -d file", "sort file | uniq", "uniq -u file"],
        "description": "去除相邻重复行（输入必须先 sort）。`-c` 在每行前显示出现次数，`-d` 只输出重复过的行，`-u` 只输出唯一的行。常配合 `sort file | uniq -c | sort -rn` 统计频次。",
        "tags": ["去重", "统计"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "wc", "category": "文本处理", "subcategory": "统计",
        "syntax": "wc [options] [file...]",
        "example": ["wc file.txt", "wc -l file", "wc -w file", "wc -c file", "ls | wc -l"],
        "description": "统计行数、词数、字节数。`-l` 行数（最常用），`-w` 词数，`-c` 字节数，`-m` 字符数。`grep -c pattern file | wc -l` 统计匹配行数。",
        "tags": ["统计", "计数"], "aliases": [], "level": "入门", "popularity": 72
    },
    {
        "name": "cut", "category": "文本处理", "subcategory": "列提取",
        "syntax": "cut [options] [file...]",
        "example": ["cut -d: -f1 /etc/passwd", "cut -d, -f1-3 data.csv", "cut -c1-10 file", "cut -f2 file"],
        "description": "按列提取字段。`-d` 指定分隔符，`-f N` 第 N 列，`-c N-M` 按字符位置。常用于 CSV/TSV 处理：`cut -d, -f1 data.csv` 提取第一列。",
        "tags": ["列", "提取", "CSV"], "aliases": [], "level": "进阶", "popularity": 58
    },
    {
        "name": "tr", "category": "文本处理", "subcategory": "字符转换",
        "syntax": "tr [options] set1 [set2]",
        "example": ["tr 'a-z' 'A-Z' < file", "tr -d '\\r' < win.txt > unix.txt", "tr -s ' ' < file", "echo 'abc' | tr 'a' 'x'"],
        "description": "字符替换/删除/压缩。`tr 'a-z' 'A-Z'` 小写转大写，`-d` 删除指定字符（如 `\\r` Windows 换行），`-s` 压缩重复字符。常配合重定向用于格式转换。",
        "tags": ["转换", "删除", "字符"], "aliases": [], "level": "进阶", "popularity": 55
    },

    # 文件查找 (5)
    {
        "name": "find", "category": "文件查找", "subcategory": "递归搜索",
        "syntax": "find [path] [expression]",
        "example": ["find /home -name '*.txt'", "find . -type f -name '*.py'", "find . -size +100M", "find . -mtime -7", "find . -maxdepth 2 -name '*.log' -delete"],
        "description": "递归搜索目录树，按名称/大小/时间/类型等条件过滤文件或目录。GNU find 支持丰富的表达式（test、action、operator），是日常排查、日志归档、清理大文件时最常用的工具。",
        "tags": ["搜索", "递归"], "aliases": [], "level": "入门", "popularity": 95
    },
    {
        "name": "locate", "category": "文件查找", "subcategory": "数据库搜索",
        "syntax": "locate [options] pattern",
        "example": ["locate nginx.conf", "locate -i readme.md", "locate -c '*.log'", "sudo updatedb"],
        "description": "基于数据库的文件查找，速度远快于 `find`。数据库通常每天自动更新（`updatedb`），新建文件需手动更新才能搜到。`-i` 忽略大小写，`-c` 只显示匹配数。",
        "tags": ["搜索", "快速"], "aliases": [], "level": "进阶", "popularity": 50
    },
    {
        "name": "which", "category": "文件查找", "subcategory": "命令位置",
        "syntax": "which [options] program...",
        "example": ["which python", "which -a gcc", "which node"],
        "description": "显示命令的完整路径（依据 PATH 环境变量）。`-a` 显示所有匹配路径（不只第一个）。用于判断命令是否存在或具体是哪个版本。",
        "tags": ["路径", "命令"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "whereis", "category": "文件查找", "subcategory": "命令位置",
        "syntax": "whereis [options] program...",
        "example": ["whereis python", "whereis -b gcc", "whereis -m bash"],
        "description": "查找命令的二进制、源码和 man 帮助页位置。`-b` 只找二进制，`-m` 只找帮助页。比 `which` 范围更广。",
        "tags": ["路径", "二进制", "帮助"], "aliases": [], "level": "进阶", "popularity": 35
    },
    {
        "name": "xargs", "category": "文件查找", "subcategory": "构造命令",
        "syntax": "xargs [options] [command]",
        "example": ["find . -name '*.log' | xargs rm", "find . -name '*.txt' | xargs grep 'pattern'", "echo 'a b c' | xargs -n1 echo", "ls *.txt | xargs -I{} cp {} backup/"],
        "description": "从标准输入构造命令行参数。常配合 `find`：`find . -name '*.log' | xargs rm`。`-I{}` 自定义替换符。处理含空格文件名需加 `-d '\\n'`。",
        "tags": ["管道", "参数", "批量"], "aliases": [], "level": "进阶", "popularity": 65
    },

    # 系统信息 (8)
    {
        "name": "uname", "category": "系统信息", "subcategory": "内核信息",
        "syntax": "uname [options]",
        "example": ["uname", "uname -a", "uname -r", "uname -m", "uname -s"],
        "description": "显示系统信息（内核）。`-a` 全部信息，`-r` 内核版本，`-m` 机器架构（x86_64 / aarch64），`-s` 内核名（Linux）。Docker 容器里排查架构最常用。",
        "tags": ["内核", "版本", "架构"], "aliases": [], "level": "入门", "popularity": 65
    },
    {
        "name": "hostname", "category": "系统信息", "subcategory": "主机名",
        "syntax": "hostname [options]",
        "example": ["hostname", "hostname -I", "hostname -f", "sudo hostname newname"],
        "description": "显示或设置主机名。`-I` 显示所有 IP 地址，`-f` 显示完全限定域名（FQDN）。修改主机名需编辑 `/etc/hostname` 并重启或用 `hostnamectl`。",
        "tags": ["主机", "网络"], "aliases": [], "level": "入门", "popularity": 55
    },
    {
        "name": "uptime", "category": "系统信息", "subcategory": "运行时长",
        "syntax": "uptime [options]",
        "example": ["uptime", "uptime -p", "uptime -s"],
        "description": "显示系统运行时长、负载均衡。`-p` 美化输出（如 `up 3 days`），`-s` 显示启动时间。`load average: 0.50, 0.60, 0.70` 是过去 1/5/15 分钟的平均负载。",
        "tags": ["运行时长", "负载"], "aliases": [], "level": "入门", "popularity": 45
    },
    {
        "name": "date", "category": "系统信息", "subcategory": "时间日期",
        "syntax": "date [options] [+format]",
        "example": ["date", "date '+%Y-%m-%d %H:%M:%S'", "date '+%s'", "date -d 'yesterday'", "date -s '2026-01-01 00:00:00'"],
        "description": "显示或设置系统时间。`+%Y-%m-%d` 自定义格式，`+%s` Unix 时间戳，`-d 'yesterday'` 相对时间。设置时间需 root：`sudo date -s '...'`，生产环境建议用 NTP 同步。",
        "tags": ["时间", "日期", "时间戳"], "aliases": [], "level": "入门", "popularity": 65
    },
    {
        "name": "cal", "category": "系统信息", "subcategory": "日历",
        "syntax": "cal [options] [month] [year]",
        "example": ["cal", "cal 2026", "cal 12 2026", "cal -3", "ncal -w"],
        "description": "显示日历。默认当前月份，`cal 2026` 显示全年，`-3` 显示上月/本月/下月。`ncal` 显示更紧凑的纵向布局。",
        "tags": ["日历", "日期"], "aliases": ["ncal"], "level": "入门", "popularity": 30
    },
    {
        "name": "who", "category": "系统信息", "subcategory": "登录用户",
        "syntax": "who [options]",
        "example": ["who", "who -b", "who -q", "whoami", "w"],
        "description": "显示当前登录用户列表。`-b` 显示系统启动时间。`whoami` 显示当前用户名，`w` 显示用户及他们在做什么。",
        "tags": ["用户", "登录"], "aliases": ["whoami"], "level": "入门", "popularity": 40
    },
    {
        "name": "env", "category": "系统信息", "subcategory": "环境变量",
        "syntax": "env [options] [name=value...] [command]",
        "example": ["env", "env | grep PATH", "env -i command", "env VAR=value command"],
        "description": "显示所有环境变量或在新环境中运行命令。`env | grep PATH` 看 PATH 路径，`env VAR=value command` 临时设环境变量运行命令。",
        "tags": ["环境变量"], "aliases": [], "level": "入门", "popularity": 55
    },
    {
        "name": "history", "category": "系统信息", "subcategory": "历史命令",
        "syntax": "history [n]",
        "example": ["history", "history 20", "history | grep pattern", "history -c", "history -d 100"],
        "description": "显示历史命令列表（默认 1000 条，存储在 `~/.bash_history`）。`!N` 执行第 N 条历史命令，`!!` 执行上一条，`!pattern` 执行最近的匹配命令。",
        "tags": ["历史", "快捷"], "aliases": [], "level": "入门", "popularity": 60
    },

    # 进程管理 (8)
    {
        "name": "ps", "category": "进程管理", "subcategory": "查看进程",
        "syntax": "ps [options]",
        "example": ["ps aux", "ps -ef", "ps aux | grep nginx", "ps -u user", "ps -ef --forest"],
        "description": "显示进程快照。`ps aux` 最常用（a 所有用户，u 用户友好格式，x 无终端进程），`ps -ef` 是 System V 风格。配合 `grep` 找进程：`ps aux | grep nginx`。",
        "tags": ["进程", "查看"], "aliases": [], "level": "入门", "popularity": 92
    },
    {
        "name": "top", "category": "进程管理", "subcategory": "实时进程",
        "syntax": "top [options]",
        "example": ["top", "top -u user", "top -p 1234", "top -bn1 | head -20", "htop"],
        "description": "实时显示进程和系统资源使用（CPU/内存）。交互式：`P` 按 CPU 排序，`M` 按内存排序，`k` kill 进程，`q` 退出。`htop` 是更友好的替代品。",
        "tags": ["实时", "CPU", "内存"], "aliases": ["htop"], "level": "入门", "popularity": 95
    },
    {
        "name": "kill", "category": "进程管理", "subcategory": "结束进程",
        "syntax": "kill [signal] PID...",
        "example": ["kill 1234", "kill -9 1234", "kill -15 1234", "kill -l", "pkill nginx"],
        "description": "向进程发送信号。默认 `SIGTERM`（15）让进程优雅退出；`-9` (`SIGKILL`) 强制终止（不给清理机会，可能丢数据）。`-l` 列出所有信号。`pkill 进程名` 按名结束。",
        "tags": ["结束", "信号"], "aliases": ["pkill", "killall"], "level": "入门", "popularity": 85
    },
    {
        "name": "jobs", "category": "进程管理", "subcategory": "后台任务",
        "syntax": "jobs [options]",
        "example": ["jobs", "jobs -l", "sleep 100 &", "fg %1", "bg %1"],
        "description": "显示当前 shell 的后台任务。`&` 让命令后台运行，`fg %N` 把任务调回前台，`bg %N` 让任务继续后台运行，`Ctrl+Z` 暂停任务。",
        "tags": ["后台", "任务"], "aliases": [], "level": "入门", "popularity": 55
    },
    {
        "name": "bg", "category": "进程管理", "subcategory": "后台任务",
        "syntax": "bg [job_spec]",
        "example": ["bg %1", "Ctrl+Z; bg", "nohup command &"],
        "description": "让暂停的任务在后台继续运行。常与 `Ctrl+Z`（暂停）+ `bg` 组合使用。`nohup command &` 启动一个不受终端关闭影响的进程。",
        "tags": ["后台", "恢复"], "aliases": [], "level": "进阶", "popularity": 50
    },
    {
        "name": "fg", "category": "进程管理", "subcategory": "前台任务",
        "syntax": "fg [job_spec]",
        "example": ["fg", "fg %1", "fg %2"],
        "description": "把后台任务调回前台运行。`fg` 默认调最近的后台任务，`fg %N` 调指定编号。",
        "tags": ["前台", "恢复"], "aliases": [], "level": "进阶", "popularity": 45
    },
    {
        "name": "nohup", "category": "进程管理", "subcategory": "脱离终端",
        "syntax": "nohup command [args]...",
        "example": ["nohup python server.py &", "nohup ./script.sh > out.log 2>&1 &", "nohup command &"],
        "description": "运行命令，忽略挂起信号（SIGHUP），即关闭终端后进程继续运行。常与 `&` 配合后台启动。重定向输出到 `nohup.out`（默认）或自定义文件。",
        "tags": ["脱离终端", "后台"], "aliases": [], "level": "进阶", "popularity": 60
    },
    {
        "name": "free", "category": "进程管理", "subcategory": "内存使用",
        "syntax": "free [options]",
        "example": ["free", "free -h", "free -m", "free -s 5", "watch -n 1 free"],
        "description": "显示内存使用情况。`-h` 人类可读，`-s N` 每 N 秒刷新，`-m` 以 MB 显示。关注 `available` 列（实际可用），不是 `free`（未使用）。",
        "tags": ["内存", "资源"], "aliases": [], "level": "入门", "popularity": 70
    },

    # 网络工具 (10)
    {
        "name": "ping", "category": "网络工具", "subcategory": "连通性测试",
        "syntax": "ping [options] host",
        "example": ["ping google.com", "ping -c 4 8.8.8.8", "ping -i 2 host", "ping -s 1000 host", "ping6 ::1"],
        "description": "测试到目标主机的网络连通性。默认持续发送，需 `Ctrl+C` 停止；`-c N` 指定发送次数。返回的 `time=` 是往返延迟。`ping -c 4 8.8.8.8` 测试 4 次。",
        "tags": ["网络", "测试", "延迟"], "aliases": ["ping6"], "level": "入门", "popularity": 88
    },
    {
        "name": "curl", "category": "网络工具", "subcategory": "HTTP 请求",
        "syntax": "curl [options] URL",
        "example": ["curl https://example.com", "curl -O url", "curl -L -o file url", "curl -X POST -d 'data' url", "curl -H 'Auth: token' url"],
        "description": "强大的 HTTP/FTP 请求工具。`-O` 保持文件名下载，`-L` 跟随重定向，`-X` 指定方法，`-d` POST 数据，`-H` 自定义头，`-I` 只看响应头。调试 API 的神器。",
        "tags": ["HTTP", "下载", "请求"], "aliases": [], "level": "进阶", "popularity": 92
    },
    {
        "name": "wget", "category": "网络工具", "subcategory": "下载工具",
        "syntax": "wget [options] URL...",
        "example": ["wget https://example.com/file.zip", "wget -c url", "wget -r -np url", "wget -O save_name url"],
        "description": "命令行下载工具，支持 HTTP/HTTPS/FTP。`-c` 断点续传，`-r` 递归下载整站，`-O` 指定保存文件名。比 `curl` 更适合大文件下载和递归镜像。",
        "tags": ["下载", "HTTP"], "aliases": [], "level": "进阶", "popularity": 80
    },
    {
        "name": "ssh", "category": "网络工具", "subcategory": "远程登录",
        "syntax": "ssh [options] user@host",
        "example": ["ssh user@server.com", "ssh -p 2222 user@host", "ssh -i ~/.ssh/key user@host", "ssh -L 8080:localhost:80 user@host"],
        "description": "安全远程登录。`-p N` 指定端口，`-i key` 用密钥登录，`-L` 本地端口转发（本地 8080 转远程 80）。生产环境推荐密钥 + 禁用密码登录。",
        "tags": ["远程", "登录", "安全"], "aliases": [], "level": "进阶", "popularity": 95
    },
    {
        "name": "scp", "category": "网络工具", "subcategory": "远程复制",
        "syntax": "scp [options] source... target",
        "example": ["scp file.txt user@host:/path/", "scp -r dir/ user@host:/", "scp user@host:/file ./", "scp -P 2222 file user@host:"],
        "description": "基于 SSH 的安全复制。本地到远程：`scp file user@host:/path/`；远程到本地：`scp user@host:/file ./`。`-r` 递归目录，`-P N` 指定端口（注意是大写 P）。",
        "tags": ["复制", "远程", "SSH"], "aliases": [], "level": "进阶", "popularity": 78
    },
    {
        "name": "rsync", "category": "网络工具", "subcategory": "同步",
        "syntax": "rsync [options] source... target",
        "example": ["rsync -av src/ dst/", "rsync -avz -e ssh dir/ user@host:/path/", "rsync -av --delete src/ dst/", "rsync -av --exclude='*.tmp' src/ dst/"],
        "description": "增量同步工具，比 `scp` 快（只传变化部分）。`-a` 归档模式（保留权限/时间），`-v` 显示详情，`-z` 压缩传输，`--delete` 镜像删除。备份和部署首选。",
        "tags": ["同步", "增量", "备份"], "aliases": [], "level": "进阶", "popularity": 85
    },
    {
        "name": "ifconfig", "category": "网络工具", "subcategory": "网络接口",
        "syntax": "ifconfig [interface] [options]",
        "example": ["ifconfig", "ifconfig eth0", "ifconfig eth0 192.168.1.100", "sudo ifconfig eth0 down"],
        "description": "显示/配置网络接口（旧工具，逐渐被 `ip` 取代）。显示 IP、MAC、收发包统计等。修改配置：`sudo ifconfig eth0 192.168.1.100 netmask 255.255.255.0`。",
        "tags": ["网络", "IP", "接口"], "aliases": [], "level": "进阶", "popularity": 60
    },
    {
        "name": "ip", "category": "网络工具", "subcategory": "网络配置",
        "syntax": "ip [options] OBJECT COMMAND",
        "example": ["ip addr", "ip link", "ip route", "ip addr add 192.168.1.100/24 dev eth0", "ip -s link"],
        "description": "新一代网络配置工具，替代 `ifconfig`/`route`/`arp`。`ip addr` 显示地址，`ip link` 显示链路，`ip route` 显示路由，`ip neigh` 显示 ARP。修改即时生效。",
        "tags": ["网络", "路由", "IP"], "aliases": [], "level": "进阶", "popularity": 75
    },
    {
        "name": "netstat", "category": "网络工具", "subcategory": "网络连接",
        "syntax": "netstat [options]",
        "example": ["netstat -tulpn", "netstat -an", "netstat -r", "netstat -tulpn | grep :80"],
        "description": "显示网络连接/监听端口/路由表。`-tulpn`（TCP+UDP+监听+数字地址+进程名）最常用。`netstat -tulpn | grep :80` 查谁占用了 80 端口（需 root）。",
        "tags": ["端口", "连接", "监听"], "aliases": [], "level": "进阶", "popularity": 70
    },
    {
        "name": "ss", "category": "网络工具", "subcategory": "网络状态",
        "syntax": "ss [options]",
        "example": ["ss -tulpn", "ss -tan", "ss -s", "ss -tn state established"],
        "description": "替代 `netstat` 的现代工具，速度更快（直接读 `/proc`）。`-tulpn` 显示所有监听端口，`-s` 汇总统计，`-tan state established` 查已建立的连接。",
        "tags": ["端口", "连接", "Socket"], "aliases": [], "level": "进阶", "popularity": 65
    },

    # 压缩归档 (5)
    {
        "name": "tar", "category": "压缩归档", "subcategory": "归档",
        "syntax": "tar [options] [archive] [file...]",
        "example": ["tar -cvf archive.tar dir/", "tar -xvf archive.tar", "tar -czvf archive.tar.gz dir/", "tar -xzvf archive.tar.gz", "tar -tjvf archive.tar.bz2"],
        "description": "归档工具（不压缩）。`-c` 创建，`-x` 提取，`-v` 详情，`-f` 指定文件名，`-z` gzip 压缩（.tar.gz），`-j` bzip2（.tar.bz2），`-J` xz（.tar.xz），`-t` 列出内容不解压。",
        "tags": ["归档", "压缩", "打包"], "aliases": [], "level": "入门", "popularity": 90
    },
    {
        "name": "zip", "category": "压缩归档", "subcategory": "压缩",
        "syntax": "zip [options] archive file...",
        "example": ["zip archive.zip file.txt", "zip -r archive.zip dir/", "zip -e secure.zip file", "zip -9 max.zip file"],
        "description": "创建 zip 压缩包（与 Windows 兼容）。`-r` 递归目录，`-e` 加密（会提示输入密码），`-9` 最大压缩率。解压用 `unzip`。",
        "tags": ["压缩", "zip"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "unzip", "category": "压缩归档", "subcategory": "解压",
        "syntax": "unzip [options] archive",
        "example": ["unzip file.zip", "unzip -d target_dir file.zip", "unzip -l file.zip", "unzip -o file.zip"],
        "description": "解压 zip 文件。`-d dir` 解压到指定目录，`-l` 列出内容，`-o` 覆盖已存在文件不解压时询问。",
        "tags": ["解压", "zip"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "gzip", "category": "压缩归档", "subcategory": "压缩",
        "syntax": "gzip [options] [file...]",
        "example": ["gzip file.txt", "gzip -k file.txt", "gzip -d file.gz", "gzip -9 file"],
        "description": "gzip 压缩（生成 .gz 文件，源文件被删除除非加 `-k`）。`gzip -d` 或 `gunzip` 解压。常配合 tar：`tar -czf` 创建 .tar.gz。",
        "tags": ["压缩", "gz"], "aliases": ["gunzip"], "level": "进阶", "popularity": 55
    },
    {
        "name": "xz", "category": "压缩归档", "subcategory": "压缩",
        "syntax": "xz [options] [file...]",
        "example": ["xz file", "xz -k file", "xz -d file.xz", "tar -cJf archive.tar.xz dir/"],
        "description": "高压缩率工具（生成 .xz，常用于 Linux 内核包）。比 gzip 慢但压缩率高。`xz -d` 或 `unxz` 解压。`tar -cJf` 创建 .tar.xz。",
        "tags": ["压缩", "xz"], "aliases": ["unxz"], "level": "进阶", "popularity": 30
    },

    # 权限用户 (5)
    {
        "name": "sudo", "category": "权限用户", "subcategory": "提权",
        "syntax": "sudo [options] command",
        "example": ["sudo apt update", "sudo !!", "sudo -i", "sudo -u user command"],
        "description": "以 root（或其他用户）权限执行命令。需在 `/etc/sudoers` 配置。`sudo !!` 重新执行上一条命令并加 sudo。`sudo -i` 进入 root shell。",
        "tags": ["权限", "root", "管理员"], "aliases": [], "level": "入门", "popularity": 95
    },
    {
        "name": "su", "category": "权限用户", "subcategory": "切换用户",
        "syntax": "su [options] [user]",
        "example": ["su", "su -", "su user", "su -c 'command' user"],
        "description": "切换用户身份。`su -` 切换到 root 并加载其环境（推荐）。需知道目标用户密码。生产环境推荐用 `sudo` 替代（更可控）。",
        "tags": ["用户", "切换"], "aliases": [], "level": "进阶", "popularity": 65
    },
    {
        "name": "useradd", "category": "权限用户", "subcategory": "用户管理",
        "syntax": "useradd [options] username",
        "example": ["sudo useradd newuser", "sudo useradd -m -s /bin/bash user", "sudo useradd -G sudo admin"],
        "description": "创建用户（需 root）。`-m` 创建家目录，`-s` 指定 shell，`-G` 加入附加组。Debian 系还需 `passwd` 设置密码。`adduser` 是更友好的交互式包装。",
        "tags": ["用户", "创建"], "aliases": ["adduser"], "level": "进阶", "popularity": 50
    },
    {
        "name": "passwd", "category": "权限用户", "subcategory": "密码",
        "syntax": "passwd [options] [user]",
        "example": ["passwd", "sudo passwd user", "passwd -l user"],
        "description": "修改密码（普通用户改自己，root 改任何人）。`passwd -l user` 锁定账号（不能登录），`-u` 解锁。",
        "tags": ["密码", "用户"], "aliases": [], "level": "进阶", "popularity": 55
    },
    {
        "name": "id", "category": "权限用户", "subcategory": "身份",
        "syntax": "id [options] [user]",
        "example": ["id", "id user", "id -u", "id -g", "id -G"],
        "description": "显示用户身份（UID/GID/组）。`-u` 只显示 UID，`-g` 只显示主组 GID，`-G` 显示所有附加组。脚本里判断用户身份常用。",
        "tags": ["身份", "用户", "组"], "aliases": [], "level": "进阶", "popularity": 45
    },

    # 磁盘存储 (6)
    {
        "name": "df", "category": "磁盘存储", "subcategory": "使用情况",
        "syntax": "df [options] [file...]",
        "example": ["df", "df -h", "df -T", "df -h /", "df -i"],
        "description": "显示文件系统磁盘空间使用。`-h` 人类可读（GB/MB），`-T` 显示文件系统类型，`-i` 显示 inode 使用。`df -h /` 看根分区占用。",
        "tags": ["磁盘", "空间", "存储"], "aliases": [], "level": "入门", "popularity": 80
    },
    {
        "name": "du", "category": "磁盘存储", "subcategory": "目录大小",
        "syntax": "du [options] [path...]",
        "example": ["du -sh dir/", "du -h --max-depth=1", "du -ah dir/", "du -h * | sort -h"],
        "description": "估算文件/目录磁盘占用。`-s` 只显示汇总，`-h` 人类可读，`--max-depth=1` 每层目录一个数字。`du -sh *` 查当前目录各子目录大小。",
        "tags": ["大小", "占用", "目录"], "aliases": [], "level": "入门", "popularity": 75
    },
    {
        "name": "mount", "category": "磁盘存储", "subcategory": "挂载",
        "syntax": "mount [options] [device] [directory]",
        "example": ["mount", "mount /dev/sdb1 /mnt", "mount -t nfs server:/share /mnt", "sudo umount /mnt"],
        "description": "挂载文件系统。`mount` 显示所有挂载；`mount /dev/sdb1 /mnt` 挂载分区到 /mnt；`-t nfs` 指定 NFS。卸载用 `umount`。",
        "tags": ["挂载", "文件系统"], "aliases": ["umount"], "level": "进阶", "popularity": 50
    },
    {
        "name": "lsblk", "category": "磁盘存储", "subcategory": "块设备",
        "syntax": "lsblk [options]",
        "example": ["lsblk", "lsblk -f", "lsblk -h", "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT"],
        "description": "树形显示块设备（磁盘/分区）。`-f` 显示文件系统类型和 UUID，`-o` 自定义列。比 `fdisk -l` 输出更直观。",
        "tags": ["块设备", "磁盘", "分区"], "aliases": [], "level": "进阶", "popularity": 45
    },
    {
        "name": "fdisk", "category": "磁盘存储", "subcategory": "分区",
        "syntax": "fdisk [options] device",
        "example": ["sudo fdisk -l", "sudo fdisk /dev/sdb"],
        "description": "磁盘分区工具（MBR）。`-l` 列出所有分区表。`fdisk /dev/sdb` 进入交互式分区管理（m 看帮助）。GPT 磁盘用 `gdisk` 或 `parted`。",
        "tags": ["分区", "MBR"], "aliases": ["gdisk", "parted"], "level": "进阶", "popularity": 40
    },
    {
        "name": "stat", "category": "磁盘存储", "subcategory": "文件信息",
        "syntax": "stat [options] file...",
        "example": ["stat file.txt", "stat -c '%s' file", "stat -c '%y' file", "stat /dev/sda"],
        "description": "显示文件/文件系统详细信息（大小/块/权限/时间戳/inode）。`-c` 自定义输出格式，`'%s'` 只输出大小（脚本常用），`'%y'` 修改时间。",
        "tags": ["元数据", "文件信息"], "aliases": [], "level": "进阶", "popularity": 45
    },

    # 软件包 (5)
    {
        "name": "apt", "category": "软件包", "subcategory": "Debian/Ubuntu",
        "syntax": "apt [options] command [package...]",
        "example": ["sudo apt update", "sudo apt install nginx", "sudo apt remove nginx", "apt search keyword", "apt list --installed"],
        "description": "Debian/Ubuntu 包管理器。`update` 更新索引，`install` 安装，`remove` 卸载（保留配置），`purge` 完全卸载（删配置），`search` 搜索，`upgrade` 升级所有包。",
        "tags": ["包管理", "Debian", "Ubuntu"], "aliases": ["apt-get", "apt-cache"], "level": "入门", "popularity": 92
    },
    {
        "name": "yum", "category": "软件包", "subcategory": "RHEL/CentOS",
        "syntax": "yum [options] command [package...]",
        "example": ["sudo yum install nginx", "sudo yum remove nginx", "yum search keyword", "sudo yum update"],
        "description": "RHEL/CentOS 老版本包管理器（已被 `dnf` 取代但仍可用）。`install` 安装，`remove` 卸载，`search` 搜索，`update` 升级。新版本 CentOS/RHEL 推荐用 `dnf`。",
        "tags": ["包管理", "RHEL", "CentOS"], "aliases": ["dnf"], "level": "进阶", "popularity": 60
    },
    {
        "name": "pacman", "category": "软件包", "subcategory": "Arch",
        "syntax": "pacman [options] [command] [package...]",
        "example": ["sudo pacman -Syu", "sudo pacman -S nginx", "sudo pacman -R nginx", "pacman -Ss keyword"],
        "description": "Arch Linux 包管理器。`-S` 安装（同步），`-Syu` 升级所有包，`-R` 卸载，`-Ss` 搜索。`pacman -S --needed pkg` 只装未装的。",
        "tags": ["包管理", "Arch"], "aliases": [], "level": "进阶", "popularity": 35
    },
    {
        "name": "pip", "category": "软件包", "subcategory": "Python",
        "syntax": "pip [options] command",
        "example": ["pip install requests", "pip install -r requirements.txt", "pip list", "pip install --upgrade pkg", "pip uninstall pkg"],
        "description": "Python 包管理器。`install` 安装（`-r` 从文件装），`list` 列出已装，`--upgrade` 升级，`uninstall` 卸载。推荐用 `pip3` 显式指定 Python 3。",
        "tags": ["Python", "包管理"], "aliases": ["pip3"], "level": "入门", "popularity": 88
    },
    {
        "name": "npm", "category": "软件包", "subcategory": "Node",
        "syntax": "npm [options] command",
        "example": ["npm install", "npm install pkg", "npm run dev", "npm list", "npm uninstall pkg"],
        "description": "Node.js 包管理器。`install` 安装依赖（无参数装 package.json 所有），`run` 跑脚本，`list` 列已装，`uninstall` 卸载。`npx` 可直接跑包命令。",
        "tags": ["Node", "包管理", "JavaScript"], "aliases": ["npx", "yarn"], "level": "入门", "popularity": 85
    },

    # 实用工具 (5)
    {
        "name": "alias", "category": "实用工具", "subcategory": "别名",
        "syntax": "alias [name[=value]]",
        "example": ["alias", "alias ll='ls -la'", "alias gs='git status'", "unalias ll"],
        "description": "定义/显示命令别名。`alias ll='ls -la'` 定义别名，临时生效；写入 `~/.bashrc` 永久生效。`unalias name` 删除别名。",
        "tags": ["别名", "快捷"], "aliases": ["unalias"], "level": "入门", "popularity": 55
    },
    {
        "name": "echo", "category": "实用工具", "subcategory": "输出",
        "syntax": "echo [options] [string...]",
        "example": ["echo 'hello'", "echo $PATH", "echo -e 'a\\nb'", "echo 'data' >> file"],
        "description": "输出字符串。`-e` 启用转义（`\\n`/`\\t`）。常用于脚本输出/调试/写入文件。`echo 'data' >> file` 追加内容。",
        "tags": ["输出", "打印"], "aliases": [], "level": "入门", "popularity": 80
    },
    {
        "name": "watch", "category": "实用工具", "subcategory": "周期执行",
        "syntax": "watch [options] command",
        "example": ["watch -n 1 'date'", "watch -n 5 'ls -la'", "watch -d 'free -h'", "watch -n 0.5 'ps aux | head'"],
        "description": "周期性执行命令并全屏显示。默认 2 秒一次。`-n N` 指定秒数，`-d` 高亮变化部分。`watch -n 1 'ls -la'` 每秒刷新文件列表。",
        "tags": ["周期", "监控"], "aliases": [], "level": "进阶", "popularity": 50
    },
    {
        "name": "screen", "category": "实用工具", "subcategory": "终端复用",
        "syntax": "screen [options] [command]",
        "example": ["screen -S session_name", "screen -ls", "screen -r session_name", "Ctrl+A d (分离)"],
        "description": "终端复用器，断开后任务继续运行。`screen -S name` 创建会话，`Ctrl+A d` 分离，`screen -r name` 恢复，`-ls` 列出会话。比 `tmux` 老但更普及。",
        "tags": ["终端", "后台"], "aliases": ["tmux"], "level": "进阶", "popularity": 60
    },
    {
        "name": "crontab", "category": "实用工具", "subcategory": "定时任务",
        "syntax": "crontab [options] [file]",
        "example": ["crontab -l", "crontab -e", "crontab -r", "0 2 * * * /script.sh"],
        "description": "管理定时任务。`-l` 列出，`-e` 编辑，`-r` 删除全部。格式：`分 时 日 月 周 命令`（`*` 任意）。`0 2 * * * /script.sh` 每天凌晨 2 点跑脚本。",
        "tags": ["定时", "计划任务"], "aliases": [], "level": "进阶", "popularity": 65
    },
]

# ───────────── Windows 命令数据 ─────────────
WINDOWS_COMMANDS = [
    # 文件操作 (15)
    {
        "name": "dir", "category": "文件操作", "subcategory": "列出目录",
        "syntax": "dir [drive:][path][filename] [options]",
        "example": ["dir", "dir /W", "dir /P", "dir *.txt", "dir /S /B *.log", "dir /A:H", "dir /T:W"],
        "description": "列出目录内容。`/W` 宽格式，`/P` 分页，`/S` 递归子目录，`/B` 简洁（只有文件名），`/A:H` 显示隐藏文件，`/T:W` 按最后写入时间排序。",
        "tags": ["列出", "目录"], "aliases": ["ls"], "level": "入门", "popularity": 98
    },
    {
        "name": "copy", "category": "文件操作", "subcategory": "复制",
        "syntax": "copy [/d] [/v] [/n] [/y] [/-y] [/z] [/l] [/a] [/b] source [destination]",
        "example": ["copy file.txt backup.txt", "copy file.txt D:\\backup\\", "copy *.txt D:\\backup\\", "copy /Y src\\*.log D:\\logs\\", "copy /Z \\\\server\\share\\file.txt"],
        "description": "复制一个或多个文件。`/Y` 覆盖现有文件不提示，`/-Y` 强制确认，`/Z` 可恢复模式（网络中断后可继续）。PowerShell 中 `copy` 是 `Copy-Item` 的别名。",
        "tags": ["复制", "拷贝"], "aliases": [], "level": "入门", "popularity": 85
    },
    {
        "name": "xcopy", "category": "文件操作", "subcategory": "复制",
        "syntax": "xcopy source [destination] [options]",
        "example": ["xcopy src dst /E /I", "xcopy src dst /S", "xcopy src dst /Y", "xcopy C:\\data D:\\backup /E /H /K"],
        "description": "增强版 copy，支持目录复制。`/E` 复制所有子目录（包括空），`/S` 复制非空子目录，`/I` 假设目标是目录，`/Y` 不提示覆盖，`/H` 含隐藏/系统文件。",
        "tags": ["复制", "目录", "递归"], "aliases": [], "level": "进阶", "popularity": 75
    },
    {
        "name": "robocopy", "category": "文件操作", "subcategory": "高级复制",
        "syntax": "robocopy <source> <destination> [file] [options]",
        "example": ["robocopy C:\\src D:\\dst /E", "robocopy C:\\src D:\\dst /MIR", "robocopy C:\\src D:\\dst /Z /MT:8", "robocopy C:\\src D:\\dst /LOG:copy.log"],
        "description": "可靠文件复制（替代 xcopy）。`/E` 含空目录，`/MIR` 镜像（删目标多余），`/Z` 可重启模式，`/MT:N` 多线程，`/LOG` 输出日志。比 xcopy 更强大，是 Windows 备份首选。",
        "tags": ["复制", "镜像", "备份"], "aliases": [], "level": "进阶", "popularity": 70
    },
    {
        "name": "move", "category": "文件操作", "subcategory": "移动",
        "syntax": "move [options] source destination",
        "example": ["move file.txt D:\\backup\\", "move *.log archive\\", "move /Y old.txt new.txt", "move C:\\src C:\\dst"],
        "description": "移动文件或重命名。`/Y` 不提示覆盖。`move file.txt new.txt` 是重命名；`move *.log archive\\` 把所有 log 移到 archive 目录。",
        "tags": ["移动", "重命名"], "aliases": ["mv", "ren"], "level": "入门", "popularity": 80
    },
    {
        "name": "rename", "category": "文件操作", "subcategory": "重命名",
        "syntax": "rename [drive:][path]filename1 filename2",
        "example": ["ren file.txt new.txt", "ren *.txt *.bak", "ren report.* report_final.*"],
        "description": "重命名文件或目录（不能跨盘）。支持通配符：`ren *.txt *.bak` 把所有 .txt 改 .bak。注意 PowerShell 中是 `Rename-Item`。",
        "tags": ["重命名", "改名"], "aliases": ["ren"], "level": "入门", "popularity": 75
    },
    {
        "name": "del", "category": "文件操作", "subcategory": "删除",
        "syntax": "del [options] filename",
        "example": ["del file.txt", "del *.tmp", "del /S /Q *.log", "del /F file.txt", "del /P *.txt"],
        "description": "删除一个或多个文件。`/S` 递归子目录，`/Q` 静默模式（不提示），`/F` 强制删除只读，`/P` 删除前确认。**不会**移到回收站，直接永久删除。",
        "tags": ["删除", "移除"], "aliases": ["erase"], "level": "入门", "popularity": 88
    },
    {
        "name": "rmdir", "category": "文件操作", "subcategory": "删除目录",
        "syntax": "rmdir [options] directory...",
        "example": ["rmdir empty_dir", "rmdir /S /Q dir", "rmdir C:\\temp"],
        "description": "删除目录。默认只删空目录；`/S` 递归删目录及其内容（含所有文件），`/Q` 静默（不提示确认）。`rmdir /S /Q dir` 强制删除整个目录树。",
        "tags": ["删除", "目录"], "aliases": ["rd"], "level": "入门", "popularity": 70
    },
    {
        "name": "mkdir", "category": "文件操作", "subcategory": "创建目录",
        "syntax": "mkdir [drive:]path",
        "example": ["mkdir new_dir", "mkdir C:\\a\\b\\c", "mkdir dir1 dir2 dir3"],
        "description": "创建目录。注意 Windows 的 `mkdir` 默认不递归（父目录必须存在）；要用递归创建多级，需 `mkdir C:\\a\\b\\c`（PowerShell 中 `mkdir` 支持 `-p`）。",
        "tags": ["创建", "目录"], "aliases": ["md"], "level": "入门", "popularity": 80
    },
    {
        "name": "type", "category": "文件操作", "subcategory": "查看文本",
        "syntax": "type [drive:][path]filename",
        "example": ["type file.txt", "type readme.md", "type *.txt"],
        "description": "显示文本文件内容到控制台。相当于 Linux 的 `cat`（但不能分页）。大文件请用 `more < file` 或 `type file | more`。",
        "tags": ["查看", "显示"], "aliases": ["cat"], "level": "入门", "popularity": 65
    },
    {
        "name": "more", "category": "文件操作", "subcategory": "分页显示",
        "syntax": "more [/options] [file]",
        "example": ["more file.txt", "type file.txt | more", "more /E +10 file.txt"],
        "description": "分页显示文件。空格翻页，回车下一行，`q` 退出。Linux 的 `less` 更强大；Windows 8+ 可用 `more /E` 启用扩展功能（支持翻页/搜索）。",
        "tags": ["分页", "查看"], "aliases": [], "level": "入门", "popularity": 45
    },
    {
        "name": "find", "category": "文件操作", "subcategory": "文件搜索",
        "syntax": "find [options] \"search_string\" [path]",
        "example": ["find \"error\" C:\\logs", "find /I \"warn\" *.log", "find /N \"TODO\" *.txt", "find /V \"DEBUG\" app.log"],
        "description": "在文件中搜索字符串。`/I` 忽略大小写，`/N` 显示行号，`/V` 反向（输出不含搜索词的行）。注意此 `find` 不支持正则也不递归，要递归用 `findstr /S`。",
        "tags": ["搜索", "查找"], "aliases": [], "level": "入门", "popularity": 55
    },
    {
        "name": "findstr", "category": "文件操作", "subcategory": "正则搜索",
        "syntax": "findstr [options] \"pattern\" [files]",
        "example": ["findstr \"error\" *.log", "findstr /S /I /N \"TODO\" C:\\src\\*.cpp", "findstr /R \"^[0-9]\" file.txt", "findstr /M \"password\" *.txt"],
        "description": "增强版 find，支持正则。`/S` 递归子目录，`/I` 忽略大小写，`/N` 行号，`/R` 正则模式，`/M` 只输出匹配的文件名。比 `find` 更强大。",
        "tags": ["搜索", "正则", "递归"], "aliases": ["grep"], "level": "进阶", "popularity": 70
    },
    {
        "name": "attrib", "category": "文件操作", "subcategory": "属性",
        "syntax": "attrib [+R|-R] [+A|-A] [+S|-S] [+H|-H] [drive:][path]filename [/S]",
        "example": ["attrib file.txt", "attrib +R file.txt", "attrib -H *.tmp", "attrib /S +H secret\\"],
        "description": "显示/修改文件属性。`+R` 只读，`+H` 隐藏，`+S` 系统，`+A` 存档。`/S` 递归处理。`attrib +R file.txt` 设只读，`attrib -H *.tmp` 取消隐藏。",
        "tags": ["属性", "只读", "隐藏"], "aliases": [], "level": "进阶", "popularity": 35
    },
    {
        "name": "compact", "category": "文件操作", "subcategory": "压缩",
        "syntax": "compact [options] [file]",
        "example": ["compact", "compact /C C:\\data", "compact /U /S C:\\data", "compact /Q C:\\Users"],
        "description": "显示/修改 NTFS 压缩状态。`/C` 压缩，`/U` 解压，`/S` 递归。NTFS 文件系统级压缩，对用户透明；不适用于跨盘移动。",
        "tags": ["压缩", "NTFS"], "aliases": [], "level": "进阶", "popularity": 25
    },

    # 系统信息 (12)
    {
        "name": "ipconfig", "category": "系统信息", "subcategory": "网络配置",
        "syntax": "ipconfig [options]",
        "example": ["ipconfig", "ipconfig /all", "ipconfig /release", "ipconfig /renew", "ipconfig /flushdns"],
        "description": "显示网络配置。`/all` 详细信息（MAC/DNS/网关），`/release` 释放 IP，`/renew` 重新获取，`/flushdns` 清 DNS 缓存（解决网站访问问题常用）。",
        "tags": ["网络", "IP", "DNS"], "aliases": ["ifconfig"], "level": "入门", "popularity": 95
    },
    {
        "name": "systeminfo", "category": "系统信息", "subcategory": "系统详情",
        "syntax": "systeminfo [options]",
        "example": ["systeminfo", "systeminfo | findstr /C:\"OS\"", "systeminfo /S remote_pc /U user"],
        "description": "显示详细系统信息（OS 版本/内存/CPU/补丁）。`/S computer` 查远程主机，`/U user` 指定用户。远程诊断必备。",
        "tags": ["系统", "信息", "诊断"], "aliases": [], "level": "进阶", "popularity": 75
    },
    {
        "name": "hostname", "category": "系统信息", "subcategory": "主机名",
        "syntax": "hostname",
        "example": ["hostname", "hostname /?"],
        "description": "显示计算机名。PowerShell 中可用 `$env:COMPUTERNAME` 或 `[System.Net.Dns]::GetHostName()`。",
        "tags": ["主机", "名称"], "aliases": [], "level": "入门", "popularity": 50
    },
    {
        "name": "whoami", "category": "系统信息", "subcategory": "当前用户",
        "syntax": "whoami [options]",
        "example": ["whoami", "whoami /all", "whoami /groups", "whoami /priv"],
        "description": "显示当前用户名及权限信息。`/all` 包括 SID/组/权限，`/groups` 用户所属组，`/priv` 用户权限。诊断权限问题常用。",
        "tags": ["用户", "权限"], "aliases": [], "level": "入门", "popularity": 80
    },
    {
        "name": "set", "category": "系统信息", "subcategory": "环境变量",
        "syntax": "set [variable=[string]]",
        "example": ["set", "set PATH", "set MY_VAR=value", "echo %PATH%"],
        "description": "显示/设置环境变量（cmd 中）。`set` 列所有，`set PATH` 查 PATH，`set X=value` 临时设变量。引用用 `%X%`。PowerShell 中用 `$env:X`。",
        "tags": ["环境变量"], "aliases": ["$env"], "level": "入门", "popularity": 70
    },
    {
        "name": "ver", "category": "系统信息", "subcategory": "Windows 版本",
        "syntax": "ver",
        "example": ["ver", "wmic os get Caption,Version"],
        "description": "显示 Windows 版本号（如 `Microsoft Windows [Version 10.0.22631.xxxx]`）。详细版本信息用 `systeminfo` 或 `wmic os get`。",
        "tags": ["版本", "Windows"], "aliases": [], "level": "入门", "popularity": 35
    },
    {
        "name": "tasklist", "category": "系统信息", "subcategory": "进程列表",
        "syntax": "tasklist [options]",
        "example": ["tasklist", "tasklist /FI \"IMAGENAME eq chrome.exe\"", "tasklist /S remote_pc", "tasklist /V"],
        "description": "列出运行中的进程（类似 Linux 的 `ps`）。`/FI` 按条件过滤（用 WMI 查询语法），`/S` 查远程主机，`/V` 详细信息。",
        "tags": ["进程", "列表"], "aliases": ["ps"], "level": "入门", "popularity": 88
    },
    {
        "name": "taskkill", "category": "系统信息", "subcategory": "结束进程",
        "syntax": "taskkill [options]",
        "example": ["taskkill /IM notepad.exe", "taskkill /PID 1234 /F", "taskkill /IM chrome.exe /F /T"],
        "description": "结束进程（类似 Linux 的 `kill`）。`/IM name` 按进程名，`/PID N` 按 PID，`/F` 强制，`/T` 连同子进程。`taskkill /IM chrome.exe /F` 强制关闭所有 Chrome。",
        "tags": ["结束", "进程"], "aliases": ["kill"], "level": "入门", "popularity": 85
    },
    {
        "name": "sc", "category": "系统信息", "subcategory": "服务管理",
        "syntax": "sc [command] [service_name] [options]",
        "example": ["sc query", "sc query Spooler", "sc start Spooler", "sc stop Spooler", "sc config Spooler start=auto"],
        "description": "与服务控制管理器交互。`query` 查服务状态，`start`/`stop` 启停，`config` 改启动类型。`sc query` 列所有服务。PowerShell 中推荐用 `Get-Service`/`Set-Service`。",
        "tags": ["服务", "Windows 服务"], "aliases": ["Get-Service"], "level": "进阶", "popularity": 65
    },
    {
        "name": "wmic", "category": "系统信息", "subcategory": "WMI 查询",
        "syntax": "wmic [object] [command]",
        "example": ["wmic os get Caption,Version", "wmic cpu get name", "wmic process where name='chrome.exe' get processid", "wmic logicaldisk get caption,size,freespace"],
        "description": "Windows Management Instrumentation 命令行。功能强大：可查 OS/CPU/磁盘/进程/网络等所有信息。`wmic process where name='x.exe' get processid` 查进程 PID。注意 wmic 在 Windows 11 24H2 已弃用。",
        "tags": ["WMI", "诊断"], "aliases": [], "level": "进阶", "popularity": 50
    },
    {
        "name": "gpupdate", "category": "系统信息", "subcategory": "组策略",
        "syntax": "gpupdate [options]",
        "example": ["gpupdate", "gpupdate /force", "gpupdate /target:computer /force"],
        "description": "刷新组策略。`/force` 强制重新应用所有策略（不只是变更的）。域环境下策略修改后等几分钟或手动 `gpupdate /force` 立即生效。",
        "tags": ["组策略", "域"], "aliases": [], "level": "进阶", "popularity": 55
    },
    {
        "name": "gpresult", "category": "系统信息", "subcategory": "组策略结果",
        "syntax": "gpresult [options]",
        "example": ["gpresult /r", "gpresult /h report.html", "gpresult /r /scope:user"],
        "description": "显示应用的组策略结果。`/r` 摘要，`/h file.html` 输出 HTML 报告（打开浏览器查看最详细），`/scope:user|computer` 范围。诊断策略问题必备。",
        "tags": ["组策略", "报告"], "aliases": [], "level": "进阶", "popularity": 50
    },

    # 网络 (12)
    {
        "name": "ping", "category": "网络", "subcategory": "连通性",
        "syntax": "ping [options] target",
        "example": ["ping google.com", "ping -n 4 8.8.8.8", "ping -t host", "ping -l 1000 host"],
        "description": "测试网络连通性。`-n N` 发送 N 次（默认 4），`-t` 持续 ping（Ctrl+C 停止），`-l N` 包大小。`ping -n 4 8.8.8.8` 测试 4 次。返回 `time=` 是延迟。",
        "tags": ["网络", "测试"], "aliases": [], "level": "入门", "popularity": 90
    },
    {
        "name": "tracert", "category": "网络", "subcategory": "路由追踪",
        "syntax": "tracert [options] target",
        "example": ["tracert google.com", "tracert -d 8.8.8.8", "tracert -h 15 host"],
        "description": "追踪到目标的路由路径（类似 Linux 的 `traceroute`）。`-d` 不解析主机名（更快），`-h N` 最大跳数。每一跳显示延迟，定位网络瓶颈点。",
        "tags": ["路由", "追踪"], "aliases": ["traceroute"], "level": "进阶", "popularity": 65
    },
    {
        "name": "pathping", "category": "网络", "subcategory": "路径分析",
        "syntax": "pathping [options] target",
        "example": ["pathping google.com", "pathping -n -q 100 host"],
        "description": "ping + tracert 的组合。先追踪路由，再对每一跳做 ping 统计。比 tracert 信息更详细但耗时更长。",
        "tags": ["路由", "统计"], "aliases": [], "level": "进阶", "popularity": 30
    },
    {
        "name": "netstat", "category": "网络", "subcategory": "连接状态",
        "syntax": "netstat [options]",
        "example": ["netstat -an", "netstat -ano | findstr :80", "netstat -an | findstr ESTABLISHED", "netstat -s"],
        "description": "显示网络连接/端口/统计。`-a` 所有（含监听），`-n` 数字地址，`-o` 显示 PID。`netstat -ano | findstr :80` 查 80 端口的进程。",
        "tags": ["端口", "连接"], "aliases": [], "level": "进阶", "popularity": 75
    },
    {
        "name": "arp", "category": "网络", "subcategory": "ARP 表",
        "syntax": "arp [options]",
        "example": ["arp -a", "arp -a 192.168.1.1", "arp -s 192.168.1.5 00-aa-bb-cc-dd-ee"],
        "description": "显示/修改 ARP 表（IP-MAC 映射）。`-a` 显示所有，`-s` 静态绑定（防 ARP 欺骗），`-d` 删除。诊断局域网问题常用。",
        "tags": ["ARP", "MAC"], "aliases": [], "level": "进阶", "popularity": 40
    },
    {
        "name": "nslookup", "category": "网络", "subcategory": "DNS 查询",
        "syntax": "nslookup [options] [name] [server]",
        "example": ["nslookup google.com", "nslookup google.com 8.8.8.8", "nslookup -type=mx gmail.com"],
        "description": "查询 DNS 记录。`nslookup domain` 用默认 DNS 查，`nslookup domain 8.8.8.8` 指定 DNS 服务器。`-type=mx` 查邮件记录。诊断 DNS 解析问题。",
        "tags": ["DNS", "解析"], "aliases": ["dig"], "level": "进阶", "popularity": 70
    },
    {
        "name": "route", "category": "网络", "subcategory": "路由表",
        "syntax": "route [command]",
        "example": ["route print", "route add 0.0.0.0 mask 0.0.0.0 192.168.1.1", "route delete 10.0.0.0 mask 255.0.0.0"],
        "description": "显示/修改路由表。`print` 显示，`add` 添加路由，`delete` 删除。`route add 0.0.0.0 mask 0.0.0.0 192.168.1.1` 设默认网关（管理员权限）。",
        "tags": ["路由", "网关"], "aliases": [], "level": "进阶", "popularity": 45
    },
    {
        "name": "netsh", "category": "网络", "subcategory": "网络配置",
        "syntax": "netsh [context] [command]",
        "example": ["netsh wlan show profiles", "netsh interface ip show config", "netsh advfirewall set allprofiles state off", "netsh wlan export profile folder=. key=clear"],
        "description": "网络 shell，Windows 网络配置瑞士军刀。`wlan show profiles` 列 WiFi 密码，`interface ip show config` 看 IP 配置，`advfirewall` 防火墙管理。功能远超 ipconfig。",
        "tags": ["网络", "配置", "WiFi"], "aliases": [], "level": "进阶", "popularity": 70
    },
    {
        "name": "ftp", "category": "网络", "subcategory": "FTP",
        "syntax": "ftp [options] [host]",
        "example": ["ftp ftp.example.com", "ftp> get file.txt", "ftp> put local.txt", "ftp> bye"],
        "example_detail": "交互式 FTP 客户端。`open host` 连接，`get` 下载，`put` 上传，`bye` 退出。明文协议，生产环境建议用 SFTP（OpenSSH）。",
        "description": "交互式 FTP 客户端。`get` 下载，`put` 上传，`binary` 二进制模式。`bye` 退出。Windows 自带；明文协议，生产环境推荐 SFTP（PowerShell `sftp` 或 WinSCP）。",
        "tags": ["FTP", "上传", "下载"], "aliases": ["sftp"], "level": "进阶", "popularity": 35
    },
    {
        "name": "telnet", "category": "网络", "subcategory": "远程登录",
        "syntax": "telnet [host [port]]",
        "example": ["telnet host.com", "telnet 192.168.1.1 23", "telnet mail.server 25"],
        "description": "远程登录（明文，不安全）和测试端口连通性。`telnet host port` 可测某端口是否开放（如 `telnet smtp.qq.com 25`）。生产环境推荐 SSH（Windows 10+ 自带 OpenSSH）。",
        "tags": ["远程", "端口测试"], "aliases": ["ssh"], "level": "进阶", "popularity": 30
    },
    {
        "name": "curl", "category": "网络", "subcategory": "HTTP 工具",
        "syntax": "curl [options] URL",
        "example": ["curl https://api.example.com", "curl -O url", "curl -L -o file url", "curl -X POST -d 'data' url"],
        "description": "Windows 10 1803+ 自带，功能同 Linux 版：HTTP 请求/下载/调试 API。`curl -O url` 下载，`-L` 跟随重定向，`-X POST -d 'data'` 发 POST。调试 Web 服务必备。",
        "tags": ["HTTP", "API"], "aliases": [], "level": "进阶", "popularity": 75
    },
    {
        "name": "ssh", "category": "网络", "subcategory": "安全远程",
        "syntax": "ssh [options] user@host",
        "example": ["ssh user@server.com", "ssh -p 2222 user@host", "ssh -i key.pem user@host"],
        "description": "OpenSSH 客户端（Windows 10+ 自带）。`ssh user@host` 登录，`-p N` 端口，`-i key` 用密钥。Linux 服务器管理必备。",
        "tags": ["SSH", "远程"], "aliases": [], "level": "进阶", "popularity": 70
    },

    # 文本查看 (8)
    {
        "name": "sort", "category": "文本查看", "subcategory": "排序",
        "syntax": "sort [options] [file]",
        "example": ["sort file.txt", "sort /R file.txt", "sort /+10 file.txt", "type file | sort"],
        "description": "排序文本行。`/R` 逆序，`/+N` 从第 N 列开始排序（1-based）。常与 `more`/`type` 配合：`type file | sort`。",
        "tags": ["排序"], "aliases": [], "level": "入门", "popularity": 45
    },
    {
        "name": "more", "category": "文本查看", "subcategory": "分页",
        "syntax": "more [/options] [file]",
        "example": ["more file.txt", "type file.txt | more", "more +10 file.txt"],
        "description": "分页显示文件（也归在文件操作）。空格翻页，`q` 退出。`more +N file` 从第 N 行开始显示。Windows 8+ 的 `more /E` 支持扩展功能（翻页/搜索）。",
        "tags": ["分页", "查看"], "aliases": [], "level": "入门", "popularity": 40
    },
    {
        "name": "clip", "category": "文本查看", "subcategory": "剪贴板",
        "syntax": "clip [options]",
        "example": ["clip < file.txt", "echo hello | clip", "ipconfig | clip"],
        "description": "读取管道数据到剪贴板。`ipconfig | clip` 把网络配置复制到剪贴板，`clip < file.txt` 把文件内容复制。粘贴到任何地方（Ctrl+V）。",
        "tags": ["剪贴板", "复制"], "aliases": [], "level": "入门", "popularity": 50
    },
    {
        "name": "echo", "category": "文本查看", "subcategory": "输出",
        "syntax": "echo [string]",
        "example": ["echo Hello", "echo. (空行)", "echo data > file.txt", "echo data >> file.txt"],
        "description": "输出字符串。`echo.` 输出空行。`>` 重定向到文件（覆盖），`>>` 追加。常用于脚本。PowerShell 中 `Write-Output` 或直接 `\"string\"`。",
        "tags": ["输出", "打印"], "aliases": [], "level": "入门", "popularity": 65
    },
    {
        "name": "fc", "category": "文本查看", "subcategory": "文件比较",
        "syntax": "fc [options] file1 file2",
        "example": ["fc file1.txt file2.txt", "fc /B file1.bin file2.bin", "fc /N file1.txt file2.txt"],
        "description": "比较两个文件内容。默认文本模式，`/B` 二进制比较，`/N` 显示行号，`/C` 忽略大小写。返回差异行。",
        "tags": ["比较", "差异"], "aliases": ["diff"], "level": "进阶", "popularity": 35
    },
    {
        "name": "comp", "category": "文本查看", "subcategory": "二进制比较",
        "syntax": "comp [options] file1 file2",
        "example": ["comp file1.bin file2.bin", "comp /A file1 file2"],
        "description": "比较两个二进制文件（旧工具，推荐用 fc /B）。`/A` ASCII 模式，`/N` 显示行号。",
        "tags": ["比较", "二进制"], "aliases": [], "level": "进阶", "popularity": 20
    },
    {
        "name": "tree", "category": "文本查看", "subcategory": "目录树",
        "syntax": "tree [drive:][path] [/options]",
        "example": ["tree", "tree C:\\Users", "tree /F", "tree /A > output.txt"],
        "description": "显示目录树结构。`/F` 含文件，`/A` 用 ASCII 字符（默认 Unicode 框线可能乱码）。`tree /F > out.txt` 输出到文件。",
        "tags": ["树形", "结构"], "aliases": [], "level": "入门", "popularity": 55
    },
    {
        "name": "diskpart", "category": "文本查看", "subcategory": "磁盘分区",
        "syntax": "diskpart",
        "example": ["diskpart", "list disk", "select disk 0", "list partition"],
        "description": "磁盘分区管理（交互式）。命令：`list disk` 列磁盘，`select disk 0` 选磁盘，`list partition` 列分区。功能类似 Linux 的 `fdisk`，但更强大（支持 GPT/动态盘）。危险操作需谨慎。",
        "tags": ["分区", "磁盘"], "aliases": [], "level": "进阶", "popularity": 40
    },

    # 服务管理 (8)
    {
        "name": "net start", "category": "服务管理", "subcategory": "启动服务",
        "syntax": "net start [service]",
        "example": ["net start", "net start Spooler", "net start \"Windows Time\""],
        "description": "启动 Windows 服务。`net start` 列所有运行中的服务，`net start 服务名` 启动指定服务。服务名含空格需引号。",
        "tags": ["服务", "启动"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "net stop", "category": "服务管理", "subcategory": "停止服务",
        "syntax": "net stop [service]",
        "example": ["net stop Spooler", "net stop \"Windows Time\""],
        "description": "停止 Windows 服务。注意：停止关键服务（如 `Winmgmt`）可能导致系统异常。服务名可用 `sc query` 查看。",
        "tags": ["服务", "停止"], "aliases": [], "level": "入门", "popularity": 60
    },
    {
        "name": "net user", "category": "服务管理", "subcategory": "用户管理",
        "syntax": "net user [username [password]] [options]",
        "example": ["net user", "net user newuser", "net user newuser password /add", "net user olduser /delete"],
        "description": "管理本地用户。`net user` 列所有用户，`net user name /add` 添加，`/delete` 删除，`/active:no` 停用。需管理员权限。",
        "tags": ["用户", "账号"], "aliases": [], "level": "进阶", "popularity": 55
    },
    {
        "name": "net localgroup", "category": "服务管理", "subcategory": "组管理",
        "syntax": "net localgroup [group] [options]",
        "example": ["net localgroup", "net localgroup Administrators", "net localgroup Administrators user /add"],
        "description": "管理本地组。`net localgroup Administrators user /add` 把用户加入管理员组（需管理员权限）。",
        "tags": ["用户组", "权限"], "aliases": [], "level": "进阶", "popularity": 50
    },
    {
        "name": "net share", "category": "服务管理", "subcategory": "共享",
        "syntax": "net share [sharename]",
        "example": ["net share", "net share docs=C:\\docs", "net share docs /delete"],
        "description": "管理共享文件夹。`net share docs=C:\\docs /grant:user,full` 创建共享并授权。`net share` 列所有共享，`/delete` 删除。",
        "tags": ["共享", "网络"], "aliases": [], "level": "进阶", "popularity": 50
    },
    {
        "name": "net use", "category": "服务管理", "subcategory": "网络映射",
        "syntax": "net use [drive:] [\\\\server\\share] [options]",
        "example": ["net use", "net use Z: \\\\server\\share", "net use Z: \\\\server\\share /persistent:yes", "net use Z: /delete"],
        "description": "映射/断开网络驱动器。`net use Z: \\\\server\\share` 映射，`/persistent:yes` 重连保持，`net use Z: /delete` 断开。",
        "tags": ["映射", "网络驱动器"], "aliases": [], "level": "进阶", "popularity": 60
    },
    {
        "name": "net session", "category": "服务管理", "subcategory": "会话",
        "syntax": "net session [\\\\computer] [/delete]",
        "example": ["net session", "net session \\\\client_pc /delete"],
        "description": "查/断开会话。`net session` 列所有连接到本机的会话，`/delete` 强制断开。服务器管理常用。",
        "tags": ["会话", "连接"], "aliases": [], "level": "进阶", "popularity": 30
    },
    {
        "name": "net view", "category": "服务管理", "subcategory": "网络浏览",
        "syntax": "net view [\\\\computer] [/options]",
        "example": ["net view", "net view \\\\server", "net view /domain"],
        "description": "浏览网络资源。`net view` 看工作组中的计算机，`net view \\\\server` 看某计算机的共享，`/domain` 看域中计算机。",
        "tags": ["浏览", "共享"], "aliases": [], "level": "进阶", "popularity": 40
    },

    # 实用工具 (5)
    {
        "name": "cls", "category": "实用工具", "subcategory": "清屏",
        "syntax": "cls",
        "example": ["cls", "cls && echo Done"],
        "description": "清空命令行窗口内容（只清显示，不影响历史）。PowerShell 中是 `Clear-Host` 或别名 `clear`。",
        "tags": ["清屏", "界面"], "aliases": ["clear"], "level": "入门", "popularity": 60
    },
    {
        "name": "exit", "category": "实用工具", "subcategory": "退出",
        "syntax": "exit [/B] [exitCode]",
        "example": ["exit", "exit /B 1"],
        "description": "退出 cmd.exe 或批处理脚本。`/B` 退出脚本但不关闭 cmd（带错误码）。批处理中用 `exit /B 1` 表示失败。",
        "tags": ["退出", "脚本"], "aliases": [], "level": "入门", "popularity": 55
    },
    {
        "name": "help", "category": "实用工具", "subcategory": "帮助",
        "syntax": "help [command]",
        "example": ["help", "help dir", "command /?"],
        "description": "显示命令帮助。`help` 列所有命令，`help command` 看某命令详情，`command /?` 也是同样效果。Windows cmd 的内建命令用 help，外部命令用 `/?`。",
        "tags": ["帮助", "文档"], "aliases": ["man"], "level": "入门", "popularity": 50
    },
    {
        "name": "title", "category": "实用工具", "subcategory": "窗口标题",
        "syntax": "title [string]",
        "example": ["title My Project Console", "title Build Server #1"],
        "description": "设置 cmd 窗口标题。脚本中常用：`title Running Tests`。PowerShell 中用 `$host.UI.RawUI.WindowTitle = '...'`。",
        "tags": ["标题", "窗口"], "aliases": [], "level": "入门", "popularity": 30
    },
    {
        "name": "color", "category": "实用工具", "subcategory": "颜色",
        "syntax": "color [attr]",
        "example": ["color 0a", "color 1F", "color"],
        "description": "设置控制台前景/背景色（两位十六进制：第一位背景，第二位前景）。`color 0a` 黑底亮绿（黑客风格），`color` 恢复默认。配色对照：0=黑 1=蓝 2=绿 3=湖蓝 4=红 5=紫 6=黄 7=白 a=亮绿 f=亮白。",
        "tags": ["颜色", "主题"], "aliases": [], "level": "入门", "popularity": 25
    },
]

# ───────────── 写入文件 ─────────────
for cmd in LINUX_COMMANDS:
    cmd["platform"] = "linux"

for cmd in WINDOWS_COMMANDS:
    cmd["platform"] = "windows"

with open(OUT_LINUX, "w", encoding="utf-8") as f:
    json.dump(LINUX_COMMANDS, f, ensure_ascii=False, indent=2)

with open(OUT_WINDOWS, "w", encoding="utf-8") as f:
    json.dump(WINDOWS_COMMANDS, f, ensure_ascii=False, indent=2)

# 统计
linux_cats = defaultdict(int)
for c in LINUX_COMMANDS:
    linux_cats[c["category"]] += 1

windows_cats = defaultdict(int)
for c in WINDOWS_COMMANDS:
    windows_cats[c["category"]] += 1

print(f"[OK] Linux: {len(LINUX_COMMANDS)} 条, {len(linux_cats)} 个类目")
for cat, count in sorted(linux_cats.items(), key=lambda x: -x[1]):
    print(f"  - {cat}: {count}")
print()
print(f"[OK] Windows: {len(WINDOWS_COMMANDS)} 条, {len(windows_cats)} 个类目")
for cat, count in sorted(windows_cats.items(), key=lambda x: -x[1]):
    print(f"  - {cat}: {count}")
print()
print(f"Output: {OUT_LINUX}")
print(f"Output: {OUT_WINDOWS}")