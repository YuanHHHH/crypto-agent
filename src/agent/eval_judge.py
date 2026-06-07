# import os
# import requests
# from openai import OpenAI
# from dotenv import load_dotenv
# load_dotenv()
#
# api_key=os.getenv("KIMI_API_KEY")
# base_url=os.getenv("KIMI_BASE_URL")
# system_prompt = """
# 你是一个 AI Agent 质量评估裁判。你的任务是评估一个加密货币分析 Agent 的回答质量。
#
# 你会收到以下信息：
# 1. 用户问题
# 2. Agent 的实际回答
# 3. 期望的关键点列表（Agent 的回答应该覆盖这些点）
# 4. Agent 实际调用的工具列表
#
# 请从三个维度评估，每个维度 0-10 分：
#
# 【accuracy（准确性）】Agent 回答的内容是否正确，是否基于真实数据
# - 10 分：所有信息准确，明确基于工具返回的真实数据回答
# - 7 分：大部分准确，有少量不精确的表述但不影响结论
# - 4 分：部分信息可能是编造的，或者数据明显不合理
# - 0 分：完全编造数据，或者给出严重错误的信息
#
# 【completeness（完整性）】Agent 是否覆盖了期望关键点列表中的所有要点
# - 10 分：覆盖所有关键点，回答全面
# - 7 分：覆盖大部分关键点，缺少 1 个次要点
# - 4 分：只覆盖了一半左右的关键点
# - 0 分：没有覆盖任何关键点，答非所问
#
# 【relevance（相关性）】Agent 的回答是否切题，有没有跑偏或加入无关内容
# - 10 分：完全切题，所有内容都和用户问题直接相关
# - 7 分：基本切题，有少量无关但不干扰的内容
# - 4 分：部分跑偏，混入了较多与问题无关的内容
# - 0 分：完全跑题，回答和问题没有关系
#
# 评估规则：
# 1. 你必须先写 reasoning（你的完整判断过程），然后再给出三个维度的分数
# 2. reasoning 中要明确说明 Agent 覆盖了哪些关键点、遗漏了哪些、有没有编造内容
# 3. 你无法验证实时数据的准确性（比如你不知道 BTC 当前真实价格），所以 accuracy 主要看 Agent 是否调用了工具获取数据，而不是验证具体数字
# 4. 输出必须是严格的 JSON 格式，不要包含 markdown 代码块或其他任何内容
#
# 输出格式：
# {"reasoning": "你的判断过程", "accuracy": 分数, "completeness": 分数, "relevance": 分数}
#
# 下面是两个评估示例：
#
# 示例一（高分案例）：
#
# 用户问题：BTC 现在多少钱？
# Agent 回答：BTC 当前价格为 $78,054，24小时涨跌幅为 -0.40%，价格小幅下跌。
# 期望关键点：["BTC 当前价格", "24h 涨跌幅"]
# Agent 调用的工具：["get_price"]
#
# 评估输出：
# {"reasoning": "Agent 调用了 get_price 工具获取真实数据，回答中包含了 BTC 当前价格（$78,054）和 24h 涨跌幅（-0.40%），完全覆盖了两个期望关键点。回答简洁切题，没有无关内容。数据来自工具返回，不是编造的。", "accuracy": 9, "completeness": 10, "relevance": 10}
#
# 示例二（低分案例）：
#
# 用户问题：BTC 现在多少钱？
# Agent 回答：比特币是一种去中心化的数字货币，由中本聪在 2009 年创建。它使用区块链技术来记录交易。目前加密货币市场波动较大，建议谨慎投资。
# 期望关键点：["BTC 当前价格", "24h 涨跌幅"]
# Agent 调用的工具：[]
#
# 评估输出：
# {"reasoning": "Agent 没有调用任何工具获取实时价格数据，而是回答了 BTC 的背景知识。用户问的是当前价格，Agent 完全没有提供价格和涨跌幅信息，两个期望关键点都未覆盖。回答内容虽然和 BTC 相关，但与用户的具体问题（价格查询）不匹配，属于跑偏。", "accuracy": 2, "completeness": 0, "relevance": 3}
#
# """
# headers = {
#         "Authorization": "Bearer " + api_key,
#         "Content-Type": "application/json",
#     }
#
#
#
# def judge_response(question, agent_output, required_tools,expected_answer_points):
#     data = {
#         "model": "kimi-k2.6",
#         "messages": [
#             {"role": "system", "content": system_prompt},
#             {
#                 "role": "user",
#                 "content": f"""用户问题：{question}
#                             Agent 回答：{agent_output}
#                             期望关键点：{expected_answer_points}
#                             Agent 调用的工具：{required_tools}"""
#             }
#         ]
#     }
#     try:
#         response = requests.post(url=base_url, headers=headers, json=data)
#         print(response.json())
#     except Exception as e:
#         print(e)
#         return
#     return response.json()
#
# def evaluate_rules(agent_run_result, rule_checks):
#     steps = agent_run_result["max_steps"]
#     call_tool = agent_run_result["must_call_tool"]
#     required_response_fields = agent_run_result["required_response_fields"]
#     res = False
#     if steps < rule_checks["max_steps"]:
#         res = True
#     if call_tool == rule_checks["must_call_tool"]:
#         res = True
#     if required_response_fields == rule_checks["required_response_fields"]:
#         res = True
#     return res

"""
LLM-as-judge 评分模块
用 GPT / Kimi 等外部模型对 Agent 输出做三维度语义评分
"""

import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

JUDGE_API_KEY = os.getenv("KIMI_API_KEY")
JUDGE_BASE_URL = os.getenv("KIMI_BASE_URL")
JUDGE_MODEL = "kimi-k2.6"

