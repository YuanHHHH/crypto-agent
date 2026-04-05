from src.tools.llm_client import llm_client
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tool_registry import ToolRegistry
from src.tools.price import get_crypto_price
from src.tools.market import get_market_overview,get_coin_market
import json

class AgentRunner:
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.tool_registry.register("get_price", get_crypto_price, "获得指定代币的价格数据",
                               {"symbol": "要查询的代币，如 bitcoin、ethereum"})
        self.tool_registry.register("get_market", get_market_overview, "获得整个市场的相关重要数据", {})
        self.tool_registry.register("get_coin_detail", get_coin_market, "获得指定代币的相关market数",
                               {"coin_id": "要查询的代币，如 bitcoin、ethereum"})

    def run(self,user_question):
        tools_description = self.tool_registry.get_tool_descriptions()
        agent_system_prompt = SYSTEM_PROMPT.format(tool_descriptions=tools_description)
        conversation = "用户问题：" + user_question
        max_steps = 5
        while max_steps > 0:
            client_response = llm_client(conversation,system_prompt=agent_system_prompt)
            print(client_response)
            if "Action" in client_response:
                info_part = client_response.split("Action:",1)[1]
                function_name = info_part.split("Action Input:", 1)[0].strip()
                params = client_response.split("Action Input:", 1)[1].strip()
                params_str = json.loads(params)
                res = self.tool_registry.call(function_name,**params_str)

                observation = f"\nObservation: {json.dumps(res)}\n"
                conversation = conversation + "\n" + client_response + observation

            elif "Final Answer" in client_response:
                final_answer = client_response.split("Final Answer:", 1)[1].strip()
                print(final_answer)
                return final_answer
            else:
                raise Exception
            max_steps = max_steps - 1

if __name__ == "__main__":
    agent_runner = AgentRunner()
    agent_runner.run("请你给我查询bitcoin的价格")


