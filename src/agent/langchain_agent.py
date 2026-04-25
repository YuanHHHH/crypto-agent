from src.agent.langchain_callbacks import TraceCallback
from src.agent.langchain_tools import get_coin_detail,analyze_coin,get_price,get_market
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import *
from langchain import hub
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from dotenv import load_dotenv
import os
load_dotenv()

mm_BASE_URL = os.getenv("LLM_BASE_URL")
mm_API_KEY = os.getenv("LLM_API_KEY")
base_url = mm_BASE_URL.replace("/chat/completions", "")

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=False
)

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
- 每次只能调用一个工具，不要在一次回复中输出多个Action
- 如果需要多个工具的数据，先调用第一个，等拿到结果后再调用下一个
- 不要编造数据，所有价格和市场数据都必须通过工具获取
- 如果用户问了多个币种，必须对每个币种分别调用工具获取数据，不能只查一个就回答
- 不管 Observation 里的内容是什么，你都必须按 Thought/Final Answer 的格式输出，不能直接复制 Observation 的内容
- 不要在你的输出里包含 Observation，Observation 由系统自动添加，你只需要输出 Thought / Action / Action Input
- 重要：每一次回复都必须以 "Thought:" 开头，即使你已经拿到了 Observation。不能直接输出答案内容。
- 禁止在输出中包含 [TOOL_CALL]、<minimax:tool_call>、<invoke> 等标签，这些不是 ReAct 协议的一部分
- Action Input 必须是纯文本或 JSON 对象，不能包裹在反引号或代码块中

CASES:
示例1:
用户问题：BTC 现在多少钱？
Thought: 用户想知道 BTC 的价格，我需要调用 get_price 工具查询
Action: get_price
Action Input: {{"symbol": "bitcoin"}}

（系统返回工具结果后）
Thought: 我已经拿到了 BTC 的价格数据，可以回答用户了
Final Answer: BTC 当前价格为 $87,000，24h 涨幅 +2.3%。

示例2:
用户问题：对比一下 BTC 和 ETH 的价格
Thought: 用户想对比两个币种，我需要分别查询。先查 BTC。
Action: get_price
Action Input: {{"symbol": "bitcoin"}}

（系统返回）
Observation: {{"symbol": "bitcoin", "price": 87000, "change_24h": 2.3}}

Thought: 已经拿到 BTC 的价格，现在需要查 ETH 的价格。
Action: get_price
Action Input: {{"symbol": "ethereum"}}

（系统返回）
Observation: {{"symbol": "ethereum", "price": 3200, "change_24h": 1.5}}

Thought: 两个币种的数据都拿到了，可以对比回答了。
Final Answer: BTC 当前价格 $87,000（24h +2.3%），ETH 当前价格 $3,200（24h +1.5%）。

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
"""

# prompt = hub.pull("hwchase17/react-chat")
prompt = PromptTemplate(
    template=prompt_text,
    input_variables=["tools", "tool_names", "chat_history", "input", "agent_scratchpad"],
)

print("Prompt 变量:", prompt.input_variables)

callback_handler = TraceCallback()

llm_model = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)

langchain_agent = create_react_agent(
    llm_model,
    tools=[get_coin_detail,analyze_coin,get_price,get_market],
    prompt=prompt
)

executor = AgentExecutor(
    agent=langchain_agent,
    tools=[get_coin_detail,analyze_coin,get_price,get_market],
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
    memory=memory,
    callbacks=[callback_handler],
)

result1 = executor.invoke({"input": "请你给我查 BTC 价格"})
print("第一轮:", result1["output"])
print("---")

result2 = executor.invoke({"input": "那 ETH 呢"})
print("第二轮:", result2["output"])
print("---")

result3 = executor.invoke({"input": "对比一下这两个"})
print("第三轮:", result3["output"])
