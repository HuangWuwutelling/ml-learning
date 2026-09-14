"""Layer 1: 输入预处理。零宽字符 + Unicode normalize + 控制字符过滤。"""
import re
import unicodedata

# Use chr() to safely encode zero-width characters
ZERO_WIDTH_CHARS = (chr(0x200B), chr(0x200C), chr(0x200D), chr(0xFEFF))
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
MAX_CHARS = 4000  # 防止超长 prompt 绕过 attention


def preprocess(text: str) -> str:
    """清洗输入文本：去零宽 + NFC normalize + 控制字符过滤 + 截断。

    Args:
        text: 原始用户输入。

    Returns:
        清洗后的字符串。
    """
    for zw in ZERO_WIDTH_CHARS:
        text = text.replace(zw, "")
    text = unicodedata.normalize("NFKC", text)
    text = CONTROL_CHARS.sub("", text)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
    return text