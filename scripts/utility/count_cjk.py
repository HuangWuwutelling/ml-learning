"""Count CJK characters in an article body, using the GLOSSARY-publishing-pipeline 口径.

    python scripts/utility/count_cjk.py articles/ai-history/12_KVCache.md

口径（GLOSSARY-publishing-pipeline.md「CJK 字数口径」）：
    取 `## 信息来源` 之前的正文，包含各级标题与表格，
    不含引言里的引用块与图说明。
同一篇文章在不同过滤组合下会给出不同数字，口径变了数字才可比，
所以这个脚本同时把被排除的部分单独打出来，方便核对。
"""
import re
import sys
from pathlib import Path

CJK = re.compile(r'[一-鿿]')


def count(text):
    return len(CJK.findall(text))


def main(paths):
    for arg in paths:
        p = Path(arg)
        text = p.read_text(encoding='utf-8')
        body = text.split('## 信息来源')[0]
        lines = body.split('\n')
        quote = [l for l in lines if l.lstrip().startswith('>')]
        caption = [l for l in lines if l.strip().startswith('<p align')]
        image = [l for l in lines if l.strip().startswith('<div align')]
        keep = [l for l in lines if l not in quote and l not in caption and l not in image]
        keep = [re.sub(r'<[^>]*>', '', l) for l in keep]
        print(f'=== {p} ===')
        print(f'  body CJK (GLOSSARY rule): {count(chr(10).join(keep))}')
        print(f'  excluded: quote {count(chr(10).join(quote))} / caption {count(chr(10).join(caption))}')
        print(f'  total incl. quote+caption: {count(body)}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    main(sys.argv[1:])
