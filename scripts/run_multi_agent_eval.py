# scripts/run_multi_agent_eval.py
"""
Week 11 Day 5: Multi-Agent Eval

独立评估：
1. 单 LangGraph Agent（复用 Week 10 runner）
2. 固定流程 Multi-Agent
3. Supervisor 动态路由 Multi-Agent

说明：
- 不 import Day 3 / Day 4 的交互式脚本，避免触发 while input()。
- Multi-Agent 图逻辑在本文件内作为测试快照维护。
- 输出写到独立结果文件，不覆盖 Week 10 的 eval_result.jsonl。
"""

import json
import os
import time
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from typing_extensions import TypedDict

from src.agent.eval_judge import judge_response
from src.agent.eval_rules import evaluate_rules
from src.agent.eval_runners import run_langgraph_for_eval
from src.agent.langchain_tools import get_coin_detail, get_market, get_price, search_rag


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVAL_SET_PATH = PROJECT_ROOT / "data" / "eval" / "eval_set_multi_agent_v1.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "eval" / "eval_result_multi_agent_v1.jsonl"

# Kimi / MiniMax 出现网络抖动时，可改为 20 或 30。
RUN_PAUSE_SECONDS = 8
JUDGE_PAUSE_SECONDS = 8

TOOLS = [get_price, get_market, get_coin_detail, search_rag]


class MultiAgentEvalState(TypedDict):
    user_question: str
    market_data: dict
    research_notes: list
    analysis_result: str
    final_report: str
    errors: list
    route_count: int
    max_route_count: int
    route_reason: str
    next_agent: str
    messages: Annotated[list[BaseMessage], add_messages]


RESEARCHER_PROMPT = """
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

ANALYST_PROMPT = """
你是 Crypto Market Analyst。

职责：
1. 只基于输入的 market_data 和 research_notes 做分析。
2. 将“事实”和“推断”明确分开。
3. 输出趋势观察、风险因素、机会信号和信息缺口。
4. 没有证据时必须说明“信息不足”，不能编造。
5. 不直接给出买卖指令，不承诺收益。

不得从单一时点价格、24小时涨跌幅、24小时高低点或全市场概览，
推导出明确的支撑位、阻力位、趋势反转、长期趋势、资金流向、
主力行为、下跌原因或未来价格目标。

若仅有24小时数据，只能描述“过去24小时的价格变化”和
“BTC与全市场是否同向变化”。

涉及支撑、阻力、趋势、资金流向、原因、未来走势时，
必须明确写“当前数据不足以确认”或“需要历史K线、链上数据、
成交量变化或资金流数据进一步验证”。
"""

REPORTER_PROMPT = """
你是 Report Generator。

职责：
1. 根据用户问题、市场事实和分析结论生成最终报告。
2. 不调用工具，不新增外部事实，不改写数据含义。
3. 明确区分“数据事实”“分析判断”“风险提示”。
4. 回答要简洁、结构清晰、面向普通用户。
5. 不构成投资建议。

不得把 Analyst 的推断写成确定事实。
不得新增支撑位、阻力位、资金流向、市场主导因素、
未来目标价或买卖行动建议。
对于缺少充分数据支撑的结论，
必须保留“可能”“当前数据不足以确认”“需进一步验证”等限定。
"""

SUPERVISOR_PROMPT = """
你是一个 Multi-Agent 加密市场分析系统中的 Supervisor（总调度器）。

你的唯一职责是：根据当前任务状态，选择下一步应该执行的 Agent。

你不负责：
- 查询市场数据；
- 调用任何工具；
- 直接分析市场；
- 生成面向用户的最终报告；
- 编造或补充任何未提供的数据。

你只能从以下三个路由目标中选择一个：
1. researcher：缺少回答问题所需的市场事实或研究资料。
2. analyst：已有足够事实或研究资料，但尚未形成分析结果。
3. reporter：已有分析结果，或问题只需要直接整理已有事实。

路由规则：
- market_data 为空，且问题需要实时价格、涨跌幅、市值、市场总览等事实时，选择 researcher。
- research_notes 为空不代表 market_data 缺失。
- 已有相关事实但 analysis_result 为空时，简单事实查询可直接选择 reporter；
  涉及“分析、原因、风险、市场情况、对比、判断”等综合任务时选择 analyst。
