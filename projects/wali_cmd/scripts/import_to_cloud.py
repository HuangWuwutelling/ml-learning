"""把 data/ 下的 markdown 命令导入云数据库。

用法:
    # 用 mock 测试
    python -c "from scripts.import_to_cloud import import_commands; ..."

    # 真机环境（需要在微信开发者工具中跑）
    # 1. 在 miniprogram 任意页面 console 里跑（导入器会作为云函数调用）
    # 或者：写一个云函数 trigger，手动触发
"""
from pathlib import Path

from scripts.config import COLLECTION_LINUX, COLLECTION_WINDOWS, IDatabase
from scripts.markdown_parser import parse_command_file


def import_commands(
    platform: str,
    data_dir: str = "data",
    db: IDatabase | None = None,
) -> int:
    """导入指定平台的所有命令到云数据库。

    Args:
        platform: 'linux' or 'windows'
        data_dir: data 目录根路径
        db: 云数据库实例（测试时传 MockDB）

    Returns:
        成功导入的命令数
    """
    if platform == "linux":
        collection = COLLECTION_LINUX
    elif platform == "windows":
        collection = COLLECTION_WINDOWS
    else:
        raise ValueError(f"Unknown platform: {platform}")

    if db is None:
        raise ValueError("db is required")

    base = Path(data_dir) / platform
    if not base.exists():
        raise FileNotFoundError(f"Data directory not found: {base}")

    count = 0
    for md_file in sorted(base.rglob("*.md")):
        doc = parse_command_file(str(md_file))
        db.upsert(collection, doc)
        count += 1

    return count


if __name__ == "__main__":
    # 真机环境入口（需要在云函数里调用，不能直接本地跑）
    # 实际部署时这段代码会被替换为云函数实现
    print("This script is meant to be called via cloud function.")
    print("See scripts/cloud_import/index.js for the cloud-side implementation.")
