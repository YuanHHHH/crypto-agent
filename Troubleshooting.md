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

## Week 6: Agent 深化 + 对话记忆 + 质量评估

### analyze_coin 返回的分析报告被 Agent 二次抄写

问题：给 Agent 加 analyze_coin 工具后，工具内部调用 LLM 生成了一份完整的行情分析报告。Agent 调用这个工具拿到报告作为 Observation，但下一轮 LLM 没有按 Thought/Final Answer 格式输出，而是直接把整份报告复制粘贴出来，parser 识别不到前缀，走了 no_parsed 兜底分支。

原因：LLM 看到 Observation 里已经是一份完整答案，觉得「都给我了我直接抄一遍就行」，但忘了加 `Final Answer:` 前缀。这是嵌套 LLM 调用（subagent）设计时的典型问题。

解决方案有两层：
1. prompt 层：加一条强制规则「不管 Observation 里的内容是什么，你都必须按 Thought/Final Answer 的格式输出，不能直接复制 Observation 的内容」
2. 代码层：parser 的 no_parsed 兜底分支只返回 raw_text，不做二次包装，agent_runner 拿到后直接展示即可

```python
# prompts.py 里加这条规则
- 不管 Observation 里的内容是什么，你都必须按 Thought/Final Answer 的格式输出

# parser.py 的兜底分支保持简洁
else:
    return {
        "type": "no_parsed",
        "thought": extract_thought(client_response),
        "raw_text": client_response,
    }
```

面试怎么说：嵌套 LLM 调用（工具内部调用 LLM）是 subagent 架构的基础，但外层 LLM 看到内层 LLM 的完整输出时会困惑，需要在 prompt 里明确约束输出格式。这也是为什么真正的 subagent 架构需要独立的 context 隔离，而不是把子 agent 的输出直接塞给父 agent。

### LLM 幻觉出 Observation 字段

问题：LLM 在输出 Action 之后，自己又模仿了一段 `Observation: {...}` 假装看到了工具结果。比如：

```
Thought: 查 BTC 价格
Action: get_price
Action Input: {"symbol": "bitcoin"}
Observation: {"symbol": "bitcoin", "price": 87000}   ← 这是 LLM 幻觉的，不是真的工具结果
```

不影响功能（parser 用 `split("Action Input:", 1)[1].split("\n")[0]` 只取第一行 JSON），但干扰阅读，trace 日志里也很难看。

原因：few-shot 示例里展示了「Action 后面跟 Observation」的完整流程，LLM 学了这个模式后以为自己也要输出 Observation。另一方面，LLM 的训练数据里大量包含这种 agent 对话示例，模型被「污染」了。

解决：
1. prompt 加规则「不要在你的输出里包含 Observation，Observation 由系统自动添加，你只需要输出 Thought / Action / Action Input」
2. few-shot 示例里的 Observation 前加「（系统返回）」标注，让 LLM 区分「这是系统会给我的」和「这是我要输出的」

```
示例2:
用户问题：对比一下 BTC 和 ETH 的价格
Thought: ...
Action: get_price
Action Input: {"symbol": "bitcoin"}

（系统返回）
Observation: {"symbol": "bitcoin", "price": 87000, "change_24h": 2.3}

Thought: 已经拿到 BTC 的价格...
```

面试怎么说：这是 prompt engineering 里的一个细节。few-shot 示例虽然有效，但 LLM 可能会误学示例里的所有模式，包括本来不该它输出的部分。解决方案是在示例里用标记区分「输入」和「输出」。

### 多轮对话用字符串累加 chat_history 会越来越乱

问题：第一版对话记忆是用字符串存储 chat_history，每次 run() 把整个 conversation（包含 Thought/Action/Observation/Final Answer）全部拼接进去。第二轮对话时，新 conversation 里包含了第一轮完整的推理过程：

```
用户问题：BTC 多少钱
Thought: ...
Action: get_price
...
Observation: ...
Final Answer: BTC 价格 87000
用户问题：那 ETH 呢
Thought: ...
Action: get_price
...
```

到第三四轮 conversation 会变成一大坨，LLM 容易混乱，Token 消耗也快速上涨。

原因：没有区分「历史对话」和「当前推理过程」两种信息。历史对话只需要「用户问了什么、Agent 最终回答了什么」，中间的 Thought/Action/Observation 是推理痕迹，不应该喂给下一轮。

解决：chat_history 改成 list of dict，每个元素只存两个关键字段：

