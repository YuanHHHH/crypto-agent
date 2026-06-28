from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langchain_core.messages import BaseMessage,SystemMessage,AIMessage,HumanMessage,ToolMessage
from src.agent.langchain_tools import get_coin_detail,get_price,get_market,search_rag
from langgraph.prebuilt import ToolNode
from src.agent.trace import trace_record
import json
import os
from dotenv import load_dotenv
load_dotenv()

mm_BASE_URL = os.getenv("LLM_BASE_URL")
mm_API_KEY = os.getenv("LLM_API_KEY")
base_url = mm_BASE_URL.replace("/chat/completions", "")

researcher = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)
tools = [get_price, get_market, get_coin_detail, search_rag]
researcher_with_tools = researcher.bind_tools(tools)

analyst = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)

reporter = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)

class Agent_State(TypedDict):
    user_question: str
    market_data:dict
    research_notes:list
    analysis_result:str
    final_report:str
    errors:list
    messages:Annotated[list[BaseMessage],add_messages]

def clean_think(content):
    if not isinstance(content, str):
        return content

    if "</think>" in content:
        return content.split("</think>", 1)[-1].strip()

    return content.strip()

def researcher_node(state:Agent_State):
    re_prompt = """
    你是 Crypto Market Researcher。

职责：
1. 根据用户问题获取必要的市场事实和项目资料。
2. 只能使用分配给你的数据工具。
3. 优先获取可验证的数据，例如价格、24h 涨跌幅、市值、成交量、项目基本信息。
4. 不输出投资建议，不做趋势判断。
5. 不要编造工具未返回的数据。
6. 对于需要市场事实的问题，优先调用合适的数据工具。
7. 你只负责决定调用哪些工具，不负责分析和生成最终报告。
    """
    re_input = [
        SystemMessage(content=re_prompt),
        HumanMessage(content=state["user_question"]),
    ]
    response = researcher_with_tools.invoke(re_input)
    return {
        "messages":[response],
    }

def research_finalize_node(state:Agent_State):
    msgs_list = state["messages"]

    latest_tool_call_ids = set()

    for msg in reversed(msgs_list):
        if isinstance(msg,AIMessage) and msg.tool_calls:
            latest_tool_call_ids = {
                tool_call.get("id")
                for tool_call in msg.tool_calls
                if tool_call.get("id")
            }
            break

    current_tool_messages = [
        msg
        for msg in msgs_list
        if isinstance(msg,ToolMessage)
        and msg.tool_call_id in latest_tool_call_ids
    ]

    market_data = {}
    research_notes = []
    errors = []

    market_tool_mapping = {
        "get_price": "price",
        "get_market": "market",
        "get_coin_detail": "coin_detail",
    }

    for tool_msg in current_tool_messages:
        try:
            parsed_content = json.loads(tool_msg.content)
        except (json.JSONDecodeError, TypeError) as e:
            errors.append({
                "tool_name": tool_msg.name,
                "tool_call_id": tool_msg.tool_call_id,
                "error_type": type(e).__name__,
                "raw_content": str(tool_msg.content)[:300],
            })
            continue

        # 行情类工具：放进 market_data
        if tool_msg.name in market_tool_mapping:
            data_key = market_tool_mapping[tool_msg.name]
            market_data[data_key] = parsed_content

        # 资料检索类工具：放进 research_notes
        elif tool_msg.name == "search_rag":
            research_notes.append(parsed_content)

        # 未处理的工具：留下记录，方便后续扩展
        else:
            errors.append({
                "tool_name": tool_msg.name,
                "tool_call_id": tool_msg.tool_call_id,
                "error_type": "UnsupportedToolResult",
                "raw_content": str(tool_msg.content)[:300],
            })

    return {
        "market_data": market_data,
        "research_notes": research_notes,
        "errors": errors,
    }

