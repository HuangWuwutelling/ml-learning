"""Layer 2: 攻击检测。启发式正则评分（production 可换 Prompt Guard 2）。"""
import re

# 高危关键词 / 短语（直接注入、越权、工具调用）
PATTERNS = [
    (r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|commands?|rules?)", 0.95),
    (r"disregard\s+(?:all|any|the)\s+(?:prior|previous|safety)", 0.95),
    (r"forget\s+everything", 0.85),
    (r"system\s+override|admin\s+mode|developer\s+mode", 0.9),
    (r"(?:i\s+am|i'm)\s+(?:the\s+)?(?:system\s+)?(?:admin|administrator|root|developer)", 0.85),
    (r"bypass\s+(?:all\s+)?(?:safety|restrictions?|filters?)", 0.9),
    (r"reveal\s+(?:your\s+)?(?:system\s+)?prompt|hidden\s+instructions?", 0.85),
    (r"(?:reveal|print|show|leak|dump)\s+(?:your\s+)?(?:full\s+)?(?:system|hidden|original)\s+prompt", 0.9),
    (r"\b(?:send_email|delete_all_files|database_query|shell_command|transfer_money|send_sms)\s*\(", 0.85),
    (r"\bsudo\s+|\brm\s+-rf\s+/", 0.95),
    (r"acting\s+as\s+root|priority\s+override|maintenance\s+command|admin\s+console", 0.85),
    (r"\[system\]|\[admin\]\s*console|jwt\s+verified", 0.85),
]

THRESHOLD = 0.6


def detect(text: str) -> tuple[str, float]:
    """对输入文本做攻击检测。

    Args:
        text: 用户输入（已 preprocess）。

    Returns:
        (label, score) 其中 label ∈ {"attack", "benign"}，score ∈ [0, 1]。
    """
    text_lower = text.lower()
    max_score = 0.0
    for pattern, weight in PATTERNS:
        if re.search(pattern, text_lower):
            max_score = max(max_score, weight)
    label = "attack" if max_score >= THRESHOLD else "benign"
    return label, max_score