```python
# 结构
self.chat_history = []

# 更新时
self.chat_history.append({
    "user_question": user_question,
    "final_answer": final_answer
})

# 使用时
history_text = ""
for turn in self.chat_history:
    history_text += f"之前的问题：{turn['user_question']}\n之前的回答：{turn['final_answer']}\n\n"
conversation = history_text + "用户问题：" + user_question
```

这样 LLM 看到的历史就是清晰的「之前问了什么 + 之前回答了什么」，不会被中间的 Thought/Action 干扰。Token 消耗也大幅下降。

面试怎么说：对话记忆的核心原则是「只存结构化的关键信息，不存推理过程」。生产环境下还需要加上下文截断（只保留最近 N 轮）、摘要压缩（超长对话做 summary）等机制，应对 Lost in the Middle 问题（LLM 对上下文中间部分记忆衰减）。这些都是 Memory 模块的进阶内容。

### 字段名在生产端和消费端不一致（同一个问题出现多次）

问题：agent_runner 里 trace 记录的字段叫 `tool_call_count`，但 eval 里读的是 `line["total_tool_success"]`，名字完全对不上。运行时报 KeyError。同样的问题在 `end_reason` / `end_type` 字段也发生过：agent_runner 存的是 `"end_reason": end_type`，eval 里读的是 `line["end_type"]`。

原因：字段名用字符串硬编码在两个地方（生产端和消费端），一边改了另一边没同步。重构时很容易漏改。

解决：
1. 生产端和消费端的字段名必须严格一致。写代码时用 IDE 全局搜索确认
2. 读旧数据时总是用 `.get("field", 默认值)` 加兜底，这样数据结构升级时老数据不会让代码崩
3. 统一命名风格：Python 惯例是小写下划线（snake_case），不要混用大小写和空格
4. 大型项目可以把字段名定义成常量（比如 trace_fields.py 里定义 `TOOL_CALL_COUNT = "tool_call_count"`），生产端和消费端都 import 这个常量，IDE 会帮你做拼写检查和重构

```python
# trace_fields.py
USER_QUESTION = "user_question"
FINAL_ANSWER = "final_answer"
END_REASON = "end_reason"
TOOL_CALL_COUNT = "tool_call_count"
PARSE_ERROR_COUNT = "parse_error_count"

# agent_runner.py
record = {
    USER_QUESTION: user_question,
    END_REASON: end_type,
    TOOL_CALL_COUNT: tool_call_count,
}

# eval.py
for line in json_list:
    if line[END_REASON] == "final_answer":
        ...
```

面试怎么说：这是数据 pipeline 里最常见的坑之一。生产环境里通常用 Protobuf / JSON Schema / Pydantic 模型做强类型约束，让字段名在编译期就对齐。我后面做 LangChain / LangGraph 时会用 Pydantic 定义所有中间状态，从根本上避免这类问题。这也是为什么面经里反复强调「接口契约」。

### steps 计数 bug：final_answer 分支 break 前没累加

问题：eval 报告显示平均步数 0.9，数据明显偏小。正常情况下调用工具的问题至少应该是 2 步（action + final_answer），不调用工具的是 1 步。10 个问题里有几个多步调用（比如对比 BTC 和 ETH 是 3 步），平均应该在 1.5-2 之间才对。

原因：agent_runner 的主循环结构是：

```python
while max_steps > steps:
    # 解析 LLM 输出
    if response_parsed.get("type") == "action":
        # 调用工具
        pass
    elif response_parsed.get("type") == "final_answer":
        break   # ← 直接跳出，下面的 steps+=1 没执行
    elif response_parsed.get("type") == "no_parsed":
        break   # ← 同样的问题
    
    steps = steps + 1   # ← 循环末尾才累加
```

action 分支走完会执行末尾的 `steps += 1`，但 final_answer 和 no_parsed 是 break 跳出循环，跳过了累加。所以最后一步（产生 final_answer 的那一步）没被计数。

举例：查 BTC 价格的流程是
1. 第一轮：action（调用 get_price）→ steps 末尾 +1 → steps = 1
2. 第二轮：final_answer → break → steps 还是 1

实际执行了 2 步，却只记录了 1 步。

解决：在 break 之前手动累加 steps：

```python
elif response_parsed.get("type") == "final_answer":
    end_type = "final_answer"
    final_answer = response_parsed["final_answer"]
    steps += 1
    break
elif response_parsed.get("type") == "no_parsed":
    end_type = "no_parsed"
    steps += 1
    break
```

修复后平均步数从 0.9 涨到 1.59，符合预期。

