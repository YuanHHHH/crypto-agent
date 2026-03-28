import os

import requests
from dotenv import load_dotenv
load_dotenv()

mm_BASE_URL=os.getenv("LLM_BASE_URL")
mm_API_KEY =os.getenv("LLM_API_KEY")
headers = {
    "Authorization": "Bearer " + mm_API_KEY,
    "Content-Type": "application/json",
}
data = {
    "model":"MiniMax-M2.7",
    "messages": [
        {"role": "system", "content": "你是一个资深ai agent开发工程师"},
        {"role": "user", "content": "你有什么关于agent开发学习建议给我吗？"}
    ],
    "max_tokens": 1000,
    "temperature": 0.7
}

response = requests.post(url=mm_BASE_URL, headers=headers, json=data)

result = response.json()
content = result["choices"][0]["message"]["content"]
if "<think>" in content:
    content = content.split("</think>")[-1].strip()
print(content)