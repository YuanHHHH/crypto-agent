import json

from src.agent.agent_runner import AgentRunner
from src.agent.prompts import SYSTEM_PROMPT
from src.tools.llm_client import llm_client


def build_history_text(chat_history):
    history_text = ""
    for turn in chat_history:
        history_text += f"之前的问题：{turn['user_question']}\n之前的回答：{turn['final_answer']}\n\n"
    return history_text


def main():
    agent = AgentRunner()

    print("========== 第一步：完整跑第一轮 ==========")
    first_answer = agent.run("请给我查ETH价格")
    print("第一轮最终答案：", first_answer)

    print("\n========== 当前 chat_history ==========")
    print(json.dumps(agent.chat_history, ensure_ascii=False, indent=2))

    tools_description = agent.tool_registry.get_tool_descriptions()
    agent_system_prompt = SYSTEM_PROMPT.format(tool_descriptions=tools_description)

    print("\n========== 第二步：构造第二轮第一次 LLM 调用的 conversation ==========")
    second_question = "那SOL呢"
    history_text = build_history_text(agent.chat_history)
    conversation = history_text + "用户问题：" + second_question

    print("----- 第二轮第一次请求的 conversation START -----")
    print(conversation)
    print("----- 第二轮第一次请求的 conversation END -----")
    print("长度 =", len(conversation))

    print("\n========== 第三步：第二轮第一次调用 LLM ==========")
    first_llm_response = llm_client(conversation, system_prompt=agent_system_prompt)
    print(first_llm_response)

    print("\n========== 第四步：解析 Action 并调用工具 ==========")
    info_part = first_llm_response.split("Action:", 1)[1]
    function_name = info_part.split("Action Input:", 1)[0].strip()
    params_text = first_llm_response.split("Action Input:", 1)[1].strip()
    params_first_line = params_text.split("\n")[0].strip()
    params_dict = json.loads(params_first_line)

    print("工具名 =", function_name)
    print("参数 =", params_dict)

    tool_result = agent.tool_registry.call(function_name, **params_dict)
    print("工具结果 =", tool_result)

    print("\n========== 第五步：构造第二轮第二次 LLM 调用的 conversation ==========")
    observation = f"\nObservation: {json.dumps(tool_result)}\n"
    conversation_after_observation = conversation + "\n" + first_llm_response + observation

    print("----- 第二轮第二次请求的 conversation START -----")
    print(conversation_after_observation)
    print("----- 第二轮第二次请求的 conversation END -----")
    print("长度 =", len(conversation_after_observation))

    print("\n========== 第六步：第二轮第二次调用 LLM ==========")
    try:
        second_llm_response = llm_client(conversation_after_observation, system_prompt=agent_system_prompt)
        print("\n===== 第二轮第二次调用成功 =====")
        print(second_llm_response)
    except Exception as e:
        print("\n===== 第二轮第二次调用失败 =====")
        print(repr(e))


if __name__ == "__main__":
    main()