面试怎么说：这个 bug 是通过 eval 发现的。如果没有质量评估，我根本不会知道步数计数有问题。这就是可观测性的价值：把肉眼看不见的行为变成可量化的指标。另外，这种 break + 循环末尾累加的模式本身就容易出 bug，更好的写法是把「累加」放在每个分支的明确位置，或者用 for 循环 + 显式退出条件替代 while + break。

### no_parsed 兜底率持续 15%，但答案其实是对的

问题：batch_test 10 个用例里有 1-2 个走了 no_parsed 兜底分支。仔细看 LLM 输出，答案内容是完全正确的：

```
Thought: 用户想知道 BTC 的价格...
Action: get_price
Action Input: {"symbol": "bitcoin"}
（系统返回 Observation）
BTC 当前价格为 $71,216，24h 跌幅 -0.97%。   ← 这一行没有 "Final Answer:" 前缀
```

LLM 拿到 Observation 后直接输出了答案文本，但**省略了 `Final Answer:` 前缀**。parser 既没匹配到 Action 也没匹配到 Final Answer，走了 no_parsed 兜底。

原因：MiniMax 模型在多轮对话的第二轮（拿到 Observation 后）有时会忘记 prompt 的格式约束。特别是当 Observation 是结构化 JSON 数据时，模型倾向于直接开始分析，跳过格式化前缀。这是模型训练偏见。

解决方案（当前标记为已知问题，Week 7 集中优化）：
1. prompt 层：加更强的格式约束「每次回复都必须以 Thought: 开头，即使你已经拿到了 Observation」
2. parser 层：智能兜底，如果 LLM 输出是有意义的长文本（比如超过 20 字），就当作 final_answer 处理而不是 no_parsed：

```python
else:
    if len(client_response.strip()) > 20:
        return {
            "type": "final_answer",
            "thought": "",
            "final_answer": client_response.strip(),
        }
    else:
        return {
            "type": "no_parsed",
            "raw_text": client_response,
        }
```

3. 根本方案：切换到 Function Calling 格式的 LLM API，让工具调用走标准化的结构化接口而不是文本解析

面试怎么说：这个 case 很有意思，值得单独拿出来讲。一个数据两种视角：用户体验角度答案正确用户满意，系统指标角度兜底率 15% 触发了异常分支。这说明 **Agent 质量不能只看「用户满没满意」还要看「系统行为是否符合预期」**。即使答案正确，走兜底分支对于调试、追踪、二次处理都有风险。这也是为什么要做 eval——没有可观测性就不知道系统真实状态。

### `<minimax:tool_call>` 格式幻觉

问题：MiniMax 模型偶尔会绕过 prompt 定义的 Action 格式，自己输出它训练时内置的工具调用格式：

```
<minimax:tool_call>
<invoke name="get_coin_detail">
<parameter name="coin_id">ethereum</parameter>
</invoke>
</minimax:tool_call>
```

parser 识别不出这种格式，走 no_parsed 分支。

原因：MiniMax 被微调过内置的 tool_call 格式（类似 OpenAI 的 Function Calling），这个格式深入了模型的训练数据。即使 prompt 要求输出 Thought/Action 格式，模型在某些触发条件下会回退到它熟悉的格式。

解决：
1. 短期：依赖 no_parsed 兜底分支处理，不让 Agent 崩溃
2. 中期：在 prompt 里明确禁止「不要使用 XML 标签或 tool_call 格式，只能输出 Thought/Action/Action Input 文本」
3. 长期：切换到 Function Calling API（让 MiniMax 走它原生的工具调用路径），或者换一个 prompt 可控性更强的模型（Claude、GPT-4）

面试怎么说：不同模型的训练偏见会影响 prompt 的有效性。生产 Agent 选型时要考虑模型对自定义格式的遵从度。这也是为什么 LangChain 抽象出了「Agent Type」的概念，不同模型用不同的 parser 和 prompt 模板。

### Streamlit st.expander 参数类型错误

问题：尝试用 `st.expander(step_log)` 展示 Agent 推理过程，报错：

```
AI 分析失败: bad argument type for built-in operation
```

原因：st.expander 的参数是**标题字符串**，不是内容。传了一个 list 进去，Streamlit 试图把 list 转成字符串作为标题，触发类型错误。

解决：用 with 代码块，expander 里面再写具体内容：

