"""工具类指标的判定口径。

这个模块只有纯函数：不 import Django / LangChain / 向量库，也不碰网络。
这样 `tests/test_eval_scoring.py` 能在离线环境下把判定逻辑整个跑完，
不用真调 LLM 也能验证「打分定义」本身没写错。

`run_eval.py` 从这里 import，保证「口径」和「跑分的脚本」是同一份定义，
不会各写各的。
"""


def tool_set_scores(called, expected):
    """一次工具选择打分的口径。

    called / expected：工具名列表（可以重复，顺序不计）。
    返回 precision / recall / f1 / exact 四个 0-1 的数。

    - 集合口径：调用顺序不影响得分，同一个工具调多次只算一次。
    - expected 为空时，正确行为就是一次都不调。
    - exact = 1.0 表示调用的工具集合与预期完全一致（该调的调了，不该调的一个没多调）。
    - f1 是集合级 F1：少调会压低 recall，多调会压低 precision，两者都罚。
    """
    called_set = set(called)
    expected_set = set(expected)
    if not expected_set:
        p = 1.0 if not called_set else 0.0
        return {'precision': p, 'recall': p, 'f1': p, 'exact': p}
    hit = len(called_set & expected_set)
    precision = hit / len(called_set) if called_set else 0.0
    recall = hit / len(expected_set)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    exact = 1.0 if called_set == expected_set else 0.0
    return {'precision': precision, 'recall': recall, 'f1': f1, 'exact': exact}


def no_tool_score(called, reply_text):
    """「这 8 条不该调工具」的判定口径。

    正确 = 一次工具都没调，并且 agent 仍然回了一句话。
    只看回复长度是不够的：调了工具也能回一段长文字。
    """
    no_tool = 1.0 if not set(called) else 0.0
    replied = 1.0 if (reply_text and str(reply_text).strip()) else 0.0
    return {'no_tool': no_tool, 'replied': replied, 'ok': 1.0 if (no_tool and replied) else 0.0}
