"""Gradio UI for environmental compliance AI Agent."""
import uuid
import gradio as gr

from agent import build_agent

agent = build_agent()


def respond(message: str, history: list):
    """Process a user message through the LangGraph agent and return the response."""
    thread_id = str(uuid.uuid4())
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content


CUSTOM_CSS = """
#title { text-align: center; margin-bottom: 0.5em; }
#subtitle { text-align: center; color: #656d76; font-size: 14px; margin-bottom: 1em; }
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
    demo.launch(css=CUSTOM_CSS)