```python
for step_info in step_log:
    step_num = step_info.get("step", "?")
    step_type = step_info.get("type", "")
    with st.expander(f"步骤 {step_num}：{step_type}"):
        if step_info.get("thought"):
            st.markdown(f"**Thought:** {step_info['thought']}")
        if step_type == "action":
            st.markdown(f"**Action:** `{step_info['action']}`")
            st.markdown(f"**Action Input:** `{step_info['action_input']}`")
            st.markdown(f"**Observation:** {step_info.get('observation', '')}")
        elif step_type == "final_answer":
            st.markdown(f"**Final Answer:** {step_info['final_answer']}")
```

面试怎么说：Streamlit 的 API 习惯是「标题放参数，内容放 with 代码块里」。这和 html 的思路一致：标签名和属性是一回事，内容是另一回事。

### Streamlit 在命令行脚本里跑出现 ScriptRunContext 警告

问题：用 `python -m scripts.batch_test` 直接跑批量测试时，输出里一直有大量警告：

```
Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
```

原因：batch_test 间接导入了 market.py，market.py 顶部有 `@st.cache_data(ttl=60)` 装饰器。Streamlit 的缓存装饰器只能在 `streamlit run` 环境下正常工作，在普通 Python 脚本里执行时会抛警告（但不影响功能）。

解决：
1. 短期：警告不影响功能可以忽略
2. 根本解决：把 Streamlit 相关代码和业务代码分离。业务层（tools/）不应该依赖 UI 层（streamlit），`@st.cache_data` 应该在 app.py 里单独包装一层：

```python
# tools/market.py 保持纯业务函数
def get_market_overview() -> dict:
    # 不带 @st.cache_data
    ...

# app.py 里再包一层缓存
@st.cache_data(ttl=60)
def cached_get_market_overview():
    return get_market_overview()
```

这样 tools 模块可以被 API、Agent、测试脚本自由导入，不再依赖 Streamlit。

面试怎么说：这是依赖边界不清的典型问题。业务层不应该依赖 UI 层，否则复用时到处漏。Week 7 重构时我会按这个原则重新组织代码。这就是「关注点分离」原则——每一层只关心自己的事，不污染下层。

### MiniMax API 520 错误频繁出现

问题：开发过程中 MiniMax API 偶尔返回 520 错误（Cloudflare 网关错误），特别是多步工具调用时。错误信息：

```
src.utils.exceptions.APIError: LLM API 调用失败: unknown error, 520 (1000)
```

一开始是整个 Agent 崩溃报 KeyError: 'choices'，因为 llm_client 直接访问 `result["choices"][0]["message"]["content"]`，没有检查返回结构。

原因：
1. MiniMax 后端服务临时抖动（最常见，几秒到几分钟内自己恢复）
2. 请求 payload 可能触发某些边界情况（特殊字符、prompt 触发安全审查等）
3. 多步工具调用时 conversation 较长，可能触发模型处理异常

解决：分三层防御
1. llm_client 层：检查返回结构，遇到错误 raise 明确异常
```python
if "choices" not in result:
    error_msg = result.get("error", {}).get("message", "unknown error")
    raise APIError(f"LLM API 调用失败: {error_msg}")
```
2. agent_runner 层：捕获 APIError，返回友好提示不崩溃
```python
try:
    client_response = llm_client(conversation, system_prompt=...)
except APIError as e:
    final_answer = f"LLM 服务暂时不可用: {e}"
    break
```
3. 用户层：给用户友好的错误信息，trace 里记录完整错误

面试怎么说：生产级 LLM 应用必须做好容错。至少三件事要做：
- 自动重试：短时抖动用 retry 装饰器处理
- 熔断机制：持续失败时切换备用模型（比如 MiniMax → 通义千问 → 豆包）
- 降级方案：LLM 完全不可用时返回预设的兜底回复，保证用户体验

这也是为什么面经里「Agent 稳定性」是重点考察方向。我的 retry 装饰器只处理了 CoinGecko API，Week 9-10 工程化阶段会给 llm_client 也加上 retry + 熔断。

### httpx 漏装导致 pytest 全部失败

问题：跑 `pytest tests/ -v` 时，tests/test_api.py 无法 collect：

```
ERROR collecting tests/test_api.py
ModuleNotFoundError: No module named 'httpx'
RuntimeError: The starlette.testclient module requires the httpx package
```

原因：FastAPI 的 TestClient 依赖 httpx，但我的 requirements.txt 漏了这个包。之前开发环境用 `pip install httpx` 单独装过，但没同步到 requirements.txt。新克隆仓库或重建 .venv 时就会出错。

解决：
1. `pip install httpx` 补装
2. 更新 requirements.txt 加上 httpx
3. 验证：删除 .venv 重建，`pip install -r requirements.txt` 能一次性装齐所有依赖

