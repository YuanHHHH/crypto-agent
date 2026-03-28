import os
import requests
from dotenv import load_dotenv

load_dotenv()

def llm_client(prompt):
    mm_BASE_URL = os.getenv("LLM_BASE_URL")
    mm_API_KEY = os.getenv("LLM_API_KEY")
    headers = {
        "Authorization": "Bearer " + mm_API_KEY,
        "Content-Type": "application/json",
    }

    data = {
        "model": "MiniMax-M2.7",
        "messages": [
            {"role": "system",
             "content": """你是一个专业的加密货币数据分析师。请严格按照以下结构输出分析报告：

1. 行情快照：当前价格、24h涨跌幅、24h最高/最低价、成交量
2. 趋势判断：基于价格变动百分比判断短期趋势方向和强度
3. 波动率分析：基于24h高低价差计算日内波动幅度，评估波动水平
4. 关键价位：识别支撑位（24h低点附近）和阻力位（24h高点附近）
5. 市场活跃度：基于成交量/市值比评估流动性
6. 与历史高点的距离：当前价格距ATH的回撤幅度

要求：
- 所有结论必须基于提供的数据，不要编造数据
- 不提供买卖建议
- 用中文回答，简洁专业"""},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    response = requests.post(url=mm_BASE_URL, headers=headers, json=data)
    result = response.json()
    content = result["choices"][0]["message"]["content"]

    if "<think>" in content:
        content = content.split("</think>")[-1].strip()
    content = content.replace("```json", "").replace("```", "").strip()

    return content