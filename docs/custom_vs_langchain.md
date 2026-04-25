# 手写 ReAct Agent vs LangChain Agent 对比文档

## 背景

Week 5-6 手写了完整的 ReAct Agent（AgentRunner + parser + ToolRegistry + prompts + trace），Week 7 用 LangChain 0.3 重构了同样功能的 Agent（create_react_agent + AgentExecutor + ConversationBufferMemory + TraceCallback）。两个版本目标相同：基于 MiniMax-M2.7 模型，调用 CoinGecko API 的 4 个工具，回答加密货币相关问题。

## 代码量对比

| 模块 | 手写版 | LangChain 版 |
|------|--------|-------------|
| Agent 主循环 | agent_runner.py ~120 行 | langchain_agent.py ~40 行 |
| 工具注册 | tool_registry.py ~40 行 | langchain_tools.py ~50 行（含 sanitize） |
| 输出解析 | parser.py ~60 行 | 框架内置 ReActOutputParser |
| Prompt | prompts.py ~50 行 | 内嵌在 langchain_agent.py |
| 对话记忆 | agent_runner.py 内 ~15 行 | ConversationBufferMemory 3 行配置 |
| Trace 记录 | trace.py ~15 行 + agent_runner.py 内嵌 | langchain_callbacks.py ~80 行 |
| 总计 | ~300 行 | ~170 行 |

代码量减少约 43%。主要减少来自 Agent 主循环（AgentExecutor 替代了手写 while 循环）和输出解析（ReActOutputParser 替代了手写 parser）。

## 核心设计对比

| 维度 | 手写版 | LangChain 版 |
|------|--------|-------------|
| Parser 严格度 | 宽松。有 no_parsed 兜底：长文本 >20 字符直接当 final_answer | 严格。必须精确匹配 Thought/Action/Final Answer 格式 |
| 错误处理 | 手动分 4 个 type（action/final_answer/no_parsed/error） | handle_parsing_errors=True 自动重试 |
| 工具调度 | ToolRegistry.call() 手动分发 | AgentExecutor 自动调度 |
| 对话记忆 | list of dict，手动拼到 conversation 前面 | ConversationBufferMemory，通过 prompt 占位符自动注入 |
| 可观测性 | trace.py 侵入式（业务代码里到处插 trace_record） | Callbacks 声明式（注册一次，自动触发） |
| Prompt 管理 | 硬编码在 prompts.py | 可从 Hub 拉取或自定义 PromptTemplate |
| 扩展性 | 加新工具需要改 register + prompt | @tool 装饰器 + 自动注入 tools 描述 |

## 在 MiniMax 上的真实测试对比

### 手写版（Week 6 eval 数据）

- 成功率：84.4%
- 平均步数：1.59
- 兜底率（no_parsed）：15.6%
- 工具调用成功：100%（调用就能返回数据）

### LangChain 版（Week 7 实测）

- 成功率：0%（三轮测试全部 iteration_limit）
- 工具调用成功：100%（sanitize 之后 CoinGecko 正常返回）
- 失败原因：MiniMax 拿到工具结果后不写 Final Answer: 前缀，ReActOutputParser 报 Invalid Format，handle_parsing_errors 重试 5 次耗尽 max_iterations

### 根因分析

MiniMax-M2.7 的 ReAct 格式遵从度不够高。具体表现：

1. 拿到 Observation 后直接输出答案文本，不写 Thought: 和 Final Answer: 前缀
2. 混用自己的 tool_call 协议（`<minimax:tool_call>` 标签）和 ReAct 文本协议
3. Action Input 格式不稳定（有时纯字符串 bitcoin，有时 JSON {"symbol": "bitcoin"}）

手写版能跑通是因为 parser 的 no_parsed 兜底策略：如果 LLM 输出不包含 Action 也不包含 Final Answer，但文本长度超过 20 字符，就直接当成 final_answer 返回。这种「实用主义兜底」在弱模型场景下非常有效。

LangChain 的 ReActOutputParser 没有这种宽松兜底。它要求精确格式，格式不对就报错。这在 GPT-4/Claude 等格式遵从度高的模型上没问题，但在 MiniMax 上会严重降低成功率。

## 核心认知

框架不是银弹。在「弱模型 + 精准场景」下，手写实现的针对性适配可能比框架的通用方案更有效。具体来说：

1. 手写 parser 的宽松性是一种「工程妥协」，它牺牲了格式一致性换取了可用性
2. LangChain 的严格 parser 是一种「工程规范」，它保证了格式一致性但对模型要求更高
3. 选择哪种取决于你的模型能力和业务场景。如果模型格式遵从度高（GPT-4/Claude），用 LangChain 更好；如果模型格式遵从度低（MiniMax），手写的针对性适配不可替代

## 框架的真正价值

尽管在 MiniMax 上表现不如手写版，LangChain 的价值在于：

1. **概念统一**：Runnable 抽象让所有组件可组合，学习成本低
2. **生态丰富**：Memory、Callbacks、Hub、LangSmith 等模块开箱即用
3. **可维护性**：换模型只需改 1 行代码（ChatOpenAI 的 model 参数），不需要改 parser 和 prompt
4. **可观测性**：Callbacks 机制比侵入式 trace 更解耦
5. **面试认可**：几乎所有 Agent 岗位都要求 LangChain 经验

## 面试素材总结

1. 「我手写过完整的 ReAct Agent 理解原理，也用 LangChain 重构过一版，能对比两者在代码量、鲁棒性、调试难度上的具体差异」
2. 「在 MiniMax 上实测发现，LangChain 默认 parser 严格度和模型格式遵从度之间有 gap，手写版通过宽松兜底策略弥补了这个 gap」
3. 「AgentExecutor 内部是一个 while 循环，_should_continue 判断退出条件，_take_next_step 执行单步，这和我手写的 while + parse_llm_output 结构一致」
4. 「LLM 输出是不可信输入源，工具层必须做 sanitize 防止参数污染」
5. 「CoinGecko 静默限流（200 + 空 body）是一个视觉欺骗级 bug，通过 repr 打印才定位到真正的参数值」
