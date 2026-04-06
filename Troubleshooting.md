# 开发踩坑记录

开发过程中遇到的问题、原因分析和解决方案。面试时可以作为「项目难点」和「踩过的坑」的素材。

## Week 3: LLM API 接入

### LLM 返回内容包含 think 标签和 markdown 反引号

问题：MiniMax M2.7 返回的 content 里包含 `<think>...</think>` 标签和 ``` 反引号，导致 JSON 解析失败。

原因：部分 LLM 会在 content 里暴露思考过程（think 标签），并用 markdown 代码块包裹 JSON 输出。

解决：在 llm_client.py 里做后处理：
```python
if "<think>" in content:
    content = content.split("</think>")[-1].strip()
content = content.replace("```json", "").replace("```", "").strip()
```

面试怎么说：LLM 的输出不是完全可控的，需要在应用层做清洗和标准化处理。

## Week 4: Streamlit 前端

### except Exception as InvalidCoinError 没有区分异常类型

问题：写了 `except Exception as InvalidCoinError`，以为只捕获 InvalidCoinError，实际上捕获了所有异常。

原因：`as InvalidCoinError` 只是给捕获到的异常对象起了个变量名，和 exceptions.py 里定义的类没有关系。等价于 `except Exception as e`。

解决：用多个 except 分别捕获不同类型：
```python
except InvalidCoinError as e:
    st.error("币种不存在")
except APIError as e:
    st.error("API 请求失败")
except Exception as e:
    st.error(f"未知错误: {e}")
```

面试怎么说：Python 的异常匹配是按类型从上往下匹配的，except Exception 必须放在最后做兜底。

### requirements.txt 依赖版本冲突

问题：pip install 报错 `ResolutionImpossible`，packaging==26.0 和 streamlit 要求的 packaging<26 冲突。

原因：之前用 `pip freeze` 生成的 requirements.txt 锁定了所有间接依赖的精确版本。

解决：只写直接依赖，不写版本号，让 pip 自动解决兼容性：
```
requests
fastapi
uvicorn
pydantic
python-dotenv
pytest
httpx
streamlit
```

面试怎么说：requirements.txt 应该只列直接依赖，间接依赖让包管理器自动处理。生产环境用 pip freeze 锁版本时要注意兼容性。

## Week 5: 手写 ReAct Agent

### ToolRegistry 存函数引用 vs 函数名字符串

问题：register 方法里写了 `"function": f"{func}"`，把函数引用转成了字符串，导致 call 时报 `str object is not callable`。

原因：f-string 会调用对象的 __str__ 方法，把函数对象变成了类似 `<function get_crypto_price at 0x...>` 的字符串。字符串不能被调用。

解决：直接存函数引用 `"function": func`，不做任何转换。

面试怎么说：Python 的函数是一等公民，可以作为变量传递和存储。Tool Registry 的核心就是一个 dict，key 是工具名，value 里存函数引用。

### LLM 返回的文本不是 dict，不能用下标访问

问题：写了 `client_response["Action"]`，报错 `string indices must be integers`。

原因：llm_client 返回的是纯文本字符串，不是 dict。需要自己解析文本提取 Action 和 Action Input。

解决：用 split 按行解析：
```python
info_part = client_response.split("Action:", 1)[1]
function_name = info_part.split("Action Input:", 1)[0].strip()
params_text = client_response.split("Action Input:", 1)[1].strip()
params = json.loads(params_text.split("\n")[0].strip())
```

面试怎么说：手写 Agent 的核心就是字符串解析。LLM 的输出是非结构化文本，需要用文本处理把工具名和参数提取出来。这也是为什么后来有了 Function Calling API，把这一步标准化了。

### Agent 的 system prompt 和分析师 prompt 冲突

问题：llm_client.py 里硬编码了「你是一个专业的加密货币数据分析师」的 system prompt，Agent 传入的 ReAct system prompt 被忽略了。LLM 不知道自己是 Agent，不按 Thought/Action 格式输出。

原因：llm_client 的 system prompt 是固定的，没有设计成可配置的。

解决：给 llm_client 加 system_prompt 参数，默认值是原来的分析师 prompt，Agent 调用时传自己的 prompt：
```python
def llm_client(prompt, system_prompt=None):
    if system_prompt is None:
        system_prompt = default_system_prompt
