"""从 GB 36600-2018 的 text layer PDF 解析出结构化限值表。

用法（PDF 不进仓库，路径由调用方给）：
    python build_corpus.py <textlayer.pdf> [-o gb36600_limits.json]

为什么要两种提取模式：
    - extract_text()                     给行的先后顺序，用来切「哪几个数属于哪一项」
    - extract_text(mode='layout')        保留横向位置，用来核「这个数落在哪一列」
    两种模式读出的四个数不一致就记进 unverified，不让错位的数字悄悄进 JSON。

抽取口径与已知修正见同目录 SOURCE.md。
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pypdf

# --- 正则 ---

# 数值：3.0 / 20 / 0.02 / 4×10-5 / 1×10-4
NUM = r'\d+(?:\.\d+)?(?:×10-?\d+)?'
VALUE_RE = re.compile(r'^' + NUM + r'$')
# CAS 号：7440-38-2 / 107-06-2 / 57465-28-8 / 32774-16-6；'-' 表示没有 CAS
CAS_RE = re.compile(r'^(?:\d{2,7}-\d{2}-\d|,)+$')
MARKERS = '①②③④⑤⑥⑦⑧⑨'
MARKER_RE = re.compile(r'^[①-⑨]$')

# 表 1 / 表 2 的分类小标题（不是条目）
CATEGORIES = [
    '重金属和无机物',
    '挥发性有机物',
    '半挥发性有机物',
    '有机农药类',
    '多氯联苯、多溴联苯和二噁英类',
    '石油烃类',
]


def parse_number(tok):
    """'3.0' -> 3.0；'4×10-5' -> 4e-5。"""
    if '×10' in tok:
        mantissa, exponent = tok.split('×10')
        return float(mantissa) * (10 ** int(exponent))
    return float(tok)


def find_region(lines, start_pat, end_pat):
    """切出 [start, end) 的行区间。end_pat 是正则。"""
    start = end = None
    for i, line in enumerate(lines):
        if start is None and re.search(start_pat, line):
            start = i
        elif start is not None and re.search(end_pat, line):
            end = i
            break
    if start is None or end is None:
        raise ValueError('region not found: %s' % start_pat)
    return lines[start:end]


# 表头 / 页脚 / 单位行：不是条目数据，解析前先清掉
_NOISE_EXACT = {'第一类', '第二类', '用地'}
_NOISE_SUBSTR = ('污染物项目', 'CAS编号', '序号', '用地', '筛选值', '管制值')


def clean_region(lines):
    """去掉表头、页脚页码、单位行。

    页脚长这样：「GB 36600—2018」+ 一个纯数字页码，两行都要去掉，
    否则页码会被当成条目的数值。
    """
    out = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if re.match(r'^GB 36600[—\-]\d{4}$', s):
            i += 1
            if i < len(lines) and re.fullmatch(r'\d+', lines[i].strip()):
                i += 1
            continue
        if (not s or s in _NOISE_EXACT or s.startswith('单位')
                or any(k in s for k in _NOISE_SUBSTR)):
            i += 1
            continue
        out.append(lines[i])
        i += 1
    return out


def clean_pages_only(lines):
    """只去掉页脚页码，留住表头（附录 A 的表名行要留着当结构标记）。"""
    out = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if re.match(r'^GB 36600[—\-]\d{4}$', s):
            i += 1
            if i < len(lines) and re.fullmatch(r'\d+', lines[i].strip()):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return out


def parse_table(lines, table_no):
    """把一张表的行切成条目。

    行的形状（PDF 里换行位置不固定，序号 / 名称 / CAS / 四个数可能各占一行）：
        [分类小标题] 序号 名称... CAS...  值1 [注] 值2 [注] 值3 值4
    做法：按 token 流走，凑够 4 个数算一行；行首的纯整数是序号，
    行首的非数字行是分类小标题。
    """
    tokens = []
    for raw in clean_region(lines):
        tokens.extend(raw.strip().split())

    rows = []
    buf = []
    category = None
    nval = 0
    for tok in tokens:
        if not buf:
            if not re.fullmatch(r'\d+', tok):
                # 行首不是序号 -> 分类小标题
                if tok in CATEGORIES:
                    category = tok
                continue
            buf.append(tok)
            continue
        buf.append(tok)
        if VALUE_RE.match(tok):
            nval += 1
        if nval == 4:
            rows.append((category, buf))
            buf = []
            nval = 0
    if buf:
        raise ValueError('table %s: trailing tokens %r' % (table_no, buf))
    return rows


# PDF 字体把「芴」的字形映射到 U+44DB（䓛）。CAS 218-01-9 是芴(fluorene)的唯一标识，
# 表 1 第 42 项按 CAS 校正。依据与复核方式见同目录 SOURCE.md。
NAME_FIXES = {
    ('䓛', '218-01-9'): '芴',
}

# 括号里的空格是 PDF 换行留下的（'（PCB 126）'），查名字时要能两种写法都命中
_BRACKET_SPACE = re.compile(r'([\[\(（])\s+|\s+([\]\)）])')


def normalize_name(name):
    name = name.strip()
    return _BRACKET_SPACE.sub(r'\1\2', name)


def row_to_item(category, tokens, table_no):
    """一行 token -> 一个条目。"""
    no = int(tokens[0])
    rest = tokens[1:]
    # 找第一个数值 token 的位置，前面是「名称 + CAS + 名称上的注」
    first_val = None
    for i, tok in enumerate(rest):
        if VALUE_RE.match(tok):
            first_val = i
            break
    if first_val is None:
        raise ValueError('item %s: no values' % no)
    prefix = rest[:first_val]
    tail = rest[first_val:]

    cas = []
    name_parts = []
    item_notes = []
    for tok in prefix:
        if CAS_RE.match(tok):
            cas.extend(t for t in tok.split(',') if t)
        elif MARKER_RE.match(tok):
            item_notes.append(tok)
        elif tok == '-':
            # CAS 列的占位符：该项没有 CAS 编号（多氯联苯总量、二噁英类等）
            continue
        else:
            name_parts.append(tok)
    name = normalize_name(''.join(name_parts))
    name_raw = name
    fixed = NAME_FIXES.get((name, ','.join(cas)))
    if fixed:
        name = fixed

    values = []
    raws = []
    value_notes = {}
    i = 0
    while len(values) < 4:
        tok = tail[i]
        if VALUE_RE.match(tok):
            note = None
            if i + 1 < len(tail) and MARKER_RE.match(tail[i + 1]):
                note = tail[i + 1]
                i += 1
            values.append(parse_number(tok))
            raws.append(tok)
            if note:
                value_notes[len(values) - 1] = note
        i += 1
    if i != len(tail):
        raise ValueError('item %s: unexpected tail %r' % (no, tail[i:]))

    labels = ['筛选值 第一类用地', '筛选值 第二类用地',
              '管制值 第一类用地', '管制值 第二类用地']
    item = {
        'table': table_no,
        'no': no,
        'name': name,
        'cas': cas,
        'category': category,
        'screening': {'第一类用地': values[0], '第二类用地': values[1]},
        'control': {'第一类用地': values[2], '第二类用地': values[3]},
        # 原文字符串（3.0 / 1×10-5 这种写法），核对原文时按它比
        'raw': {
            'screening': {'第一类用地': raws[0], '第二类用地': raws[1]},
            'control': {'第一类用地': raws[2], '第二类用地': raws[3]},
        },
        'item_notes': item_notes,
        'value_notes': {labels[k]: v for k, v in value_notes.items()},
        'clause': 'GB 36600-2018 表 %d 第 %d 项' % (table_no, no),
    }
    if name != name_raw:
        # 记下原始字形，改名有据可查
        item['name_raw'] = name_raw
    return item


def parse_background(lines):
    """附录 A：砷 / 钴 / 钒 的土壤环境背景值。

    形状：一堆土壤类型（可能跨行，顿号分隔）+ 一个数值。
    土壤名本身可能跨行断在「灰漠土、灰」这种地方，所以先把行拼成整段文本，
    再按顿号切，不按行切。
    返回 {元素: {背景值: [土壤类型, ...]}}。
    """
    out = {}
    element = None
    pending = ''
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = re.match(r'^表 A\.(\d)\s*各主要类型土壤中(.+?)的背景值$', line)
        if m:
            element = m.group(2)
            out[element] = {}
            pending = ''
            continue
        if element is None or '背景值' in line or '土壤类型' in line:
            continue
        m2 = re.match(r'^(.*?)(\d+)\s*$', line)
        if m2:
            pending += m2.group(1)
            value = int(m2.group(2))
        elif re.fullmatch(r'\d+', line):
            value = int(line)
        else:
            pending += line
            continue
        soils = [s.strip() for s in re.split(r'[、,]', pending) if s.strip()]
        out[element].setdefault(value, [])
        out[element][value].extend(soils)
        pending = ''
    return out


def cross_check(items, layout_text):
    """用 layout 模式再读一遍，核每个条目的四个数在原文里是不是这个顺序。

    核不上不等于错（名称跨行的条目四个数可能不在同一行），
    但核不上的条目必须在 unverified 里列出来，由人看。
    """
    unverified = []
    for it in items:
        raws = [it['raw']['screening']['第一类用地'], it['raw']['screening']['第二类用地'],
                it['raw']['control']['第一类用地'], it['raw']['control']['第二类用地']]
        # 数值后面可能紧跟一个上标注（20①）
        pat = r'\s+'.join(re.escape(r) + r'\s*[①-⑨]?' for r in raws)
        if not re.search(pat, layout_text):
            unverified.append({'table': it['table'], 'no': it['no'], 'name': it['name']})
    return unverified


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf', help='GB 36600-2018 的 text layer PDF 路径')
    ap.add_argument('-o', '--out', default=str(Path(__file__).parent / 'gb36600_limits.json'))
    args = ap.parse_args()

    reader = pypdf.PdfReader(args.pdf)
    pages = [p.extract_text() or '' for p in reader.pages]
    layout_pages = [p.extract_text(extraction_mode='layout') or '' for p in reader.pages]
    raw_lines = []
    for page in pages:
        raw_lines.extend(page.split('\n'))
    layout_text = '\n'.join(layout_pages)

    t1 = find_region(raw_lines, r'^表 1 建设用地', r'^注：')
    t2 = find_region(raw_lines, r'^表 2 建设用地', r'^注：')

    items = []
    for table_no, region in ((1, t1), (2, t2)):
        for category, tokens in parse_table(region, table_no):
            items.append(row_to_item(category, tokens, table_no))

    # 附录 A：按页找（A.1 / A.2 / A.3 三张表）
    try:
        a_start = next(i for i, l in enumerate(raw_lines) if l.strip() == '附录 A')
    except StopIteration:
        raise ValueError('appendix A not found')
    background = parse_background(clean_pages_only(raw_lines[a_start:]))

    unverified = cross_check(items, layout_text)

    doc = {
        'standard_id': 'GB 36600-2018',
        'standard_name': '土壤环境质量 建设用地土壤污染风险管控标准',
        'issued': '2018-06-22',
        'approved': '2018-05-17',
        'effective': '2018-08-01',
        'unit': 'mg/kg',
        'land_types': ['第一类用地', '第二类用地'],
        'tables': {
            '1': {
                'title': '建设用地土壤污染风险筛选值和管制值（基本项目）',
                'role': '初步调查阶段必测项目（5.2.1）',
            },
            '2': {
                'title': '建设用地土壤污染风险筛选值和管制值（其他项目）',
                'role': '初步调查阶段选测项目（5.2.2）',
            },
        },
        'notes': {
            '①': '具体地块土壤中污染物检测含量超过筛选值，但等于或者低于土壤环境背景值（见 3.6）水平的，不纳入污染地块管理。土壤环境背景值可参见附录 A。',
            '②': '氯丹为α-氯丹、γ-氯丹两种物质含量总和。',
            '③': '滴滴涕为 o,p\'-滴滴涕、p,p\'-滴滴涕两种物质含量总和。',
            '④': '硫丹为α-硫丹、β-硫丹两种物质含量总和。',
            '⑤': '多氯联苯（总量）为 PCB 77、PCB 81、PCB105、PCB114、PCB118、PCB123、PCB 126、PCB156、PCB157、PCB167、PCB169、PCB189十二种物质含量总和。',
        },
        'background_values': {k: {str(v): soils for v, soils in vals.items()}
                              for k, vals in background.items()},
        'cross_check': {
            'method': 'extract_text() 取行序、extract_text(extraction_mode="layout") 取列位，'
                      '两种模式读出的四个数必须一致；核不上的条目列在 failed 里由人看',
            'failed': unverified,
        },
        'item_count': len(items),
        'items': items,
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')
    print('items', len(items), 't1', sum(1 for i in items if i['table'] == 1),
          't2', sum(1 for i in items if i['table'] == 2))
    print('background elements', list(background))
    print('unverified (cross-check failed)', len(unverified))
    for u in unverified:
        print('  ', u)
    print('written', args.out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
