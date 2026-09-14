"""Layer 6: 行动沙盒。工具白名单 + 高风险工具人工确认。"""

# 工具白名单（允许调用的工具）
TOOL_WHITELIST = {
    "get_weather",
    "search_docs",
    "calculate",
    "translate",
    "summarize",
    "delete_record",  # 即使在白名单也是高风险
}

# 高风险工具（即使在白名单也需人工确认）
HIGH_RISK_TOOLS = {
    "delete_record",
    "delete_all_files",
    "transfer_money",
    "send_email",
    "send_sms",
    "shell_command",
    "database_query",
}


def check_tool_call(tool_name: str, args: dict) -> tuple[bool, str]:
    """检查 LLM 提议的工具调用是否允许。

    Args:
        tool_name: 工具名。
        args: 工具参数。

    Returns:
        (allowed, reason)。allowed=True 表示通过，False 表示拦截。
    """
    if tool_name not in TOOL_WHITELIST:
        return False, f"tool '{tool_name}' not in whitelist"

    if tool_name in HIGH_RISK_TOOLS:
        return True, f"tool '{tool_name}' requires human confirmation before execution"

    return True, "ok"