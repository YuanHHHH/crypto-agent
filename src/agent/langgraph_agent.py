from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from typing import Literal,Annotated
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import BaseMessage,SystemMessage,AIMessage,HumanMessage,ToolMessage
from src.agent.langchain_tools import get_coin_detail,analyze_coin,get_price,get_market,search_rag
from langgraph.prebuilt import ToolNode
from src.agent.trace import trace_record
import os
from dotenv import load_dotenv
load_dotenv()

mm_BASE_URL = os.getenv("LLM_BASE_URL")
mm_API_KEY = os.getenv("LLM_API_KEY")
base_url = mm_BASE_URL.replace("/chat/completions", "")
llm = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)
tools = [get_price, get_market, get_coin_detail, analyze_coin,search_rag]
llm_with_tools = llm.bind_tools(tools)


class Agent_State(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]
    tool_approved:str


def think_node(state:Agent_State):
    response = llm_with_tools.invoke(state["messages"])
    return {
        "messages":[response]
    }

def route_after_think(state:Agent_State)-> Literal["tools", "end"]:
    ai_last_msg = state["messages"][-1]
    if ai_last_msg.tool_calls:
        return "tools"
    return "end"

def interrupt_node(state:Agent_State):
    last_msg = state["messages"][-1]
    tool_calls = []
    if isinstance(last_msg, AIMessage):
        tool_calls = last_msg.tool_calls

    human_feedback = interrupt(
        {
            "question":"模型准备调用工具，是否允许？请输入 yes 或 no。",
            "tool_calls":tool_calls,
            "response":["yes","no"]
        }
    )
    if human_feedback == "no":
        return {
        "tool_approved": "no"
    }
    else:
        return {
        "tool_approved": "yes"
    }

def route_after_interrupt(state:Agent_State)-> Literal["tools", "reject"]:
    if state["tool_approved"] == "yes":
        return "tools"
    return "reject"

def reject_node(state:Agent_State):
    return {
        "messages":[AIMessage(content="用户拒绝调用工具，本轮会话终止")]
    }

tool_node = ToolNode(tools)


builder = StateGraph(Agent_State)

builder.add_node("think_node",think_node)
builder.add_node("tool_node",tool_node)
builder.add_node("interrupt_node",interrupt_node)
builder.add_node("reject_node",reject_node)

builder.add_edge(START,"think_node")
builder.add_conditional_edges("think_node",
                              route_after_think,
                              {
                                  "tools":"interrupt_node",
                                  "end":END
                              })

builder.add_conditional_edges(
    "interrupt_node",
    route_after_interrupt,
    {
        "tools":"tool_node",
        "reject":"reject_node"
    }
)
builder.add_edge("tool_node","think_node")
builder.add_edge("reject_node",END)

checkpoint = InMemorySaver()

config = {
    "configurable":{
        "thread_id":"user1"
    }
}

graph = builder.compile(checkpointer = checkpoint)


system_prompt = """你是一个加密货币分析助手。
用户问实时价格、市场数据时，使用对应工具查询真实数据，禁止编造。
用户问概念性问题时，使用知识库检索工具。
回答要准确、简洁，基于工具返回的真实数据。"""


def record_step(step):
    if "__interrupt__" in step:
        trace_record({
            "node_name": "__interrupt__",
            "node_update": str(step["__interrupt__"])
        })
        return True  # 表示遇到了 interrupt

    node_name, node_update = next(iter(step.items()))
    if "messages" in node_update:
        trace_record({
            "node_name": node_name,
            "node_update": node_update["messages"][0].content
        })
    else:
        trace_record({
            "node_name": node_name,
            "node_update": str(node_update)
        })
    return False

is_first_turn = True

while True:
    user_input = input("请输入要查询的问题：")
    if user_input == "exit":
        break
    if is_first_turn:
        input_msgs = {
        "messages": [SystemMessage(content=system_prompt), HumanMessage(content=user_input)]
    }
        is_first_turn = False
    else:
        input_msgs = {
            "messages":[HumanMessage(content=user_input)]
        }

    for step in graph.stream(
            input_msgs,
            config=config
    ):
        print(step)
        print("---")

        is_interrupt = record_step(step)

        if is_interrupt:
            human_decision = input("请决定是否使用工具？请输入 yes 或 no：").strip().lower()
            while human_decision not in ["yes","no"]:
                human_decision = input("输入错误，请输入 yes 或 no：").strip().lower()


            for resume_step in graph.stream(
                    Command(resume=human_decision),
                    config=config
            ):
                print(resume_step)
                print("---")

                record_step(resume_step)
            break