面试怎么说：每次 pip install 新包都要同步到 requirements.txt。更规范的做法是用 poetry / uv / pipenv 这种工具，装包的同时自动更新依赖配置文件。这也是为什么现代 Python 项目推荐用 pyproject.toml 替代 requirements.txt。Week 12 重构时我会考虑迁移到 uv（更快，且依赖管理更可靠）。

### parser 里的 thought 提取会把后面的内容全部带进来

问题：第一版 extract_thought 写成 `client_response.split("Thought:", 1)[1].strip()`，结果 thought 里包含了后面的 Action、Action Input、Final Answer 全部内容。

原因：split 只是按关键字切分，取 [1] 拿到的是「Thought:」之后的所有文本，没有设定结束边界。

解决：加一个辅助函数，遇到下一个关键字时截断：

```python
def extract_thought(text):
    if "Thought:" not in text:
        return ""
    after_thought = text.split("Thought:", 1)[1]
    for stop_word in ["Action:", "Final Answer:"]:
        if stop_word in after_thought:
            after_thought = after_thought.split(stop_word)[0]
    return after_thought.strip()
```

另外 no_parsed 情况下 LLM 可能完全没有 Thought 关键字，`split("Thought:", 1)[1]` 会报 IndexError。上面的实现用了 `if "Thought:" not in text` 提前判断，返回空串。

面试怎么说：文本解析要考虑边界情况。「某个关键字不存在」「某个关键字出现多次」「关键字之间的文本可能包含特殊字符」都是常见陷阱。生产级解析应该用正则或状态机替代 split 的暴力切分。

### agent_runner 里定义了 step_log 但没使用

问题：Day 2 写 agent_runner 时定义了 `step_log = []`，但后面主循环里完全没有使用这个变量。定义了却不用会让代码迷惑读者。

原因：规划 Day 5 可视化时提前埋了变量，但当时还没实现。

解决：要么删掉（等 Day 5 再加），要么立刻实现（完成每一步的推理记录）。最终在 Day 5 真正用上了它。

面试怎么说：写代码的原则之一是「不要提前引入未使用的抽象」（YAGNI，You Ain't Gonna Need It）。当时埋下这个变量不算错，但应该加注释说明「Day 5 会用到」，或者干脆等要用时再加。

### step_log 里步骤编号跳号（0, 2 没有 1）

问题：Streamlit 展示的推理过程里，步骤编号不连续，从 0 直接跳到 2。

原因：各个分支 append step_log 时用的是当前 `steps` 值，但不同分支累加 steps 的时机不一样。action 分支在 append 之后才累加，final_answer 分支在 append 之前就累加了，导致编号错乱。

解决：不用 steps 变量做编号，直接用 `len(step_log) + 1`：

```python
step_log.append({
    "step": len(step_log) + 1,
    "type": response_parsed.get("type"),
    ...
})
```

这样每次 append 时编号严格按 list 长度递增，和 steps 变量解耦。

面试怎么说：两个变量做同一件事（记录顺序）就会出现不一致。原则是「一个数据只由一个源头维护」，显示编号用 list 长度，循环控制用 steps 变量，各司其职。

### tests 模块 import 顺序问题

问题：pytest 运行时偶尔会因为导入顺序不对崩溃。某些模块在导入时会触发 Streamlit 缓存装饰器初始化，在非 streamlit run 环境下抛警告。

原因：测试环境没有 Streamlit runtime，但被测代码（如 market.py）顶部有 `@st.cache_data`。

解决：暂时忽略警告，根本方案是把 Streamlit 缓存移出业务代码（参见「ScriptRunContext 警告」那条）。

面试怎么说：测试和生产环境的差异会暴露出代码里的隐式依赖。好的测试应该只依赖被测对象，不依赖外部运行时。

# TROUBLESHOOTING - Week 7 新增条目

## 15. LLM 输出参数污染导致工具调用失败

现象：LangChain ReAct Agent 调用 get_price 时，底层 CoinGecko API 返回空 body {}，报 InvalidCoinError。但用 curl 单独测试 CoinGecko 完全正常。

根因：MiniMax 在同一次输出里混用了 ReAct 协议和自己的 [TOOL_CALL] 格式。LangChain 的 ReActOutputParser 把 Action Input 后面所有内容（包括 [TOOL_CALL] 块）都当成参数值，导致 symbol 被污染为 "bitcoin\n[TOOL_CALL]..." 这种脏字符串。CoinGecko 收到脏 ids 返回空对象。

