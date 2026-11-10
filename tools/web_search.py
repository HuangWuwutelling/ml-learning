"""网页搜索 / 抓取的薄封装，走 Firecrawl API。

为什么不用 firecrawl MCP 工具：那两个工具的 schema 每轮常驻约 5-6k token
（CLAUDE.md「阶段边界」节），日常用不起。这个脚本零常驻成本。

Key 从 `.mcp.json` 读（该文件被 gitignore），也认环境变量 `FIRECRAWL_API_KEY`。

用法：

    python tools/web_search.py search "honeywell ai engineer guangzhou"
    python tools/web_search.py search "广州 外企 AI 工程师" --lang zh --country CN
    python tools/web_search.py scrape "https://www.liepin.com/job/xxx.shtml" --out jd.md

已知口径：

- Firecrawl 的检索后端对**英文 query 友好、中文 query 差**（中文 query 会返回
  无关的维基/翻译页）。中文场景改用 `scrape` 直接抓已知 URL，或用英文 query 搜。
- 猎聘、前程无忧这类页面 firecrawl 能抓出正文（已实测猎聘 JD 页）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows GBK 控制台会炸中文
except Exception:  # pragma: no cover - 老 Python 或非标准流
    pass

API = "https://api.firecrawl.dev/v1"
REPO_ROOT = Path(__file__).resolve().parent.parent


def get_key() -> str:
    """先环境变量，再 `.mcp.json`。找不到就抛，带清楚的下一步。"""
    key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if key:
        return key
    mcp = REPO_ROOT / ".mcp.json"
    if mcp.exists():
        data = json.loads(mcp.read_text(encoding="utf-8"))
        key = (
            data.get("mcpServers", {})
            .get("firecrawl", {})
            .get("env", {})
            .get("FIRECRAWL_API_KEY", "")
            .strip()
        )
        if key:
            return key
    raise SystemExit(
        "no firecrawl key: set FIRECRAWL_API_KEY, or add it under "
        "mcpServers.firecrawl.env in .mcp.json"
    )


def post(path: str, payload: dict, key: str) -> dict:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"firecrawl HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"firecrawl network error: {exc.reason}") from exc

    if not body.get("success", False):
        raise SystemExit(f"firecrawl returned failure: {json.dumps(body)[:400]}")
    return body.get("data") or {}


def cmd_search(args: argparse.Namespace) -> int:
    key = get_key()
    payload: dict = {"query": args.query, "limit": args.limit}
    if args.lang:
        payload["lang"] = args.lang
    if args.country:
        payload["country"] = args.country
    data = post("/search", payload, key)

    if isinstance(data, list):  # /v1/search 直接回列表
        results = data
    elif isinstance(data, dict):
        results = data.get("web") or data.get("data") or []
    else:
        results = []
    if not results:
        print("(no results)")
        return 0

    for i, item in enumerate(results, 1):
        title = (item.get("title") or "").replace("\n", " ").strip()
        url = item.get("url") or ""
        desc = (item.get("description") or "").replace("\n", " ").strip()
        print(f"{i}. {title}")
        print(f"   {url}")
        if desc:
            print(f"   {desc[:300]}")
    print(f"--- {len(results)} results ---")
    return 0


def cmd_scrape(args: argparse.Namespace) -> int:
    key = get_key()
    payload: dict = {
        "url": args.url,
        "formats": ["markdown"],
        "onlyMainContent": not args.full_page,
    }
    if args.wait:
        payload["waitFor"] = args.wait
    data = post("/scrape", payload, key)
    text = data.get("markdown") or data.get("content") or ""

    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {len(text)} chars -> {args.out}")
        return 0

    limit = args.max_chars if args.max_chars > 0 else len(text)
    print(text[:limit])
    if len(text) > limit:
        print(f"\n--- truncated at {limit} of {len(text)} chars ---")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Firecrawl search/scrape wrapper")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_search = sub.add_parser("search", help="search the web")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--lang", default=None, help="e.g. zh / en")
    p_search.add_argument("--country", default=None, help="e.g. CN / US")
    p_search.set_defaults(func=cmd_search)

    p_scrape = sub.add_parser("scrape", help="scrape one url to markdown")
    p_scrape.add_argument("url")
    p_scrape.add_argument("--out", default=None, help="write markdown to this file")
    p_scrape.add_argument("--max-chars", type=int, default=6000)
    p_scrape.add_argument("--full-page", action="store_true")
    p_scrape.add_argument("--wait", default=None, help="waitFor selector, e.g. '#app'")
    p_scrape.set_defaults(func=cmd_scrape)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
