"""
数据收集脚本：保存内置法律法规文本到文件
"""

from src.data.collector import save_raw_laws

if __name__ == "__main__":
    files = save_raw_laws()
    print(f"✅ 已保存 {len(files)} 部环境法律法规文本到 data/raw/ 目录")
    for f in files:
        print(f"   {f}")
