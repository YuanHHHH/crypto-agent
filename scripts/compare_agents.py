"""
三版 Agent 对比测试脚本
测试手写版 / LangChain 版 / LangGraph 版在同一组问题上的表现

用法：python scripts/compare_agents.py
"""

import time
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()


# ========== 测试用例 ==========
TEST_QUESTIONS = [
    {"id": 1, "question": "BTC 现在多少钱", "type": "单工具"},
    {"id": 2, "question": "以太坊最近的市场数据怎么样", "type": "单工具"},
    {"id": 3, "question": "现在加密市场整体行情如何", "type": "单工具"},
    {"id": 4, "question": "你好，你是谁", "type": "无工具"},
    {"id": 5, "question": "对比一下 BTC 和 ETH 的价格", "type": "多工具"},
]


# ========== 手写版 Agent ==========
def run_handwritten(question: str) -> dict:
    """调用 Week 5-6 的手写 ReAct Agent"""
    from src.agent.agent_runner import AgentRunner

    runner = AgentRunner()
    start = time.time()
    try:
        final_answer, step_log = runner.run(question)
        elapsed = time.time() - start
        return {
            "version": "handwritten",
            "success": bool(final_answer and len(str(final_answer)) > 0),
            "answer": str(final_answer) if final_answer else "",
            "steps": len(step_log) if step_log else 0,
            "time": round(elapsed, 2),
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "version": "handwritten",
            "success": False,
            "answer": "",
            "steps": 0,
            "time": round(elapsed, 2),
            "error": str(e)
        }
    finally:
        runner.reset()


# ========== LangChain 版 Agent ==========
def run_langchain(question: str) -> dict:
    """调用 Week 7 的 LangChain Agent"""
    from src.agent.langchain_tools import get_coin_detail, analyze_coin, get_price, get_market
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

规则:
- 每次只能调用一个工具
- 不要编造数据，所有价格和市场数据都必须通过工具获取
- 重要：每一次回复都必须以 "Thought:" 开头
- 禁止在输出中包含 [TOOL_CALL] 等标签

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

    lc_tools = [get_coin_detail, analyze_coin, get_price, get_market]

    langchain_agent = create_react_agent(llm_model, tools=lc_tools, prompt=prompt)

    executor = AgentExecutor(
        agent=langchain_agent,
        tools=lc_tools,
        verbose=False,
        max_iterations=5,
        handle_parsing_errors=True,
        memory=memory,
    )

    start = time.time()
    try:
        result = executor.invoke({"input": question})
        elapsed = time.time() - start
        output = result.get("output", "")
        return {
            "version": "langchain",
            "success": bool(output and "Agent stopped" not in output),
            "answer": output,
            "steps": len(result.get("intermediate_steps", [])),
            "time": round(elapsed, 2),
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "version": "langchain",
            "success": False,
            "answer": "",
            "steps": 0,
            "time": round(elapsed, 2),
            "error": str(e)
        }


