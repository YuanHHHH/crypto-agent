from src.agent.langchain_tools import get_coin_detail,analyze_coin,get_price,get_market
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import *
from langchain import hub

from dotenv import load_dotenv
import os
load_dotenv()

mm_BASE_URL = os.getenv("LLM_BASE_URL")
mm_API_KEY = os.getenv("LLM_API_KEY")
base_url = mm_BASE_URL.replace("/chat/completions", "")

llm_model = ChatOpenAI(
    model="MiniMax-M2.7",
    base_url=base_url,
    api_key=mm_API_KEY,
    temperature=0.7,
    max_tokens=1000
)

prompt = hub.pull("hwchase17/react")

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
)

result = executor.invoke({"input": "请你给我查 BTC 价格"})
print(result["output"])