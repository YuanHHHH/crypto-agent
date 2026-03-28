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
             "content": "你是一个加密货币数据分析助手。你的任务是根据提供的价格数据进行客观的技术分析，包括趋势判断、波动率分析、关键价位识别。你只做数据层面的分析，不提供买卖建议。"},
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