SYSTEM_PROMPT = """你是一个 AI Agent 质量评估裁判。你的任务是评估一个加密货币分析 Agent 的回答质量。

你会收到以下信息：
1. 用户问题
2. Agent 的实际回答
3. 期望的关键点列表（Agent 的回答应该覆盖这些点）
4. Agent 实际调用的工具列表

请从三个维度评估，每个维度 0-10 分：

【accuracy（准确性）】Agent 回答的内容是否正确，是否基于真实数据
- 10 分：所有信息准确，明确基于工具返回的真实数据回答
- 7 分：大部分准确，有少量不精确的表述但不影响结论
- 4 分：部分信息可能是编造的，或者数据明显不合理
- 0 分：完全编造数据，或者给出严重错误的信息

【completeness（完整性）】Agent 是否覆盖了期望关键点列表中的所有要点
- 10 分：覆盖所有关键点，回答全面
- 7 分：覆盖大部分关键点，缺少 1 个次要点
- 4 分：只覆盖了一半左右的关键点
- 0 分：没有覆盖任何关键点，答非所问

【relevance（相关性）】Agent 的回答是否切题，有没有跑偏或加入无关内容
- 10 分：完全切题，所有内容都和用户问题直接相关
- 7 分：基本切题，有少量无关但不干扰的内容
- 4 分：部分跑偏，混入了较多与问题无关的内容
- 0 分：完全跑题，回答和问题没有关系

评估规则：
1. 你必须先写 reasoning（你的完整判断过程），然后再给出三个维度的分数
2. reasoning 中要明确说明 Agent 覆盖了哪些关键点、遗漏了哪些、有没有编造内容
3. 你无法验证实时数据的准确性（比如你不知道 BTC 当前真实价格），所以 accuracy 主要看 Agent 是否调用了工具获取数据，而不是验证具体数字
4. 输出必须是严格的 JSON 格式，不要包含 markdown 代码块或其他任何内容

输出格式：
{"reasoning": "你的判断过程", "accuracy": 分数, "completeness": 分数, "relevance": 分数}

下面是两个评估示例：

示例一（高分案例）：

用户问题：BTC 现在多少钱？
Agent 回答：BTC 当前价格为 $78,054，24小时涨跌幅为 -0.40%，价格小幅下跌。
期望关键点：["BTC 当前价格", "24h 涨跌幅"]
Agent 调用的工具：["get_price"]

评估输出：
{"reasoning": "Agent 调用了 get_price 工具获取真实数据，回答中包含了 BTC 当前价格（$78,054）和 24h 涨跌幅（-0.40%），完全覆盖了两个期望关键点。回答简洁切题，没有无关内容。数据来自工具返回，不是编造的。", "accuracy": 9, "completeness": 10, "relevance": 10}

示例二（低分案例）：

用户问题：BTC 现在多少钱？
Agent 回答：比特币是一种去中心化的数字货币，由中本聪在 2009 年创建。它使用区块链技术来记录交易。目前加密货币市场波动较大，建议谨慎投资。
期望关键点：["BTC 当前价格", "24h 涨跌幅"]
Agent 调用的工具：[]

评估输出：
{"reasoning": "Agent 没有调用任何工具获取实时价格数据，而是回答了 BTC 的背景知识。用户问的是当前价格，Agent 完全没有提供价格和涨跌幅信息，两个期望关键点都未覆盖。回答内容虽然和 BTC 相关，但与用户的具体问题（价格查询）不匹配，属于跑偏。", "accuracy": 2, "completeness": 0, "relevance": 3}
"""


def judge_response(question, agent_output, actual_tools, expected_answer_points):
    """
    调用 judge 模型对 Agent 输出做三维度评分

    参数：
        question: 用户问题
        agent_output: Agent 最终回答文本
        actual_tools: Agent 实际调用的工具列表，如 ["get_price"]
        expected_answer_points: 期望关键点列表，如 ["BTC 价格", "24h 涨跌"]

    返回：
        {"reasoning": "...", "accuracy": 8, "completeness": 9, "relevance": 10}
        失败时返回 {"reasoning": "judge 调用失败", "accuracy": 0, "completeness": 0, "relevance": 0}
    """
    if not JUDGE_API_KEY or not JUDGE_BASE_URL:
        return {
            "reasoning": "judge API 未配置：请检查 KIMI_API_KEY 和 KIMI_BASE_URL",
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
        }

    user_message = f"""用户问题：{question}
Agent 回答：{agent_output}
期望关键点：{json.dumps(expected_answer_points, ensure_ascii=False)}
Agent 调用的工具：{json.dumps(actual_tools, ensure_ascii=False)}"""

    headers = {
        "Authorization": "Bearer " + JUDGE_API_KEY,
        "Content-Type": "application/json",
    }

    data = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        "thinking": {
            "type": "disabled"
        },
        "response_format": {
            "type": "json_object"
        },
        "max_completion_tokens": 512
    }

    try:
        response = requests.post(url=JUDGE_BASE_URL, headers=headers, json=data, timeout=90)
        result = response.json()

        if "choices" not in result:
            print("[JUDGE RAW RESPONSE]", result)
            return {
                "reasoning": f"judge 返回异常结构: {result}",
                "accuracy": 0,
                "completeness": 0,
                "relevance": 0,
            }

        # 从返回结果里提取 content
        content = result["choices"][0]["message"]["content"]

        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        parsed = json.loads(content)
        return {
            "reasoning": parsed.get("reasoning", ""),
            "accuracy": parsed.get("accuracy", 0),
            "completeness": parsed.get("completeness", 0),
            "relevance": parsed.get("relevance", 0),
        }

    except Exception as e:
        print(f"[JUDGE ERROR] {e}")
        return {
            "reasoning": f"judge 调用失败: {str(e)}",
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
        }