排查关键：在 retry 装饰器里 print args 才看到真实参数值。普通 print(symbol) 因为换行符让污染内容显示在下一行，看起来像独立日志。

解决：在 Tool wrapper 里加 _sanitize 函数，只取第一行第一段作为真实参数。同时处理 JSON 对象字符串（{"symbol": "bitcoin"} -> bitcoin）。

## 16. CoinGecko 静默限流（200 + 空 body）

现象：CoinGecko API 返回 HTTP 200 但 body 是空对象 {}。代码只检查了 status_code != 200，没检查 body 结构，直接进入 symbol not in data 判断抛 InvalidCoinError。

根因：CoinGecko demo key 超额或被限流时，不返回 429，而是返回 200 + 空对象。这是 CoinGecko 对 demo tier 的一种静默限流策略。

解决：临时注释掉 API key 的 headers（裸访问也能用，额度更低但 Day 4 测试够了）。长期方案是在 price.py 里加空 body 检查。

教训：不能只信 HTTP 状态码。API 提供商可能在应用层做限流但不改状态码。

## 17. LangChain 版本选择（0.3 vs 1.0）

情况：LangChain 1.0 在 2025 年 10 月发布，推荐用 create_agent 替代 create_react_agent。但 Python 3.9 环境用 pip 装不了 langchain>=1.0。

决策：继续用 0.3.28。理由：0.3 教程更多、概念学习和 1.0 一致、1.0 API 还在变动（1.1 又挪了 create_agent 位置）。计划在 Week 9 用 Python 3.11 环境升级到 1.x + LangGraph。

面试话术：「我项目里用的是 0.3，我了解 1.0 的 create_agent 基于 LangGraph runtime，支持 middleware 和 durable execution。两者概念一致，1.0 更面向生产。」

## 18. react-chat prompt 缺少 chat_history 占位符

现象：用 hub.pull("hwchase17/react") 作为 prompt，配合 ConversationBufferMemory(memory_key="chat_history")，多轮对话时 Agent 不记得之前的对话。

根因：hwchase17/react 这个 prompt 的 input_variables 里没有 chat_history 占位符。Memory 存了历史但没有地方注入到 prompt 里。

解决：换成 hwchase17/react-chat（有 chat_history 占位符），或自定义 PromptTemplate 显式包含 {chat_history}。

教训：Memory 的生效需要两端对接：memory_key 命名要和 prompt 占位符名字一致。光传 memory 参数不够，prompt 里必须有对应的变量。

## 19. ReAct parser 严格性导致 LangChain 版成功率为 0

现象：三轮测试中工具调用全部成功（CoinGecko 返回了真实数据），但 Agent 最终输出全是 "Agent stopped due to iteration limit"。

根因：MiniMax 拿到工具结果后直接输出答案文本，不写 Thought: 和 Final Answer: 前缀。LangChain 的 ReActOutputParser 要求精确格式，缺少这些前缀就报 Invalid Format，handle_parsing_errors 让 LLM 重试也无效，循环耗尽 max_iterations。

对比：手写版 parser 有「长文本兜底」策略（>20 字符直接当 final_answer），所以成功率 84.4%。

教训：框架的严格 parser 在弱模型上反而降低成功率。「弱模型 + 精准场景」下，手写的宽松兜底可能比标准框架更有效。

## 20. LangChain Callback on_tool_start 不触发

现象：在 TraceCallback 里重写了 on_tool_start，但工具被调用时 on_tool_start 的 print 从未出现在输出里。tool_call_count 永远是 0。

根因：LangChain 0.3 里 @tool 装饰器生成的 StructuredTool 的调用走的是 Runnable chain 路径（触发 on_chain_start/end），而不是 Tool 路径（on_tool_start/end）。

解决：改用 on_agent_action（Agent 决定调用工具时触发）来统计 tool_call_count。

教训：Callback 的观察粒度取决于框架暴露了哪些 hook，以及具体组件走了哪条执行路径。不能想当然地假设 hook 名字对应的事件一定会触发。

## 21. on_chain_start/end 被子链多次触发

现象：预期 on_chain_start 在每次 invoke 时只触发一次，实际触发多次（AgentExecutor 自己一次、内部 LLM 调用一次、工具调用包装链一次）。导致状态被反复重置。

解决：用 parent_run_id is None 判断是否是顶层 AgentExecutor 的事件。顶层 chain 的 parent_run_id 是 None，子链的 parent_run_id 指向父链的 run_id。

注意：parent_run_id 和 run_id 不一样。run_id 是本次调用的唯一 ID（永远不为 None），parent_run_id 是父调用的 ID（顶层为 None）。

