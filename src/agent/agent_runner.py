from src.agent.parser import parse_llm_output
from src.tools.llm_client import llm_client
from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tool_registry import ToolRegistry
from src.tools.price import get_crypto_price
from src.tools.market import get_market_overview,get_coin_market
from src.tools.analyzer import analyze_coin
import json
from src.agent.trace import trace_record
import time

class AgentRunner:
    def __init__(self):
        self.chat_history = []
        self.tool_registry = ToolRegistry()
        self.tool_registry.register("get_price", get_crypto_price, "获得指定代币的价格数据",
                               {"symbol": "要查询的代币，如 bitcoin、ethereum"})
        self.tool_registry.register("get_market", get_market_overview, "获得整个市场的相关重要数据", {})
        self.tool_registry.register("get_coin_detail", get_coin_market, "获得指定代币的相关market数",
                               {"coin_id": "要查询的代币，如 bitcoin、ethereum"})
        self.tool_registry.register("analyze_coin",analyze_coin,"对指定币种进行深度行情分析",
                                    {"symbol":"要查询的代币"})

    def reset(self):
        self.chat_history = []


    def run(self,user_question):
        tools_description = self.tool_registry.get_tool_descriptions()
        agent_system_prompt = SYSTEM_PROMPT.format(tool_descriptions=tools_description)

        history_text = ""
        for turn in self.chat_history:
            history_text += f"之前的问题：{turn['user_question']}\n之前的回答：{turn['final_answer']}\n\n"

        conversation = history_text + "用户问题：" + user_question
        final_answer = None
        step_log = []

        max_steps = 5
        steps = 0
        start_time = time.time()
        end_type = "max_steps"
        tool_call_count = 0
        parse_error_count = 0
        while max_steps > steps:
            client_response = llm_client(conversation,system_prompt=agent_system_prompt)
            print(client_response)
            response_parsed = parse_llm_output(client_response)
            if response_parsed.get("type") == "action":
                function_name = response_parsed["function_name"]
                if function_name not in self.tool_registry.tools:
                    conversation += f"\n{client_response}\nObservation: tools中无{function_name}工具，请检查\n"
                    steps +=1
                    continue
                res = self.tool_registry.call(function_name,**response_parsed["action_input"])
                observation = f"\nObservation: {json.dumps(res)}\n"
                tool_call_count += 1
                conversation = conversation + "\n" + client_response + observation
                step_log.append(
                    {
                        "step": len(step_log) + 1,
                        "type":response_parsed.get("type"),
                        "thought":response_parsed.get("thought", ""),
                        "action":function_name,
                        "action_input":response_parsed["action_input"],
                        "observation":observation,
                    }
                )


            elif response_parsed.get("type") =="final_answer":
                end_type = "final_answer"
                final_answer = response_parsed["final_answer"]
                print(final_answer)
                steps += 1
                step_log.append(
                    {
                        "step": len(step_log) + 1,
                        "type":response_parsed.get("type"),
                        "thought":response_parsed.get("thought", ""),
                        "final_answer":final_answer,
                    }
                )
                break
            elif response_parsed.get("type") =="no_parsed":
                #兜底
                end_type = "no_parsed"
                raw_text = f"返回的格式无法解析，现在直接回复raw_text：{response_parsed['raw_text']}"
                print(raw_text)
                steps += 1
                step_log.append(
                    {
                        "step": len(step_log) + 1,
                        "type":response_parsed.get("type"),
                        "thought":response_parsed.get("thought", ""),
                        "raw_text":raw_text,
                    }
                )
                break
            elif response_parsed.get("type") =="error":
                end_type = "error"
                parse_error_count += 1
                error_notice = response_parsed["error_notice"]
                conversation = f"{conversation}\n{client_response}\nObservation: {error_notice}，请重新按格式输出\n"
                steps +=1
                step_log.append(
                    {
                        "step": len(step_log) + 1,
                        "type":response_parsed.get("type"),
                        "thought":response_parsed.get("thought", ""),
                        "observation":error_notice,
                    }
                )
                continue

            steps = steps + 1

        end_time= time.time()
        record={
            "user_question": user_question,
            "final_answer": final_answer,
            "full_conversation": conversation,
            "total_steps": steps,
            "total_time": end_time - start_time,
            "end_reason": end_type,
            "tool_call_count": tool_call_count,
            "parse_error_count": parse_error_count,
        }
        trace_record(record)
        self.chat_history.append({"user_question":user_question,"final_answer":final_answer})
        return (final_answer,step_log)

if __name__ == "__main__":
    agent_runner = AgentRunner()
    agent_runner.run("帮我分析一下 ETH 的行情")


