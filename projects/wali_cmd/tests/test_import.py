import os
import tempfile
from scripts.import_to_cloud import import_commands
from scripts.markdown_parser import parse_command_file


class MockDB:
    def __init__(self):
        self.collections = {}

    def upsert(self, collection, doc):
        if collection not in self.collections:
            self.collections[collection] = []
        # 去重（按 name）
        self.collections[collection] = [
            d for d in self.collections[collection]
            if d.get("name") != doc.get("name")
        ]
        self.collections[collection].append(doc)

    def count(self, collection):
        return len(self.collections.get(collection, []))


def test_import_linux_commands():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 准备 2 个 markdown 文件
        os.makedirs(os.path.join(tmpdir, "linux", "01_文件操作"))
        for name in ["find", "ls"]:
            with open(os.path.join(tmpdir, "linux", "01_文件操作", f"{name}.md"), "w", encoding="utf-8") as f:
                f.write(f"""---
name: {name}
category: 测试
syntax: "{name} [options]"
tags: ["test"]
level: 入门
popularity: 50
---

测试描述。

## 示例

```bash
{name} --help
```
""")
        db = MockDB()
        count = import_commands(platform="linux", data_dir=tmpdir, db=db)
        assert count == 2
        assert db.count("linux_commands") == 2


def test_import_upsert_idempotent():
    """同一命令多次导入不会重复。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "linux", "01_文件操作"))
        with open(os.path.join(tmpdir, "linux", "01_文件操作", "find.md"), "w", encoding="utf-8") as f:
            f.write("""---
name: find
category: 测试
syntax: "find [path]"
---

测试描述。
""")
        db = MockDB()
        # 第一次导入
        import_commands(platform="linux", data_dir=tmpdir, db=db)
        # 第二次导入（修改了文件）
        with open(os.path.join(tmpdir, "linux", "01_文件操作", "find.md"), "w", encoding="utf-8") as f:
            f.write("""---
name: find
category: 测试（更新）
syntax: "find [path] [new]"
---

更新描述。
""")
        import_commands(platform="linux", data_dir=tmpdir, db=db)
        # 不应该重复
        assert db.count("linux_commands") == 1
        # 应该是新版本
        assert db.collections["linux_commands"][0]["category"] == "测试（更新）"