# TROUBLESHOOTING - Week 8 新增条目

## 22. MiniLM 跨语言 embedding 相似度极低

现象：用 all-MiniLM-L6-v2 对 "bitcoin" 和 "比特币" 做 embedding，cosine similarity 只有 0.10。预期应该 > 0.5。

根因：all-MiniLM-L6-v2 虽然号称支持多语言，但对中英文跨语言的语义对齐能力很弱。它在英文同义词上表现正常（"bitcoin" vs "BTC" = 0.72），但无法将中文和英文的同义词映射到向量空间中相近的位置。

解决：本项目语料是英文，所以在 SYSTEM_PROMPT 里引导 Agent 用英文关键词检索（示例 3 里 Action Input 写的是英文 query）。

教训：选 embedding 模型时必须测跨语言能力，不能只看模型名字里有没有 "multilingual"。如果需要中英混合检索，应该用 multilingual-e5-base、BGE-M3 等真正的多语言模型。

## 23. LLM 编造 Observation 绕过工具调用

现象：测试「对比 BTC 和 ETH 价格」时，Agent 正确调用了 get_price(bitcoin) 拿到 BTC 价格，但随后 LLM 自己伪造了一个 ETH 的 Observation（价格 $1,942.62），和真实价格（$2,339.82）严重不符。

根因：MiniMax 的格式遵从度不够。LLM 在一次输出里同时生成了 Action（查 ETH）和伪造的 Observation + Final Answer，parser 读到 Final Answer 后直接返回，没有等工具真实执行。

解决：这是 MiniMax 模型层面的问题，在 Week 8 无法根治。可以通过更严格的 prompt 约束（「禁止在输出里包含 Observation」已经写了但模型不一定遵守）或者在 parser 里检测是否存在未经工具返回的 Observation 来缓解。

教训：LLM 输出的所有内容都是不可信的，包括它声称的「工具返回结果」。只有系统级的 Observation（由 agent_runner 注入）才可信。这是 Agent 安全性的核心问题之一。

## 24. Chroma 的 distance 和 similarity 概念混淆

现象：开发时把 Chroma 返回的 distance 当成 similarity 使用，导致排序逻辑混乱。

根因：Chroma 的 query 返回的是 L2 距离（欧氏距离），距离越小越相似。而 sklearn 的 cosine_similarity 返回的是相似度，值越大越相似。两者方向相反。

解决：在 VectorStore.search 的返回字段里明确命名为 "distance" 而不是 "score" 或 "similarity"，避免调用方误解。在笔记里记录清楚 Chroma 默认用 L2 距离。

教训：不同库对「相似度」的定义和度量方式不同。cosine similarity（范围 -1 到 1，越大越相似）、cosine distance（1 减 cosine similarity）、L2 distance（欧氏距离，越小越相似）是三个不同的概念。使用前必须搞清楚当前库返回的是哪个。

## 25. chromadb PersistentClient 路径为相对路径导致数据创建在意外位置

现象：VectorStore 初始化时 persist_dir 使用相对路径 "data/vector_db"，在 PyCharm 中直接运行脚本时数据创建在了非项目根目录下。

根因：相对路径相对于运行脚本时的当前工作目录（cwd），PyCharm 的 cwd 设置可能和终端不一样。

解决：在 src/utils/config.py 里统一定义 VECTOR_DB_DIR 和 DOCS_DIR，用 os.path.dirname + os.path.abspath 推算项目根目录，所有文件都从 config 引用绝对路径。

教训：项目里的所有路径都应该从一个统一的 config 出发，不要硬编码相对路径或绝对路径。硬编码绝对路径会泄露个人信息（如用户名），硬编码相对路径会因 cwd 不同导致文件位置不可预测。

# TROUBLESHOOTING - Week 9 新增条目

## 26. LangGraph State 字段过多导致设计冗余

现象：Day 2 设计 State 时写了 8 个字段（user_input、messages、llm_output、tool_call、final_answer、usetool、toolname、tool_param），Day 4 实现后发现只有 messages 被实际读写，其他字段全是摆设。

根因：用手写版 ReAct Agent 的心智模型来设计 LangGraph State。手写版需要独立字段因为 LLM 输出是自由文本，必须用 parser 提取到各个变量里。LangGraph + Function Calling 模式下，所有信息都编码在 Message 类型系统里（AIMessage.tool_calls、ToolMessage.content 等），不需要额外字段。

