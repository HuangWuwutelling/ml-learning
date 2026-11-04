"""语料层的测试：条数、四个值、索引、背景值、交叉核验。"""
from server.corpus import load_corpus, normalize

CORPUS = load_corpus()


def test_item_count_is_85():
    """GB 36600-2018：表 1 基本项目 45 项 + 表 2 其他项目 40 项。"""
    assert CORPUS.item_count == 85
    assert len(CORPUS.items) == 85
    assert sum(1 for it in CORPUS.items if it['table'] == 1) == 45
    assert sum(1 for it in CORPUS.items if it['table'] == 2) == 40


def test_every_item_has_four_values():
    for it in CORPUS.items:
        for kind in ('screening', 'control'):
            for land in ('第一类用地', '第二类用地'):
                assert it[kind][land] is not None, '%s 缺 %s %s' % (it['name'], kind, land)
        assert it['name']
        assert it['clause']


def test_find_by_name_and_cas():
    item, how = CORPUS.find('镉')
    assert item['name'] == '镉' and how == 'name'
    item, how = CORPUS.find('7440-43-9')
    assert item['name'] == '镉' and how == 'cas'


def test_find_is_normalization_insensitive():
    """全角括号、大小写、空格差异不应该让查询落空。"""
    for q in ('PCB126', '（PCB126）', 'pcb 126', 'pcb126'):
        item, how = CORPUS.find(q)
        assert item is not None, q
        assert item['name'].endswith('（PCB126）'), (q, item['name'])


def test_find_miss_returns_none():
    item, how = CORPUS.find('正己烷')
    assert item is None and how is None


def test_search_ranks_exact_first():
    hits = CORPUS.search('镉', 10)
    assert hits[0]['name'] == '镉'


def test_search_by_category():
    hits = CORPUS.search('重金属', 50)
    assert len(hits) == 13
    assert all(h['category'] == '重金属和无机物' for h in hits)


def test_background_lookup():
    value, source, soils = CORPUS.background_for('砷', '水稻土')
    assert value == 40.0
    assert '水稻土' in soils
    assert '附录 A' in source


def test_background_not_in_appendix():
    """附录 A 只给砷、钒、钴，别的元素不能编一个背景值出来。"""
    value, reason, _ = CORPUS.background_for('镉', '水稻土')
    assert value is None
    assert '附录 A' in reason


def test_background_unknown_soil_type():
    value, reason, _ = CORPUS.background_for('砷', '火星土')
    assert value is None
    assert reason


def test_cross_check_clean():
    """两种提取模式读出的四个数必须一致，核不上的要留在 failed 里。"""
    assert CORPUS.doc['cross_check']['failed'] == []


def test_fluorene_name_was_corrected():
    """标准 PDF 的字体把「芴」映射成 U+44DB（䓛），按 CAS 校正。"""
    item, _ = CORPUS.find('芴')
    assert item is not None
    assert item['cas'] == ['218-01-9']
    assert item['name_raw'] == '䓛'


def test_normalize_strips_spaces_and_case():
    assert normalize('  PCB 126 ') == 'pcb126'
    assert normalize('（总量）') == '(总量)'
