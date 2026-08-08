"""把 markdown 源数据导出为 JSON（供 cloudImport 云函数嵌入用）。"""
import json
import sys
from pathlib import Path

# 让脚本既能从项目根（python -m scripts.export_to_json），
# 也能从项目根直接跑（python scripts/export_to_json.py）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.markdown_parser import parse_command_file


def export_platform(platform: str, data_dir: str = "data") -> list:
    base = Path(data_dir) / platform
    commands = []
    for md_file in sorted(base.rglob("*.md")):
        commands.append(parse_command_file(str(md_file)))
    return commands


if __name__ == "__main__":
    out_dir = Path("cloudfunctions/cloudImport/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    for platform, fname in [("linux", "linux_commands.json"),
                            ("windows", "windows_commands.json")]:
        data = export_platform(platform)
        with open(out_dir / fname, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Exported {len(data)} {platform} commands to {out_dir / fname}")