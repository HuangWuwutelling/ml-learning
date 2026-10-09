from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from .tools import (assess_severity, search_recall_history,
                    query_quality_manual, query_regulation, draft_capa)
from .prompts import SYSTEM_PROMPT, ROUTER_PROMPT
from .memory import get_memory

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str

TOOLS = [assess_severity, search_recall_history, query_quality_manual, query_regulation, draft_capa]

def get_llm():
    return ChatOpenAI(
        model='deepseek-chat',
        api_key=os.getenv('DEEPSEEK_API_KEY'),
        base_url='https://api.deepseek.com',
        temperature=0.1,
    )

def router_node(state: AgentState) -> AgentState:
    llm = get_llm()
    last = state['messages'][-1].content if state['messages'] else ''
    resp = llm.invoke([SystemMessage(content=ROUTER_PROMPT.format(user_input=last))])
    intent = resp.content.strip().lower()
    if intent not in ('complaint', 'knowledge', 'chat'):
        intent = 'chat'
    return {**state, 'intent': intent}

def agent_node(state: AgentState) -> AgentState:
    llm = get_llm().bind_tools(TOOLS)
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + state['messages']
    resp = llm.invoke(msgs)
    return {**state, 'messages': state['messages'] + [resp]}

def should_continue(state: AgentState) -> str:
    last = state['messages'][-1]
    if hasattr(last, 'tool_calls') and last.tool_calls:
        return 'tools'
    return END

def build_graph():
    g = StateGraph(AgentState)
    g.add_node('router', router_node)
    g.add_node('agent', agent_node)
    g.add_node('tools', ToolNode(TOOLS))
    g.add_edge(START, 'router')
    g.add_edge('router', 'agent')
    g.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
    g.add_edge('tools', 'agent')
    return g.compile(checkpointer=get_memory())

_GRAPH = None
def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH

def run(message: str, thread_id: str = 'default') -> str:
    g = get_graph()
    config = {'configurable': {'thread_id': thread_id}}
    result = g.invoke({'messages': [HumanMessage(content=message)], 'intent': ''}, config=config)
    return result['messages'][-1].content