解决：State 砍到只剩 `messages: Annotated[list[BaseMessage], add_messages]`。后来加 interrupt 时增加了 `tool_approved: str`，这是因为 interrupt 确认结果不适合放在 messages 里。

教训：设计 State 时先问「这个信息能不能从 messages 里读出来」，能读就不要加字段。State 字段越少，维护越简单。

## 27. start_node 不应该放在 graph 内部

现象：Day 4 第一版代码在 graph 里加了一个 start_node，内部调用 input() 获取用户输入。代码能跑但设计不对。

根因：混淆了 graph 的职责。graph 的职责是「接收输入 State → 处理 → 返回输出 State」，用户交互（input()、Streamlit 输入框、API 请求）是 graph 外部的事。graph 应该是纯粹的处理引擎，不关心输入从哪来。

解决：删掉 start_node，用户输入在 graph.invoke() 调用前处理，把 SystemMessage + HumanMessage 作为初始 State 传入。

教训：graph 里的 node 应该是纯函数（输入 state → 输出 dict），不能有 input()、print() 等副作用。副作用放在 graph 外面。

## 28. MiniMax Function Calling 后 ReAct prompt 残留导致混合输出

现象：Day 4 第一次跑通后，LLM 返回的 content 里混着 `<think>` 标签、`Thought:` 前缀和 `Final Answer:` 前缀，但 tool_calls 字段正常。最终输出有冗余格式文本。

根因：system prompt 还在用 Week 5-6 的 SYSTEM_PROMPT（包含 ReAct 格式规定和 few-shot 示例）。Function Calling 模式下 LLM 通过 tool_calls 表达工具调用，不需要在 content 里写 Action/Action Input，但 prompt 里的格式规定让 LLM 两种格式都输出了。

解决：system prompt 简化为 4 行纯业务指令，删掉所有格式规定和 few-shot 示例。

教训：切换工具调用协议时，prompt 必须同步调整。Function Calling 不需要 ReAct 格式约束，保留会导致 LLM 混合输出。

## 29. graph.invoke() 不传参数报错

现象：代码最后一行写了 `graph.invoke()` 没传参数，运行直接报错。

根因：invoke 需要初始 State 作为输入。手写版的 AgentRunner.run() 接收 user_question 字符串，但 LangGraph 的 invoke 需要完整的 State dict。

解决：`graph.invoke({"messages": [SystemMessage(...), HumanMessage(...)]})`。

## 30. TypedDict 运行时不校验类型导致静默错误

现象：Day 3 hello 图里 `messages` 定义为 `list[str]`，但 invoke 时传了一个 str 而不是 list。代码没报错但 len() 返回的是字符数而不是消息数，conditional_edge 走了错误分支。

根因：TypedDict 是静态类型标注，Python 运行时不做校验。传错类型不会报错，只是行为偏离预期。

解决：观察到输出异常后改成正确类型 `["hello", "langgraph"]`。生产环境应该用 Pydantic BaseModel 替代 TypedDict，Pydantic 会在运行时强制校验。

教训：Day 1 学概念时就提到过「TypedDict 运行时不校验，Pydantic 会校验」，Day 3 实际踩到了。

## 31. CoinGecko SSL 限流导致批量测试部分失败

现象：compare_agents.py 批量测试 15 个 API 请求（3 版 x 5 题），测试 2 的 LangChain、测试 5 的手写版和 LangChain 报 SSLEOFError。

根因：短时间内发起太多 HTTPS 请求，CoinGecko 或中间代理的 SSL 连接池耗尽，直接断开连接。不是 429 限流，是 SSL 握手阶段就失败了。

解决：测试之间加 3 秒间隔（time.sleep(3)）。LangGraph 版测试 5 第一次也 SSL 报错但 retry 成功了，说明 langchain_tools 里的 retry 装饰器在 LangGraph 版里也生效了。

教训：批量测试 Agent 时必须控制请求频率。CoinGecko 免费 tier 的限流不只是 429，还有 SSL 层面的连接拒绝。

## 32. Checkpointer thread_id 不传导致每次都是新会话

现象：Day 5 第一次测试多轮对话时，第二轮「那 ETH 呢」Agent 不理解上下文，当作全新问题处理。

根因：invoke 时忘了传 config（包含 thread_id）。没有 thread_id 的 invoke 每次都是独立会话，Checkpointer 不知道该恢复哪个状态。

解决：每次 invoke 和 stream 都传 `config={"configurable": {"thread_id": "user1"}}`。

教训：Checkpointer 的多轮记忆依赖 thread_id。生产环境下 thread_id 应该用 user_id 或 session_id，不能用固定字符串。