```

面试怎么说：Agent 和普通 LLM 调用使用不同的 system prompt。设计上应该把 LLM 调用层做成通用的，system prompt 由上层业务（Agent / 分析器）决定。

### Agent 死循环：LLM 反复调用同一个工具

问题：LLM 每轮都输出相同的 Action，工具被反复调用 5 次直到 max_steps 耗尽。

原因：llm_client 返回值没有赋值回 client_response（忘了写 `client_response = llm_client(...)`），或者 conversation 没有正确累加 Observation，导致 LLM 每轮看到的上下文完全一样。

解决：
1. 确保 `client_response = llm_client(conversation, ...)` 接住返回值
2. 每轮把 LLM 回复 + Observation 追加到 conversation
3. system prompt 和 conversation 分开传，system prompt 放 system message，conversation 放 user message

面试怎么说：Agent 的 conversation 管理是最容易出 bug 的地方。LLM 需要看到完整的历史（包括自己之前的思考和工具返回的结果）才能正确推进。

### LLM 一次输出多个 Action，JSON 解析报 Extra data

问题：用户问「对比 BTC 和 ETH」，LLM 一次输出了两个 Action + Action Input，json.loads 解析第一个 JSON 后遇到多余内容报错。

原因：LLM 想一步到位同时查两个币种，但 Agent 的文本解析逻辑每次只能处理一个 Action。

解决：只取 Action Input 后面的第一行做 JSON 解析：
```python
params_first_line = params.split("\n")[0].strip()
params = json.loads(params_first_line)
```
在 system prompt 里加规则「每次只调用一个工具」。

面试怎么说：LLM 的输出格式不保证 100% 一致，Agent 代码必须做防御性解析。这也是 prompt engineering 的一部分：通过规则和示例约束 LLM 的输出行为。

### LLM 编造数据：只查了一个币种就编造另一个的价格

问题：LLM 查了 BTC 的价格后，直接编造了 ETH 的价格写在 Final Answer 里，没有调用第二次工具。

原因：LLM 倾向于「偷懒」，拿到部分数据后就开始编造剩余部分。

解决：
1. system prompt 加规则「不要编造数据，所有价格必须通过工具获取」
2. 加 few-shot 示例：展示一个完整的多币种对比流程（查 BTC > Observation > 查 ETH > Observation > Final Answer）
3. LLM 看到示例后学会分步查询

面试怎么说：这是 Agent 开发中最常见的问题之一。LLM 有「幻觉」倾向，在 Agent 场景里表现为编造工具返回值。解决方案是 prompt 约束 + few-shot 示例 + 代码层数据校验。

### dict 遍历方式错误

问题：`for tool in self.tools` 遍历 dict 时，tool 拿到的是 key（字符串），不是 value。写 `tool["description"]` 实际上是在对字符串做下标访问。

解决：用 `.items()` 同时拿 key 和 value：
```python
for name, info in self.tools.items():
    desc = info["description"]
```

### `if __name__` 写法错误

问题：写成了 `def __name__():` 定义了一个函数，而不是主程序入口判断。

解决：正确写法是 `if __name__ == "__main__":`，这是一个 if 判断，不是函数定义。

### call 方法传参方式错误

问题：`registry.call("get_price", {"symbol": "bitcoin"})` 把 dict 当成位置参数传入，而 call 方法期望 **kwargs。

解决：用 ** 解包 dict：`registry.call("get_price", **{"symbol": "bitcoin"})` 或 `registry.call("get_price", symbol="bitcoin")`。