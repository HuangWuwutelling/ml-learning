import pytest
from eval.scoring import tool_set_scores, no_tool_score


# --- 工具集合打分口径 ---

def test_exact_set_match_scores_one():
    s = tool_set_scores(['assess_severity', 'draft_capa'], ['draft_capa', 'assess_severity'])
    assert s['precision'] == 1.0
    assert s['recall'] == 1.0
    assert s['f1'] == 1.0
    assert s['exact'] == 1.0


def test_call_order_does_not_matter():
    a = tool_set_scores(['a', 'b'], ['b', 'a'])
    b = tool_set_scores(['b', 'a'], ['a', 'b'])
    assert a == b


def test_repeated_tool_counts_once():
    s = tool_set_scores(['draft_capa', 'draft_capa'], ['draft_capa'])
    assert s['exact'] == 1.0


def test_missing_tool_lowers_recall_only():
    s = tool_set_scores(['assess_severity'], ['assess_severity', 'draft_capa'])
    assert s['precision'] == 1.0
    assert s['recall'] == 0.5
    assert s['f1'] == pytest.approx(2 / 3)
    assert s['exact'] == 0.0


def test_extra_tool_lowers_precision_only():
    s = tool_set_scores(['assess_severity', 'query_regulation'], ['assess_severity'])
    assert s['precision'] == 0.5
    assert s['recall'] == 1.0
    assert s['exact'] == 0.0


def test_calling_nothing_when_tools_expected_scores_zero():
    s = tool_set_scores([], ['assess_severity'])
    assert s['precision'] == 0.0
    assert s['recall'] == 0.0
    assert s['f1'] == 0.0
    assert s['exact'] == 0.0


def test_empty_expectation_means_must_not_call():
    assert tool_set_scores([], [])['exact'] == 1.0
    assert tool_set_scores([], [])['f1'] == 1.0
    assert tool_set_scores(['draft_capa'], [])['exact'] == 0.0


# --- 不该调工具的打分口径 ---

def test_no_tool_score_needs_no_call_and_a_reply():
    assert no_tool_score([], '你好')['ok'] == 1.0
    assert no_tool_score([], '你好')['no_tool'] == 1.0
    assert no_tool_score([], '你好')['replied'] == 1.0


def test_no_tool_score_fails_when_a_tool_was_called():
    s = no_tool_score(['draft_capa'], '你好')
    assert s['ok'] == 0.0
    assert s['no_tool'] == 0.0
    assert s['replied'] == 1.0


def test_no_tool_score_fails_on_empty_reply():
    assert no_tool_score([], '')['ok'] == 0.0
    assert no_tool_score([], '   ')['ok'] == 0.0


# --- run_eval 的退出码三态 ---

def _fake_metric(name, accuracy, target=0.8):
    def fn():
        return {'name': name, 'total': 1, 'correct': 1, 'accuracy': accuracy,
                'target': target, 'summary': 'fake'}
    return fn


def _boom_metric(name):
    def fn():
        raise RuntimeError('no key')
    return fn


def _recorder(ran, name, accuracy=1.0):
    def fn():
        ran.append(name)
        return {'name': name, 'total': 1, 'correct': 1, 'accuracy': accuracy,
                'target': 0.8, 'summary': 'fake'}
    return fn


def test_exit_code_0_when_all_metrics_pass(monkeypatch, tmp_path):
    import eval.run_eval as run_eval
    monkeypatch.setattr(run_eval, 'RESULTS_DIR', tmp_path)
    monkeypatch.setattr(run_eval, 'METRICS', [(_fake_metric('m1', 1.0), 'm1')])
    # argv 传 []，不让 argparse 去读 pytest 自己的命令行参数
    assert run_eval.main([]) == 0


def test_exit_code_1_when_a_metric_fails(monkeypatch, tmp_path):
    import eval.run_eval as run_eval
    monkeypatch.setattr(run_eval, 'RESULTS_DIR', tmp_path)
    monkeypatch.setattr(run_eval, 'METRICS', [(_fake_metric('m1', 0.2), 'm1')])
    assert run_eval.main([]) == 1


def test_exit_code_2_when_a_metric_is_skipped(monkeypatch, tmp_path):
    """跳过的指标没测出来，不能当通过，也不能当失败。"""
    import eval.run_eval as run_eval
    monkeypatch.setattr(run_eval, 'RESULTS_DIR', tmp_path)
    monkeypatch.setattr(run_eval, 'METRICS', [
        (_fake_metric('m1', 1.0), 'm1'),
        (_boom_metric('m2'), 'm2'),
    ])
    assert run_eval.main([]) == 2


def test_only_selects_the_named_metrics(monkeypatch, tmp_path):
    """--only 只跑点名的指标，其余一个都不碰。"""
    import eval.run_eval as run_eval
    ran = []
    monkeypatch.setattr(run_eval, 'RESULTS_DIR', tmp_path)
    monkeypatch.setattr(run_eval, 'METRICS', [
        (_recorder(ran, 'm1'), 'm1'),
        (_recorder(ran, 'm2'), 'm2'),
        (_recorder(ran, 'm3'), 'm3'),
    ])
    assert run_eval.main(['--only', 'm1,m3']) == 0
    assert ran == ['m1', 'm3']


def test_only_with_unknown_metric_is_not_measured(monkeypatch, tmp_path):
    """指标名写错：一个都没跑出来，退出码 2（跟「跳过」同一档）。"""
    import eval.run_eval as run_eval
    ran = []
    monkeypatch.setattr(run_eval, 'RESULTS_DIR', tmp_path)
    monkeypatch.setattr(run_eval, 'METRICS', [(_recorder(ran, 'm1'), 'm1')])
    assert run_eval.main(['--only', 'typo']) == 2
    assert ran == []
