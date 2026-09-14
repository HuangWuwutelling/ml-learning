"""6 层防线管线。任意一层 block 则短路返回。"""
import time
from defenses.layer1_preprocess import preprocess
from defenses.layer2_detect import detect
from defenses.layer3_spotlight import wrap_user_input
from defenses.layer4_harden import harden
from defenses.layer5_validate import validate
from defenses.layer6_sandbox import check_tool_call


class Orchestrator:
    """6 层防御管线。"""

    def __init__(self, layers: list[int], base_system_prompt: str, llm_call):
        """初始化。

        Args:
            layers: 启用的 layer 编号列表（如 [1,2,3,4,5,6] 或 [2] 或 []）。
            base_system_prompt: 原始 system prompt。
            llm_call: callable(system, user) -> str，注入便于测试 mock。
        """
        self.layers = layers
        self.base_system_prompt = base_system_prompt
        self.llm_call = llm_call

    def process(self, user_input: str) -> dict:
        """执行 6 层管线。

        Returns:
            {
              "response": str,           # LLM 输出（blocked 时为空）
              "blocked": bool,
              "blocked_by": int | None,  # 哪一层拦截
              "latency_ms": float,       # 总耗时 ms
              "log": list[dict],         # 每层的执行日志
            }
        """
        start = time.perf_counter()
        log = []
        blocked = False
        blocked_by = None
        response = ""
        current_text = user_input

        # Layer 1: 输入预处理
        if 1 in self.layers:
            current_text = preprocess(current_text)
            log.append({"layer": 1, "action": "preprocess", "out_len": len(current_text)})

        # Layer 2: 攻击检测
        if 2 in self.layers:
            label, score = detect(current_text)
            log.append({"layer": 2, "label": label, "score": score})
            if label == "attack":
                blocked = True
                blocked_by = 2

        # Layer 3: Prompt 隔离
        if 3 in self.layers and not blocked:
            current_text = wrap_user_input(current_text)
            log.append({"layer": 3, "action": "spotlight_wrap", "out_len": len(current_text)})

        # Layer 4: System prompt 加固
        system_prompt = self.base_system_prompt
        if 4 in self.layers:
            system_prompt = harden(self.base_system_prompt)
            log.append({"layer": 4, "system_prompt_len": len(system_prompt)})

        # 调用 LLM（如未在前层被 block）
        if not blocked:
            response = self.llm_call(system_prompt, current_text)
            log.append({"layer": "llm", "out_len": len(response)})

        # Layer 5: 输出验证
        if 5 in self.layers and not blocked:
            ok = validate(response, schema=None)
            log.append({"layer": 5, "valid": ok})
            if not ok:
                blocked = True
                blocked_by = 5
                response = ""

        # Layer 6: 行动沙盒（示例：检测 LLM 输出是否包含 tool_call 关键词）
        # （真实场景中 LLM 会以 JSON 形式输出 tool_call，此处简化匹配）
        if 6 in self.layers and not blocked:
            import re
            tool_match = re.search(r"call\s+(\w+)\s*\(", response.lower())
            if tool_match:
                tool_name = tool_match.group(1)
                allowed, reason = check_tool_call(tool_name, {})
                log.append({"layer": 6, "tool": tool_name, "allowed": allowed, "reason": reason})
                if not allowed:
                    blocked = True
                    blocked_by = 6
                    response = ""

        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "response": response,
            "blocked": blocked,
            "blocked_by": blocked_by,
            "latency_ms": round(latency_ms, 2),
            "log": log,
        }