# ========== LangGraph 版 Agent ==========
def run_langgraph(question: str) -> dict:
    """调用 Week 9 的 LangGraph Agent（不启用 interrupt）"""
    from langchain_openai import ChatOpenAI
    from langgraph.graph import StateGraph, START, END
    from typing import Literal, Annotated
    from typing_extensions import TypedDict
    from langgraph.graph.message import add_messages
    from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
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

    class TestState(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]

    def think_node(state: TestState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def route_after_think(state: TestState) -> Literal["tools", "end"]:
        if state["messages"][-1].tool_calls:
            return "tools"
        return "end"

    tool_node = ToolNode(tools)
    builder = StateGraph(TestState)
    builder.add_node("think_node", think_node)
    builder.add_node("tool_node", tool_node)
    builder.add_edge(START, "think_node")
    builder.add_conditional_edges("think_node", route_after_think, {"tools": "tool_node", "end": END})
    builder.add_edge("tool_node", "think_node")
    graph = builder.compile()

    system_prompt = """你是一个加密货币分析助手。
用户问实时价格、市场数据时，使用对应工具查询真实数据，禁止编造。
用户问概念性问题时，使用知识库检索工具。
回答要准确、简洁，基于工具返回的真实数据。"""

    start = time.time()
    step_count = 0
    try:
        final_content = ""
        for step in graph.stream({
            "messages": [SystemMessage(content=system_prompt), HumanMessage(content=question)]
        }):
            step_count += 1
            if "think_node" in step:
                msg = step["think_node"]["messages"][0]
                if not msg.tool_calls and msg.content:
                    final_content = msg.content

        elapsed = time.time() - start
        return {
            "version": "langgraph",
            "success": bool(final_content and len(final_content) > 0),
            "answer": final_content,
            "steps": step_count,
            "time": round(elapsed, 2),
            "error": None
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "version": "langgraph",
            "success": False,
            "answer": "",
            "steps": step_count,
            "time": round(elapsed, 2),
            "error": str(e)
        }


# ========== 主流程 ==========
def run_all_tests():
    results = []

    for test in TEST_QUESTIONS:
        q = test["question"]
        qid = test["id"]
        qtype = test["type"]
        print(f"\n{'='*60}")
        print(f"测试 {qid}: {q} ({qtype})")
        print(f"{'='*60}")

        # 手写版
        print(f"\n--- 手写版 ---")
        r1 = run_handwritten(q)
        print(f"  成功: {r1['success']} | 步数: {r1['steps']} | 耗时: {r1['time']}s")
        if r1['error']:
            print(f"  错误: {r1['error']}")
        else:
            answer_preview = r1['answer'][:100] if r1['answer'] else "(空)"
            print(f"  回答: {answer_preview}")
        r1["question_id"] = qid
        r1["question"] = q
        r1["question_type"] = qtype
        results.append(r1)

        time.sleep(3)

        # LangChain 版
        print(f"\n--- LangChain 版 ---")
        r2 = run_langchain(q)
        print(f"  成功: {r2['success']} | 步数: {r2['steps']} | 耗时: {r2['time']}s")
        if r2['error']:
            print(f"  错误: {r2['error']}")
        else:
            answer_preview = r2['answer'][:100] if r2['answer'] else "(空)"
            print(f"  回答: {answer_preview}")
        r2["question_id"] = qid
        r2["question"] = q
        r2["question_type"] = qtype
        results.append(r2)

        time.sleep(3)

        # LangGraph 版
        print(f"\n--- LangGraph 版 ---")
        r3 = run_langgraph(q)
        print(f"  成功: {r3['success']} | 步数: {r3['steps']} | 耗时: {r3['time']}s")
        if r3['error']:
            print(f"  错误: {r3['error']}")
        else:
            answer_preview = r3['answer'][:100] if r3['answer'] else "(空)"
            print(f"  回答: {answer_preview}")
        r3["question_id"] = qid
        r3["question"] = q
        r3["question_type"] = qtype
        results.append(r3)

        time.sleep(3)

    # 保存结果
    output_path = "data/eval/compare_results.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已保存到 {output_path}")

    # 打印汇总表
    print(f"\n{'='*60}")
    print("汇总")
    print(f"{'='*60}")
    print(f"{'版本':<15} {'成功率':<10} {'平均步数':<10} {'平均耗时':<10}")
    print(f"{'-'*45}")

    for version in ["handwritten", "langchain", "langgraph"]:
        version_results = [r for r in results if r["version"] == version]
        success_count = sum(1 for r in version_results if r["success"])
        total = len(version_results)
        avg_steps = sum(r["steps"] for r in version_results) / total if total > 0 else 0
        avg_time = sum(r["time"] for r in version_results) / total if total > 0 else 0
        success_rate = f"{success_count}/{total}"
        print(f"{version:<15} {success_rate:<10} {avg_steps:<10.1f} {avg_time:<10.1f}s")

    # 打印逐题对比
    print(f"\n{'='*60}")
    print("逐题对比")
    print(f"{'='*60}")
    print(f"{'题目':<25} {'手写版':<10} {'LangChain':<10} {'LangGraph':<10}")
    print(f"{'-'*55}")

    for test in TEST_QUESTIONS:
        qid = test["id"]
        q_short = test["question"][:20]
        r_hw = next((r for r in results if r["question_id"] == qid and r["version"] == "handwritten"), None)
        r_lc = next((r for r in results if r["question_id"] == qid and r["version"] == "langchain"), None)
        r_lg = next((r for r in results if r["question_id"] == qid and r["version"] == "langgraph"), None)

        hw_status = "pass" if r_hw and r_hw["success"] else "FAIL"
        lc_status = "pass" if r_lc and r_lc["success"] else "FAIL"
        lg_status = "pass" if r_lg and r_lg["success"] else "FAIL"

        print(f"{q_short:<25} {hw_status:<10} {lc_status:<10} {lg_status:<10}")


if __name__ == "__main__":
    run_all_tests()