- analysis_result 已存在且 final_report 为空时，选择 reporter。
- errors 表示工具多次失败时，不要无限重复选择 researcher；应基于已有信息选择 analyst 或 reporter。
- 只能基于 State 判断，不允许主观猜测。
- 不要输出 Markdown、代码块、额外解释或其他字段。

请严格只输出 JSON：
{
  "next_agent": "researcher | analyst | reporter",
  "route_reason": "一句基于当前 State 的中文理由"
}
"""


def clean_think(content):
    if not isinstance(content, str):
        return content

    if "</think>" in content:
        return content.split("</think>", 1)[-1].strip()

    return content.strip()


def strip_json_fence(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def create_llm() -> ChatOpenAI:
    base_url = (os.getenv("LLM_BASE_URL") or "").replace("/chat/completions", "")
    api_key = os.getenv("LLM_API_KEY")

    if not base_url or not api_key:
        raise RuntimeError("缺少 LLM_BASE_URL 或 LLM_API_KEY")

    return ChatOpenAI(
        model="MiniMax-M2.7",
        base_url=base_url,
        api_key=api_key,
        temperature=0.7,
        max_tokens=1000,
    )


def initial_state(question: str) -> MultiAgentEvalState:
    return {
        "user_question": question,
        "market_data": {},
        "research_notes": [],
        "analysis_result": "",
        "final_report": "",
        "errors": [],
        "route_count": 0,
        "max_route_count": 5,
        "route_reason": "",
        "next_agent": "",
        "messages": [HumanMessage(content=question)],
    }


def build_worker_nodes(researcher_with_tools, analyst_llm, reporter_llm):
    def researcher_node(state: MultiAgentEvalState):
        response = researcher_with_tools.invoke(
            [
                SystemMessage(content=RESEARCHER_PROMPT),
                HumanMessage(content=state["user_question"]),
            ]
        )
        return {"messages": [response]}

    def research_finalize_node(state: MultiAgentEvalState):
        latest_tool_call_ids = set()

        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                latest_tool_call_ids = {
                    tool_call.get("id")
                    for tool_call in msg.tool_calls
                    if tool_call.get("id")
                }
                break

        current_tool_messages = [
            msg
            for msg in state["messages"]
            if isinstance(msg, ToolMessage)
            and msg.tool_call_id in latest_tool_call_ids
        ]

        market_data = dict(state["market_data"])
        research_notes = list(state["research_notes"])
        errors = list(state["errors"])

        market_tool_mapping = {
            "get_price": "price",
            "get_market": "market",
            "get_coin_detail": "coin_detail",
        }

        for tool_msg in current_tool_messages:
            try:
                parsed_content = json.loads(tool_msg.content)
            except (json.JSONDecodeError, TypeError) as exc:
                errors.append(
                    {
                        "tool_name": tool_msg.name,
                        "tool_call_id": tool_msg.tool_call_id,
                        "error_type": type(exc).__name__,
                        "raw_content": str(tool_msg.content)[:300],
                    }
                )
                continue

            if tool_msg.name in market_tool_mapping:
                market_data[market_tool_mapping[tool_msg.name]] = parsed_content
            elif tool_msg.name == "search_rag":
                research_notes.append(parsed_content)
            else:
                errors.append(
                    {
                        "tool_name": tool_msg.name,
                        "tool_call_id": tool_msg.tool_call_id,
                        "error_type": "UnsupportedToolResult",
                        "raw_content": str(tool_msg.content)[:300],
                    }
                )

        return {
            "market_data": market_data,
            "research_notes": research_notes,
            "errors": errors,
        }

    def analyst_node(state: MultiAgentEvalState):
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

        response = analyst_llm.invoke(
            [
                SystemMessage(content=ANALYST_PROMPT),
                HumanMessage(content=analyst_context),
            ]
        )

        return {
            "messages": [response],
            "analysis_result": clean_think(response.content),
        }

    def reporter_node(state: MultiAgentEvalState):
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

        response = reporter_llm.invoke(
            [
                SystemMessage(content=REPORTER_PROMPT),
                HumanMessage(content=reporter_context),
            ]
        )

        return {
            "messages": [response],
            "final_report": clean_think(response.content),
        }

    def route_after_researcher(state: MultiAgentEvalState) -> Literal["tool_node", "research_finalize_node"]:
        last_msg = state["messages"][-1]

        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            return "tool_node"

        return "research_finalize_node"

    return researcher_node, research_finalize_node, analyst_node, reporter_node, route_after_researcher


def build_fixed_flow_graph():
    researcher_llm = create_llm()
    analyst_llm = create_llm()
    reporter_llm = create_llm()

    researcher_with_tools = researcher_llm.bind_tools(TOOLS)

    (
        researcher_node,
        research_finalize_node,
        analyst_node,
        reporter_node,
        route_after_researcher,
    ) = build_worker_nodes(researcher_with_tools, analyst_llm, reporter_llm)

    builder = StateGraph(MultiAgentEvalState)
    builder.add_node("researcher_node", researcher_node)
    builder.add_node("tool_node", ToolNode(TOOLS))
    builder.add_node("research_finalize_node", research_finalize_node)
    builder.add_node("analyst_node", analyst_node)
    builder.add_node("reporter_node", reporter_node)

    builder.add_edge(START, "researcher_node")
    builder.add_conditional_edges(
        "researcher_node",
        route_after_researcher,
        {
            "tool_node": "tool_node",
            "research_finalize_node": "research_finalize_node",
        },
    )
    builder.add_edge("tool_node", "research_finalize_node")
    builder.add_edge("research_finalize_node", "analyst_node")
    builder.add_edge("analyst_node", "reporter_node")
    builder.add_edge("reporter_node", END)

    return builder.compile()


def build_supervisor_graph():
    supervisor_llm = create_llm()
    researcher_llm = create_llm()
    analyst_llm = create_llm()
    reporter_llm = create_llm()

    researcher_with_tools = researcher_llm.bind_tools(TOOLS)

    (
        researcher_node,
        research_finalize_node,
        analyst_node,
        reporter_node,
        route_after_researcher,
    ) = build_worker_nodes(researcher_with_tools, analyst_llm, reporter_llm)

    def supervisor_node(state: MultiAgentEvalState):
        def build_command(next_agent: str, route_reason: str, goto):
            return Command(
                update={
                    "next_agent": next_agent,
                    "route_reason": route_reason,
                    "route_count": state["route_count"] + 1,
                },
                goto=goto,
            )

        # 这两条属于 Python 硬规则，不交给 LLM 决定。
        if state["final_report"].strip():
            return build_command(
                next_agent="end",
                route_reason="最终报告已生成，任务结束。",
                goto=END,
            )

        if state["route_count"] >= state["max_route_count"]:
            return build_command(
                next_agent="reporter",
                route_reason="已达到最大路由次数，基于已有信息生成最终报告。",
                goto="reporter_node",
            )

        supervisor_context = f"""
