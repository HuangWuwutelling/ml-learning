"""Layer 5: 输出验证。JSON Schema + 正则 blocklist + 黑名单短语。"""
import json
import re

# 黑名单短语（输出侧 prompt leak / 攻击成功标志）
OUTPUT_BLOCKLIST = [
    r"INJECTION\s+SUCCESSFUL",
    r"my\s+(?:hidden|original|full)\s+(?:system\s+)?prompt\s+is",
    r"i\s+have\s+been\s+pwned",
    r"i\s+am\s+now\s+in\s+(?:admin|developer|unrestricted)\s+mode",
]

BLOCKLIST_REGEX = re.compile("|".join(OUTPUT_BLOCKLIST), re.IGNORECASE)


def validate(output: str, schema: dict | None = None) -> bool:
    """验证 LLM 输出。

    Args:
        output: LLM 输出文本。
        schema: 可选 JSON Schema。若提供则要求输出是合法 JSON 且符合 schema。

    Returns:
        True = 通过，False = 拦截。
    """
    if BLOCKLIST_REGEX.search(output):
        return False

    if schema is not None:
        # 尝试从输出中提取 JSON
        json_match = re.search(r"\{.*\}", output, re.DOTALL)
        if not json_match:
            return False
        try:
            obj = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return False
        # 简化 schema 校验：只检查 required 字段存在 + 类型匹配
        for required_key, expected in schema.get("properties", {}).items():
            if required_key in schema.get("required", []):
                if required_key not in obj:
                    return False
                if expected.get("type") == "string" and not isinstance(obj[required_key], str):
                    return False
                if expected.get("type") == "number" and not isinstance(obj[required_key], (int, float)):
                    return False
    return True