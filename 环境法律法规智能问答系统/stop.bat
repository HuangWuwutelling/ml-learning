@echo off
echo 正在关闭端口 8000 上的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    taskkill /PID %%a /F 2>nul
)
echo 已关闭。按任意键退出。
pause >nul
