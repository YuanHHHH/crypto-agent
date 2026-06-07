"""
三版 Agent 的统一执行和提取模块
每个版本跑完后，提取成统一格式供 eval_rules 和 eval_judge 使用

统一格式：
{
    "final_answer": "Agent 最终回答文本",
    "tools_called": ["get_price", "get_market"],
    "total_steps": 3,
    "tool_results": [{"price": 78000, ...}, {...}],
}
"""

import os
import json
import time
from dotenv import load_dotenv


load_dotenv()


def run_langgraph_for_eval(question):
    """
    跑 LangGraph 版 Agent（不带 interrupt），返回统一格式

    注意：每次调用都新建 graph，避免 checkpointer 状态互相干扰
    """
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, START, END
    from typing import Literal, Annotated
    from typing_extensions import TypedDict
    from langgraph.graph.message import add_messages
    from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
    from src.agent.langchain_tools import get_coin_detail, analyze_coin, get_price, get_market, search_rag
    from langgraph.prebuilt import ToolNode

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
    tools = [get_price, get_market, get_coin_detail, analyze_coin, search_rag]
    llm_with_tools = llm.bind_tools(tools)

    class EvalState(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]

    def think_node(state: EvalState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def route_after_think(state: EvalState) -> Literal["tools", "end"]:
        if state["messages"][-1].tool_calls:
            return "tools"
        return "end"

    tool_node = ToolNode(tools)
    builder = StateGraph(EvalState)
    builder.add_node("think_node", think_node)
    builder.add_node("tool_node", tool_node)
    builder.add_edge(START, "think_node")
    builder.add_conditional_edges("think_node", route_after_think, {"tools": "tool_node", "end": END})
    builder.add_edge("tool_node", "think_node")
    graph = builder.compile()  # 不带 interrupt，不带 checkpointer

    system_prompt = """你是一个加密货币分析助手。
用户问实时价格、市场数据时，使用对应工具查询真实数据，禁止编造。
用户问概念性问题时，使用知识库检索工具。
回答要准确、简洁，基于工具返回的真实数据。"""

    # 收集结果
    tools_called = []
    tool_results = []
    total_steps = 0
    final_answer = ""

    try:
        for step in graph.stream({
            "messages": [SystemMessage(content=system_prompt), HumanMessage(content=question)]
        }):
            total_steps += 1

            if "think_node" in step:
                msg = step["think_node"]["messages"][0]
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        # 这一步 LLM 决定调工具
                        for tc in msg.tool_calls:
                            tools_called.append(tc["name"])
                    else:
                        # 没有 tool_calls，这是最终回答
                        final_answer = msg.content

            elif "tool_node" in step:
                # 工具执行结果
                for msg in step["tool_node"]["messages"]:
                    if isinstance(msg, ToolMessage):
                        try:
                            tool_results.append(json.loads(msg.content))
                        except json.JSONDecodeError:
                            tool_results.append({"raw": msg.content})

    except Exception as e:
        final_answer = f"[ERROR] {str(e)}"

    return {
        "final_answer": final_answer,
        "tools_called": tools_called,
        "total_steps": total_steps,
        "tool_results": tool_results,
    }


def run_handwritten_for_eval(question):
    """
    跑手写版 Agent，返回统一格式
    """
    from src.agent.agent_runner import AgentRunner

    runner = AgentRunner()

    tools_called = []
    tool_results = []

    try:
        final_answer, step_log = runner.run(question)

        # 从 step_log 里提取工具调用信息
        for step in step_log:
            if step.get("type") == "action":
                tools_called.append(step.get("action", ""))
                # observation 是字符串，尝试解析成 dict
                obs = step.get("observation", "")
                if isinstance(obs, str):
                    try:
                        if "Observation:" in obs:
                            json_part = obs.split("Observation:", 1)[1].strip()
                        else:
                            json_part = obs.strip()

                        tool_results.append(json.loads(json_part))
                    except json.JSONDecodeError:
                        tool_results.append({"raw": obs})

        return {
            "final_answer": str(final_answer) if final_answer else "",
            "tools_called": tools_called,
            "total_steps": len(step_log),
            "tool_results": tool_results,
        }

    except Exception as e:
        return {
            "final_answer": f"[ERROR] {str(e)}",
            "tools_called": [],
            "total_steps": 0,
            "tool_results": [],
        }
    finally:
        runner.reset()


def run_langchain_for_eval(question):
    """
    跑 LangChain 版 Agent，返回统一格式
    """
    from src.agent.langchain_tools import get_coin_detail, analyze_coin, get_price, get_market,search_rag
    from langchain.agents import create_react_agent, AgentExecutor
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    from langchain.memory import ConversationBufferMemory

    mm_BASE_URL = os.getenv("LLM_BASE_URL")
    mm_API_KEY = os.getenv("LLM_API_KEY")
    base_url = mm_BASE_URL.replace("/chat/completions", "")

    prompt_text = """你是一个加密货币分析 Agent。你需要根据用户的问题，决定是否使用工具来获取数据，然后给出分析。
TOOLS:
------

Assistant has access to the following tools:

{tools}

To use a tool, please use the following format:
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
Thought: Do I need to use a tool? No
Final Answer: [your response here]

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
"""

    prompt = PromptTemplate(
        template=prompt_text,
        input_variables=["tools", "tool_names", "chat_history", "input", "agent_scratchpad"],
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=False)

    llm_model = ChatOpenAI(
        model="MiniMax-M2.7",
        base_url=base_url,
        api_key=mm_API_KEY,
        temperature=0.7,
        max_tokens=1000
    )

    lc_tools = [get_coin_detail, analyze_coin, get_price, get_market,search_rag]
    langchain_agent = create_react_agent(llm_model, tools=lc_tools, prompt=prompt)

    executor = AgentExecutor(
        agent=langchain_agent,
        tools=lc_tools,
        verbose=False,
        max_iterations=5,
        handle_parsing_errors=True,
        memory=memory,
        return_intermediate_steps=True
    )

    tools_called = []
    tool_results = []

    try:
        result = executor.invoke({"input": question})
        output = result.get("output", "")

        # 从 intermediate_steps 提取工具调用
        for action, observation in result.get("intermediate_steps", []):
            tools_called.append(action.tool)
            if isinstance(observation, dict):
                tool_results.append(observation)
            elif isinstance(observation, str):
                try:
                    tool_results.append(json.loads(observation))
                except json.JSONDecodeError:
                    tool_results.append({"raw": observation})

        success = bool(output and "Agent stopped" not in output)

        return {
            "final_answer": output if success else f"[FAILED] {output}",
            "tools_called": tools_called,
            "total_steps": len(result.get("intermediate_steps", [])),
            "tool_results": tool_results,
        }

    except Exception as e:
        return {
            "final_answer": f"[ERROR] {str(e)}",
            "tools_called": [],
            "total_steps": 0,
            "tool_results": [],
        }