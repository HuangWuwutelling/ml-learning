"""云开发环境配置。"""
import os
from typing import Protocol


class IDatabase(Protocol):
    """云数据库抽象接口（方便测试用 mock）。"""

    def upsert(self, collection: str, doc: dict) -> None: ...
    def count(self, collection: str) -> int: ...


# 云开发环境 ID（需要在微信开发者工具创建后填入）
CLOUD_ENV_ID = os.environ.get("WALI_CMD_ENV_ID", "wali-cmd-dev")

# collection 名称
COLLECTION_LINUX = "linux_commands"
COLLECTION_WINDOWS = "windows_commands"
