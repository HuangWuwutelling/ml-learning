"""LangGraph agent for environmental compliance declaration."""
import os
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from config import config
from tools import lookup_regulation, calculate_emission, calculate_air_emission, fill_form, generate_report


def _load_prompt() -> str:
    """Load system prompt from prompt.md."""
    path = os.path.join(os.path.dirname(__file__), "prompt.md")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def build_agent():
    llm = ChatOpenAI(
        model=config.LLM_MODEL,
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_API_BASE,
        temperature=0.3,
    )

    tools = [
        lookup_regulation,
        calculate_emission,
        calculate_air_emission,
        fill_form,
        generate_report,
    ]

    llm_with_tools = llm.bind_tools(tools)

    agent = create_react_agent(
        model=llm_with_tools,
        tools=tools,
        prompt=_load_prompt(),
        checkpointer=MemorySaver(),
    )

    return agent
