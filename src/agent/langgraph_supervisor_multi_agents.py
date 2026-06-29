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
import uuid
from dotenv import load_dotenv
load_dotenv()

mm_BASE_URL = os.getenv("LLM_BASE_URL")
mm_API_KEY = os.getenv("LLM_API_KEY")
base_url = mm_BASE_URL.replace("/chat/completions", "")

supervisor = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)

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
    route_count:int
    max_route_count:int
    route_reason: str
    next_agent:str
    messages:Annotated[list[BaseMessage],add_messages]

def clean_think(content):
    if not isinstance(content, str):
        return content

    if "</think>" in content:
        return content.split("</think>", 1)[-1].strip()

    return content.strip()

def supervisor_node(state:Agent_State):
    sup_prompt = """
    你是一个 Multi-Agent 加密市场分析系统中的 Supervisor（总调度器）。

你的唯一职责是：根据当前任务状态，选择下一步应该执行的 Agent。

你不负责：

* 查询市场数据；
* 调用任何工具；
* 直接分析市场；
* 生成面向用户的最终报告；
* 编造或补充任何未提供的数据。

你只能从以下三个路由目标中选择一个：

1. researcher
   适用场景：当前缺少回答用户问题所必需的事实数据、市场数据或补充研究资料，需要先由 Researcher 获取信息。

2. analyst
   适用场景：已经具备足够的事实数据或研究资料，但尚未形成分析结果，需要由 Analyst 对事实、推断、风险和信息缺口进行分析。

3. reporter
   适用场景：已经有分析结果，需要由 Reporter 将事实、分析推断、风险和信息缺口组织成最终回答。
   由 Reporter 基于已有信息生成一份明确说明数据不足或存在异常的最终报告。


你必须严格遵循以下路由原则：

* 优先检查 final_report：

* 再检查 route_count：

  * 若 route_count 已达到或超过 max_route_count，且 final_report 为空，选择 reporter。
  * 不要在达到最大轮数后继续选择 researcher 或 analyst。

* 再检查市场事实与研究资料：

  * 若 market_data 为空，且用户问题需要实时市场数据、币种价格、涨跌幅、市值、市场总览等事实信息，选择 researcher。
  * 若 research_notes 为空并不代表 market_data 缺失。
  * 只有 market_data 与当前问题真正相关的必要字段都缺失时，才能说“数据不足”。
  * 不要因为某个非关键字段缺失，就无限重复派发 researcher。
  * 若 errors 表明某个工具已经多次失败，不要无条件重复派发 researcher；应基于已有信息选择 analyst 或 reporter，并在 routing_reason 中说明限制。

* 再检查分析结果：

  * 若已有足够 market_data 或 research_notes，但 analysis_result 为空，选择 analyst。
  * 若 analysis_result 已存在但 final_report 为空，选择 reporter。

* 你必须基于 State 中的字段做判断，不要根据主观猜测决定路由。

* 不要输出“Researcher Agent”“去分析”“需要更多信息”等自由文本作为路由目标。

* 不要选择不在允许集合中的目标。

* 不要输出 Markdown、解释文字、代码块或额外字段。

请严格只输出以下 JSON：

{
"next_agent": "researcher | analyst | reporter",
"route_reason": "一句简短、基于当前 State 的中文理由"
}
    """
    supervisor_context = f"""
        用户问题：
        {state["user_question"]}

        市场事实：
        {json.dumps(state["market_data"], ensure_ascii=False, indent=2)}

        补充研究资料：
        {json.dumps(state["research_notes"], ensure_ascii=False, indent=2)}

        分析结果:
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

    input_supervisor = [
        SystemMessage(content=sup_prompt),
        HumanMessage(content=supervisor_context),
    ]

    if state["final_report"].strip():
        return Command(
            update={
                "next_agent": "end",
                "route_reason": "最终报告已生成，任务结束。",
                "route_count": state["route_count"] + 1,
            },
            goto=END,
        )

    if state["route_count"] >= state["max_route_count"]:
        return Command(
            update={
                "next_agent": "reporter",
                "route_reason": "已达到最大路由次数，基于已有信息生成最终报告。",
                "route_count": state["route_count"] + 1,
            },
            goto="reporter_node",
        )

    response = supervisor.invoke(input_supervisor)
    raw_content = clean_think(response.content)

    if raw_content.startswith("```json"):
        raw_content = raw_content[len("```json"):].strip()
    elif raw_content.startswith("```"):
        raw_content = raw_content[len("```"):].strip()

    if raw_content.endswith("```"):
        raw_content = raw_content[:-3].strip()

    try:
        clean_content = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Supervisor JSON 解析失败，原始输出：{raw_content}"
        ) from e
    decision = clean_content["next_agent"]
    route_reason = clean_content["route_reason"]
    route_count = state["route_count"]

    allowed_decisions = {"researcher", "analyst", "reporter"}
    if decision not in allowed_decisions:
        raise ValueError(
            f"Supervisor 返回非法路由值：{decision}；"
            f"原始输出：{raw_content}"
        )
    if not isinstance(route_reason, str) or not route_reason.strip():
        raise ValueError(
            f"Supervisor 未返回有效 route_reason；"
            f"原始输出：{raw_content}"
        )

    if decision == "researcher":
        return Command(
            update={
                "next_agent": decision,
                "route_reason": route_reason,
                "route_count": route_count+1
            },
            goto="researcher_node",
        )
    if decision == "analyst":
        return Command(
            update={
                "next_agent": decision,
                "route_reason": route_reason,
                "route_count": route_count+1
            },
            goto="analyst_node",
        )
    if decision == "reporter":
        return Command(
            update={
                "next_agent": decision,
                "route_reason": route_reason,
                "route_count": route_count+1
            },
            goto="reporter_node",
        )


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

不得从单一时点价格、24小时涨跌幅、24小时高低点或全市场概览，
推导出明确的支撑位、阻力位、趋势反转、长期趋势、资金流向、
主力行为、下跌原因或未来价格目标。

若仅有24小时数据，只能描述“过去24小时的价格变化”和
“BTC与全市场是否同向变化”。

涉及支撑、阻力、趋势、资金流向、原因、未来走势时，
必须明确写“当前数据不足以确认”或“需要历史K线、链上数据、
成交量变化或资金流数据进一步验证”。
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
不得把 Analyst 的推断写成确定事实。

不得新增支撑位、阻力位、资金流向、市场主导因素、
未来目标价或买卖行动建议。

对于缺少充分数据支撑的结论，
必须保留“可能”“当前数据不足以确认”“需进一步验证”等限定。
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

builder.add_node("supervisor_node",supervisor_node)
builder.add_node("researcher_node",researcher_node)
builder.add_node("tool_node",tool_node)

builder.add_node("research_finalize_node",research_finalize_node)
builder.add_node("analyst_node",analyst_node)
builder.add_node("reporter_node",reporter_node)

builder.add_edge(START,"supervisor_node")

builder.add_conditional_edges(
    "researcher_node",
    route_after_researcher,
    {
        "tool_node": "tool_node",
        "research_finalize_node": "research_finalize_node",
    }
)
builder.add_edge("tool_node","research_finalize_node")

builder.add_edge("research_finalize_node","supervisor_node")
builder.add_edge("analyst_node","supervisor_node")
builder.add_edge("reporter_node","supervisor_node")

checkpoint = InMemorySaver()

task_config = {
    "configurable": {
        "thread_id": f"task-{uuid.uuid4()}"
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
        "market_data": {},
        "research_notes": [],
        "analysis_result": "",
        "final_report": "",
        "errors": [],
        "route_count": 0,
        "max_route_count": 5,
        "route_reason": "",
        "next_agent": "",
        "messages": [HumanMessage(content=user_input)],
    }

    for step in graph.stream(
        input_msgs,
        config=task_config
    ):
        print(step)
        print("---")
        record_step(step)



