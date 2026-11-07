"""校验 article md 是否符合 CLAUDE.md 写作约束。

Usage:
    python scripts/utility/check_article.py <article.md> [more.md ...]

不带参数时打印用法并列出候选文章，退出码 2（不猜默认文章）。
注：字数不作为自动校验项（用户根据内容判定）。仅校验硬约束：
- 无 `——` 破折号
- 无 AI 腔禁词
- 文中引用的图片文件必须存在（含 markdown image 语法和 HTML <img> 两类）
- 文中指向本地文件的 markdown 链接必须存在（http/https 外链不查）
"""
import re
import sys
from pathlib import Path

# Windows GBK 控制台兼容：强制 UTF-8 输出
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

FORBIDDEN = ['含义：', '模型显示：', '教科书级', '成本量级', '监管层面',
             '如果以', '为参照线', '单看', '数字之外']


def candidate_articles(limit=5):
    """列出 articles/ 下最近修改的几篇文章，供用户挑。"""
    art = REPO_ROOT / 'articles'
    if not art.is_dir():
        return []
    files = [p for p in art.glob('*/*.md') if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def check_one(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    article_dir = path.parent.resolve()
    ok = True

    # 1. 破折号
    em = '——' in text
    print(f'  破折号 {"FOUND" if em else "OK"}')
    ok = ok and not em

    # 2. AI 腔禁词
    hits = [w for w in FORBIDDEN if w in text]
    print(f'  AI 腔禁词 {hits if hits else "OK"}')
    ok = ok and not hits

    # 3. 图片路径必须存在（markdown `![..](path)` 与 HTML `<img src=path>`）
    md_imgs = re.findall(r'!\[.*?\]\((.+?)\)', text)
    html_imgs = re.findall(r'<img[^>]+src=["\'](.+?)["\']', text)
    broken = [i for i in md_imgs + html_imgs if not (article_dir / i).is_file()]
    print(f'  失效图片 {broken if broken else "OK"}')
    ok = ok and not broken

    # 4. 本地 markdown 链接必须存在（外链与锚点不查）
    local_links = []
    for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text):
        target = target.split('#')[0].strip()
        if not target or target.startswith(('http://', 'https://', 'mailto:')):
            continue
        local_links.append(target)
    missing = [t for t in local_links if not (article_dir / t).exists()]
    print(f'  失效本地链接 {missing if missing else "OK"}')
    ok = ok and not missing

    # 5. 字数（仅供参考，不作为通过条件）
    body = re.sub(r'<[^>]+>', '', text)
    body = re.sub(r'#+', '', body)
    body = re.sub(r'!\[.*?\]\(.*?\)', '', body)
    body = re.sub(r'\[.*?\]\(.*?\)', '', body)
    body = re.sub(r'^\s*[-*+]\s', '', body, flags=re.M)
    body = re.sub(r'`([^`]+)`', r'\1', body)
    body = re.sub(r'\*([^*]+)\*', r'\1', body)
    body = re.sub(r'\s+', '', body)
    print(f'  字数（去 markdown + HTML，仅参考）: {len(body)}')

    return ok


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        print('候选文章（最近修改）：')
        for p in candidate_articles():
            print('  ', p.relative_to(REPO_ROOT))
        sys.exit(2)

    all_ok = True
    for arg in args:
        p = Path(arg)
        if not p.is_absolute():
            p = REPO_ROOT / p
        print(f'\n=== {p.relative_to(REPO_ROOT) if p.is_relative_to(REPO_ROOT) else p} ===')
        if not p.is_file():
            print('  文件不存在')
            all_ok = False
            continue
        all_ok = check_one(p) and all_ok

    print('\n结果：', 'OK' if all_ok else 'FAIL')
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