def analyst_node(state:Agent_State):
    an_prompt = """
    你是 Crypto Market Analyst。

职责：
1. 只基于输入的 market_data 和 research_notes 做分析。
2. 将“事实”和“推断”明确分开。
3. 输出趋势观察、风险因素、机会信号和信息缺口。
4. 没有证据时必须说明“信息不足”，不能编造。
5. 不直接给出买卖指令，不承诺收益。
    """
    analyst_context = f"""
    用户问题：
    {state["user_question"]}

    市场事实：
    {json.dumps(state["market_data"], ensure_ascii=False, indent=2)}

    补充研究资料：
    {json.dumps(state["research_notes"], ensure_ascii=False, indent=2)}

    工具或数据异常：
    {json.dumps(state["errors"], ensure_ascii=False, indent=2)}
    """

    input_analyst = [
        SystemMessage(content=an_prompt),
        HumanMessage(content=analyst_context),
    ]

    response = analyst.invoke(input_analyst)
    return {
        "messages":[response],
        "analysis_result": clean_think(response.content),
    }

def reporter_node(state:Agent_State):
    rep_prompt = """
    你是 Report Generator。

职责：
1. 根据用户问题、市场事实和分析结论生成最终报告。
2. 不调用工具，不新增外部事实，不改写数据含义。
3. 明确区分“数据事实”“分析判断”“风险提示”。
4. 回答要简洁、结构清晰、面向普通用户。
5. 不构成投资建议。
    """
    reporter_context = f"""
    用户问题：
    {state["user_question"]}

    市场事实：
    {json.dumps(state["market_data"], ensure_ascii=False, indent=2)}

    补充研究资料：
    {json.dumps(state["research_notes"], ensure_ascii=False, indent=2)}

    分析结论：
    {state["analysis_result"]}

    工具或数据异常：
    {json.dumps(state["errors"], ensure_ascii=False, indent=2)}
    """

    input_reporter = [
        SystemMessage(content=rep_prompt),
        HumanMessage(content=reporter_context),
    ]
    response = reporter.invoke(input_reporter)
    return {
        "messages": [response],
        "final_report":clean_think(response.content)
    }

def route_after_researcher(state:Agent_State):
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tool_node"
    return "research_finalize_node"

tool_node = ToolNode(tools)


builder = StateGraph(Agent_State)

builder.add_node("researcher_node",researcher_node)
builder.add_node("tool_node",tool_node)

builder.add_node("research_finalize_node",research_finalize_node)
builder.add_node("analyst_node",analyst_node)
builder.add_node("reporter_node",reporter_node)

builder.add_edge(START,"researcher_node")
builder.add_conditional_edges(
    "researcher_node",
    route_after_researcher,
    {
        "tool_node": "tool_node",
        "research_finalize_node": "research_finalize_node",
    }
)
builder.add_edge("tool_node","research_finalize_node")
builder.add_edge("research_finalize_node","analyst_node")
builder.add_edge("analyst_node","reporter_node")
builder.add_edge("reporter_node",END)

checkpoint = InMemorySaver()

config = {
    "configurable":{
        "thread_id":"user1"
    }
}

graph = builder.compile(checkpointer = checkpoint)



def record_step(step):
    node_name, node_update = next(iter(step.items()))

    if "messages" in node_update:
        message_contents = [
            clean_think(msg.content)
            for msg in node_update["messages"]
        ]

        trace_record({
            "node_name": node_name,
            "node_update": json.dumps(
                message_contents,
                ensure_ascii=False
            )
        })

    else:
        trace_record({
            "node_name": node_name,
            "node_update": json.dumps(
                node_update,
                ensure_ascii=False,
                default=str
            )
        })

is_first_turn = True

while True:
    user_input = input("请输入要查询的问题：").strip()

    if user_input.lower() == "exit":
        break

    input_msgs = {
        "user_question": user_input,
        "messages": [HumanMessage(content=user_input)],
    }

    for step in graph.stream(
        input_msgs,
        config=config
    ):
        print(step)
        print("---")
        record_step(step)