用户问题：
{state["user_question"]}

市场事实：
{json.dumps(state["market_data"], ensure_ascii=False, indent=2)}

补充研究资料：
{json.dumps(state["research_notes"], ensure_ascii=False, indent=2)}

分析结果：
{json.dumps(state["analysis_result"], ensure_ascii=False, indent=2)}

最终报告：
{json.dumps(state["final_report"], ensure_ascii=False, indent=2)}

已路由次数：
{state["route_count"]}

最大允许路由次数：
{state["max_route_count"]}

工具或数据异常：
{json.dumps(state["errors"], ensure_ascii=False, indent=2)}
"""

        response = supervisor_llm.invoke(
            [
                SystemMessage(content=SUPERVISOR_PROMPT),
                HumanMessage(content=supervisor_context),
            ]
        )

        raw_content = strip_json_fence(clean_think(response.content))

        try:
            decision_data = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Supervisor JSON 解析失败，原始输出：{raw_content}"
            ) from exc

        decision = decision_data.get("next_agent")
        route_reason = decision_data.get("route_reason")

        allowed_decisions = {"researcher", "analyst", "reporter"}
        if decision not in allowed_decisions:
            raise ValueError(
                f"Supervisor 返回非法路由值：{decision}；原始输出：{raw_content}"
            )

        if not isinstance(route_reason, str) or not route_reason.strip():
            raise ValueError(
                f"Supervisor 未返回有效 route_reason；原始输出：{raw_content}"
            )

        route_to_node = {
            "researcher": "researcher_node",
            "analyst": "analyst_node",
            "reporter": "reporter_node",
        }

        return build_command(
            next_agent=decision,
            route_reason=route_reason.strip(),
            goto=route_to_node[decision],
        )

    builder = StateGraph(MultiAgentEvalState)
    builder.add_node("supervisor_node", supervisor_node)
    builder.add_node("researcher_node", researcher_node)
    builder.add_node("tool_node", ToolNode(TOOLS))
    builder.add_node("research_finalize_node", research_finalize_node)
    builder.add_node("analyst_node", analyst_node)
    builder.add_node("reporter_node", reporter_node)

    builder.add_edge(START, "supervisor_node")
    builder.add_conditional_edges(
        "researcher_node",
        route_after_researcher,
        {
            "tool_node": "tool_node",
            "research_finalize_node": "research_finalize_node",
        },
    )
    builder.add_edge("tool_node", "research_finalize_node")
    builder.add_edge("research_finalize_node", "supervisor_node")
    builder.add_edge("analyst_node", "supervisor_node")
    builder.add_edge("reporter_node", "supervisor_node")

    return builder.compile()


def extract_multi_agent_result(graph, question: str):
    tools_called = []
    tool_results = []
    node_path = []
    agent_path = []
    route_decisions = []
    final_answer = ""

    agent_node_map = {
        "researcher_node": "researcher",
        "analyst_node": "analyst",
        "reporter_node": "reporter",
    }

    try:
        for step in graph.stream(initial_state(question)):
            node_name, node_update = next(iter(step.items()))
            node_path.append(node_name)

            if node_name in agent_node_map:
                agent_path.append(agent_node_map[node_name])

            if node_name == "supervisor_node":
                route = node_update.get("next_agent")
                if route:
                    route_decisions.append(route)

            if node_name == "tool_node":
                for msg in node_update.get("messages", []):
                    if not isinstance(msg, ToolMessage):
                        continue

                    tools_called.append(msg.name)

                    try:
                        tool_results.append(json.loads(msg.content))
                    except (json.JSONDecodeError, TypeError):
                        tool_results.append({"raw": str(msg.content)})

            if node_name == "reporter_node":
                final_answer = node_update.get("final_report", "") or ""

        return {
            "final_answer": final_answer,
            "tools_called": tools_called,
            "total_steps": len(node_path),
            "tool_results": tool_results,
            "node_path": node_path,
            "agent_path": agent_path,
            "route_decisions": route_decisions,
        }

    except Exception as exc:
        return {
            "final_answer": f"[ERROR] {str(exc)}",
            "tools_called": tools_called,
            "total_steps": len(node_path),
            "tool_results": tool_results,
            "node_path": node_path,
            "agent_path": agent_path,
            "route_decisions": route_decisions,
        }


def run_fixed_flow_multi_agent_for_eval(question: str):
    graph = build_fixed_flow_graph()
    return extract_multi_agent_result(graph, question)


def run_supervisor_multi_agent_for_eval(question: str):
    graph = build_supervisor_graph()
    return extract_multi_agent_result(graph, question)


def safe_judge(question, agent_result, expected_answer_points):
    final_answer = agent_result.get("final_answer", "") or ""
    actual_tools = agent_result.get("tools_called", []) or []

    if "[ERROR]" in final_answer or "[FAILED]" in final_answer:
        return {
            "reasoning": "Agent 执行失败，跳过 LLM judge",
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
        }

    return judge_response(
        question=question,
        agent_output=final_answer,
        actual_tools=actual_tools,
        expected_answer_points=expected_answer_points,
    )


def clean_agent_result_for_report(agent_result: dict) -> dict:
    result = dict(agent_result)
    result["final_answer"] = clean_think(result.get("final_answer", "") or "")
    return result


def evaluate_routing(agent_result: dict, case: dict, agent_name: str) -> dict:
    """
    路由检查不并入 Week 10 的 overall_pass。

    原因：
    - 单 LangGraph 没有 researcher / analyst / reporter 角色路径。
    - 固定流程与 Supervisor 的设计目标不同。
    - Day 5 需要把“路由是否符合该架构自身预期”单独记录。
    """
    expectation = case.get("routing_expectations", {}).get(agent_name)

    if not expectation:
        return {
            "applicable": False,
            "overall_pass": True,
            "details": "该 Agent 没有配置路由期望，不适用。",
        }

    agent_path = agent_result.get("agent_path", []) or []
    route_decisions = agent_result.get("route_decisions", []) or []
    details = []

    required_agents = expectation.get("must_include_agents", [])
    missing_agents = [name for name in required_agents if name not in agent_path]
    must_include_agents_pass = not missing_agents

    if missing_agents:
        details.append(
            f"缺少预期业务角色：{missing_agents}，实际 agent_path：{agent_path}"
        )

    forbidden_agents = expectation.get("must_not_include_agents", [])
    unexpected_agents = [name for name in forbidden_agents if name in agent_path]
    must_not_include_agents_pass = not unexpected_agents

    if unexpected_agents:
        details.append(
            f"出现不应经过的业务角色：{unexpected_agents}，实际 agent_path：{agent_path}"
        )

    expected_routes = expectation.get("expected_route_decisions")
    if expected_routes is None:
        route_decisions_pass = True
    else:
        route_decisions_pass = route_decisions == expected_routes
        if not route_decisions_pass:
            details.append(
                f"路由决策不符合预期：期望 {expected_routes}，实际 {route_decisions}"
            )

    overall_pass = (
        must_include_agents_pass
        and must_not_include_agents_pass
        and route_decisions_pass
    )

    return {
        "applicable": True,
        "must_include_agents_pass": must_include_agents_pass,
        "must_not_include_agents_pass": must_not_include_agents_pass,
        "route_decisions_pass": route_decisions_pass,
        "overall_pass": overall_pass,
        "details": "; ".join(details) if details else "路由检查通过",
    }


AGENT_RUNNERS = {
    "langgraph_single_agent": run_langgraph_for_eval,
    "fixed_flow_multi_agent": run_fixed_flow_multi_agent_for_eval,
    "supervisor_multi_agent": run_supervisor_multi_agent_for_eval,
}


def load_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def append_jsonl(path: Path, record: dict):
    with open(path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def pause(seconds: int):
    if seconds > 0:
        time.sleep(seconds)


def main():
    cases = load_jsonl(EVAL_SET_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("", encoding="utf-8")

    records = []

    for case in cases:
        case_id = case["id"]
        question = case["question"]

        print(f"\n{'=' * 70}")
        print(f"[CASE {case_id}] {question}")

        for agent_name, runner in AGENT_RUNNERS.items():
            print(f"[CASE {case_id}] [{agent_name}] agent start")
            agent_result = runner(question)
            agent_result = clean_agent_result_for_report(agent_result)
            print(f"[CASE {case_id}] [{agent_name}] agent done")

            rule_result = evaluate_rules(agent_result, case)
            routing_result = evaluate_routing(agent_result, case, agent_name)

            pause(RUN_PAUSE_SECONDS)

            print(f"[CASE {case_id}] [{agent_name}] judge start")
            judge_result = safe_judge(
                question=question,
                agent_result=agent_result,
                expected_answer_points=case["expected_answer_points"],
            )
            print(f"[CASE {case_id}] [{agent_name}] judge done")

            record = {
                "case_id": case_id,
                "question": question,
                "capability": case.get("capability"),
                "sub_type": case.get("sub_type"),
                "agent": agent_name,
                "agent_result": agent_result,
                "judge_result": judge_result,
                "rule_result": rule_result,
                "routing_result": routing_result,
            }

            append_jsonl(OUTPUT_PATH, record)
            records.append(record)

            print(
                f"[CASE {case_id}] [{agent_name}] "
                f"rule_pass={rule_result['overall_pass']} | "
                f"routing_pass={routing_result['overall_pass']} | "
                f"tools={agent_result['tools_called']} | "
                f"agent_path={agent_result.get('agent_path', [])}"
            )

            pause(JUDGE_PAUSE_SECONDS)

    print("\n=== Multi-Agent Eval Done ===")
    print(f"records: {len(records)}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
