"""GB 36600-2018 限值语料的加载与查询。

语料是 `corpus/gb36600_limits.json`，由 `corpus/build_corpus.py` 从标准原文 PDF 解析而来
（抽取口径见 `corpus/SOURCE.md`）。本模块只负责「找出哪一条」，
判定逻辑在 `rules.py`。

查询串一律先过 `normalize()`：NFKC 归一（全角转半角）+ 去空白 + 小写。
所以 'PCB126' / '（PCB126）' / 'pcb 126' 是同一个键。
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

CORPUS_PATH = Path(__file__).resolve().parent.parent / 'corpus' / 'gb36600_limits.json'


def normalize(text) -> str:
    """归一化查询串：NFKC + 去空白 + 小写。"""
    if text is None:
        return ''
    text = unicodedata.normalize('NFKC', str(text))
    return re.sub(r'\s+', '', text).lower()


class Corpus:
    """GB 36600-2018 的 85 个污染物项目 + 附录 A 背景值。"""

    def __init__(self, doc: dict):
        self.doc = doc
        self.standard_id = doc['standard_id']
        self.standard_name = doc['standard_name']
        self.unit = doc['unit']
        self.notes = doc['notes']
        self.tables = doc.get('tables', {})
        self.background_values = doc['background_values']

        # 条目上挂一份表注原文（①②③④⑤），条文是文档级的，不挂上来调用方取不到
        self.items = []
        self._by_name = {}
        self._by_cas = {}
        for raw in doc['items']:
            item = dict(raw)
            item['notes'] = self.notes
            self.items.append(item)
            self._by_name[normalize(item['name'])] = item
            for cas in item['cas']:
                self._by_cas[cas] = item
        self.item_count = len(self.items)

    # --- 查条目 ---

    def find(self, pollutant):
        """按污染物名或 CAS 号找条目。

        依次尝试：名字完全相等 -> CAS 完全相等 -> 名字包含。
        返回 (条目, 命中方式)；找不到返回 (None, None)。
        """
        if not pollutant:
            return None, None
        key = normalize(pollutant)
        if not key:
            return None, None
        if key in self._by_name:
            return self._by_name[key], 'name'
        if pollutant in self._by_cas:
            return self._by_cas[pollutant], 'cas'
        for cas, item in self._by_cas.items():
            if normalize(cas) == key:
                return item, 'cas'
        hits = [it for it in self.items if key in normalize(it['name'])]
        if hits:
            return hits[0], 'name_contains'
        return None, None

    def search(self, query, limit=10):
        """模糊查候选条目，供 Agent 先确认标准里的项目名。"""
        key = normalize(query)
        if not key:
            return []
        scored = []
        for item in self.items:
            nk = normalize(item['name'])
            if nk == key:
                rank = 0
            elif nk.startswith(key):
                rank = 1
            elif key in nk:
                rank = 2
            elif any(key in normalize(c) for c in item['cas']):
                rank = 3
            elif key in normalize(item['category']):
                rank = 4
            else:
                continue
            scored.append((rank, item['table'], item['no'], item))
        scored.sort(key=lambda x: (x[0], x[1], x[2]))
        return [x[3] for x in scored[:max(1, int(limit))]]

    # --- 查背景值 ---

    def background_for(self, element, soil_type):
        """查附录 A 的土壤环境背景值。

        返回 (数值, 来源说明, 适用土壤类型列表)；查不到返回 (None, 原因, [])。
        附录 A 只给了砷、钒、钴三个元素的背景值，其余元素的标准里没有。
        """
        if not element:
            return None, '未给元素名', []
        vals = self.background_values.get(element)
        if vals is None:
            return None, 'GB 36600-2018 附录 A 未给该元素的背景值（只给了砷、钒、钴）', []
        if not soil_type:
            return None, '未给土壤类型，无法定位附录 A 里的那一档', []
        want = normalize(soil_type)
        matched = None
        for value, soils in vals.items():
            if any(normalize(s) == want for s in soils):
                matched = (value, soils)
                break
        if matched is None:
            return None, '附录 A 里没有土壤类型「%s」这一档' % soil_type, []
        value, soils = matched
        return float(value), 'GB 36600-2018 附录 A', list(soils)


def load_corpus(path=None) -> Corpus:
    """读语料 JSON。"""
    p = Path(path) if path else CORPUS_PATH
    with open(p, encoding='utf-8') as f:
        return Corpus(json.load(f))
