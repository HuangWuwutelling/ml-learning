"""Gradio UI for environmental compliance AI Agent."""
import os

# 避免 Gradio 启动自检时被代理拦截（Windows 上用 httpx 会读取注册表代理设置）
# NO_PROXY 始终设上绕过本地地址；HTTP_PROXY 从环境变量读取，不硬编码
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost,0.0.0.0")

import gradio as gr

from agent import build_agent

agent = build_agent()


def respond(message: str, history: list):
    """Process a user message through the LangGraph agent and return the response.

    Gradio 6 passes history as a list of openai-style dicts
    [{"role": "user"|"assistant", "content": str}, ...].
    Pass the full conversation to the agent so it remembers context.
    """
    messages = list(history or [])
    messages.append({"role": "user", "content": message})

    result = agent.invoke({"messages": messages})
    return result["messages"][-1].content


CUSTOM_CSS = """
#title { text-align: center; margin-bottom: 0.5em; }
"""

EXAMPLES = [
    "我想办排污许可证",
    "印染行业的废水排放标准是多少",
    "帮我算一下钢铁厂的废气排放量",
    "排污申报需要什么材料",
]

with gr.Blocks(title="环保申报 AI 助手", fill_height=True) as demo:
    gr.Markdown(
        "# 环保申报 AI 助手\n"
        "帮你完成排污许可证申报——查法规、算排放、填表单、出报告。",
        elem_id="title",
    )

    chatbot = gr.ChatInterface(
        fn=respond,
        title="",
        description="在下方输入你的问题，AI 助手会一步步引导你完成申报。",
        examples=EXAMPLES,
    )


if __name__ == "__main__":
    print("Starting env_agent on http://localhost:7861", flush=True)
    demo.launch(css=CUSTOM_CSS, server_port=7861)
