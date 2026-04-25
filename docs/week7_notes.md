# Week 7 学习笔记

## 1. Runnable 抽象是什么，解决了什么问题

LangChain 的核心抽象。所有组件（LLM、Prompt、Tool、Agent、Parser、Retriever）都实现 Runnable 接口，统一暴露 invoke/stream/batch 三种调用方式。

解决的问题：让不同类型的组件可以用 `|` 管道符自由组合。`prompt | llm | parser` 组成一个新的 Runnable，数据从左到右流。不用关心每个组件的内部实现差异。

类比：就像 Unix 管道 `cat file | grep error | sort`，每个命令有统一的 stdin/stdout 接口。

## 2. 手写 vs 框架的映射表

| 手写 Week 5-6 | LangChain Week 7 |
|---|---|
| AgentRunner 类 | create_react_agent（决策逻辑）+ AgentExecutor（主循环 + 工具调度） |
| ToolRegistry.register(name, func, desc, params) | @tool 装饰器（读 docstring + 类型标注自动生成 schema） |
| while 循环 + max_steps | AgentExecutor._call 里的 while self._should_continue(iterations, time_elapsed) |
| parse_llm_output 函数 | ReActOutputParser（内置在 create_react_agent 里） |
| conversation 字符串累加 | agent_scratchpad 占位符（AgentExecutor 自动管理） |
| SYSTEM_PROMPT + few-shot | hub.pull("hwchase17/react") 或自定义 PromptTemplate |
| chat_history list of dict | ConversationBufferMemory（memory_key + prompt 占位符对接） |
| trace.py 侵入式记录 | BaseCallbackHandler 声明式 hook |

## 3. AgentExecutor 主循环流程

executor.invoke({"input": "..."}) 的完整执行流程：

1. Chain.prep_inputs：调用 memory.load_memory_variables() 把对话历史合并到输入 dict
2. AgentExecutor._call：进入主循环
3. while self._should_continue(iterations, time_elapsed)：判断是否继续（没超过 max_iterations 且没超时）
4. self._take_next_step(...)：调用 agent（create_react_agent 返回的 Runnable）拿到下一步动作
5. 如果返回 AgentFinish：调用 _return() 返回最终答案，跳出循环
6. 如果返回 AgentAction 列表：执行对应工具，把 (action, observation) 追加到 intermediate_steps
7. 检查 return_direct：如果只调了一个工具且这个工具设了 return_direct=True，直接返回工具结果
8. iterations += 1，回到第 3 步
9. 如果循环走完没返回：用 early_stopping_method（force 或 generate）生成兜底答案
10. Chain.prep_outputs：调用 memory.save_context() 把本轮 QA 存入 memory

## 4. Memory 的 4 种类型和适用场景

ConversationBufferMemory：存全部对话历史。适合短对话（<10 轮）。问题是对话多了 token 消耗爆炸。

ConversationBufferWindowMemory：只存最近 K 轮。适合不需要长期记忆的场景（如客服 FAQ）。丢弃了早期上下文。

ConversationSummaryMemory：用 LLM 把历史总结成一段摘要。适合长对话（>20 轮）。缺点是总结本身消耗 token，而且可能丢失细节。

ConversationSummaryBufferMemory：最近 K 轮原文 + 早期对话的摘要。适合需要「近期精确 + 远期概括」的场景。是最灵活的方案，但实现最复杂。

生产环境还需要考虑：用户隔离（session_id）、持久化存储（Redis/SQL）、跨会话恢复。

## 5. Callbacks 的设计哲学

核心思想：关注点分离。业务逻辑和观测逻辑解耦。

手写版 trace.py 是「侵入式」的：在 agent_runner 的 while 循环里到处插 trace_record() 调用。改业务就要动观测，改观测就要动业务。

LangChain Callbacks 是「事件驱动」的：定义一个 Callback 对象，注册给 AgentExecutor。框架在执行过程中自动在关键时刻触发 hook（on_chain_start、on_tool_start、on_agent_action 等），业务代码完全不动。

实际踩的坑：

1. on_tool_start 在 LangChain 0.3 的 @tool 装饰器生成的 StructuredTool 上不触发。改用 on_agent_action 统计 tool_call_count
2. on_chain_start/on_chain_end 会被子链（LLM、Tool）多次触发，必须用 parent_run_id is None 过滤顶层
3. max_iterations 兜底时 on_agent_finish 仍然会触发（输出是兜底文案），不能靠「是否触发 on_agent_finish」判断成功失败

这些坑说明 Callbacks 不是万能的——它的观察粒度取决于框架暴露了哪些 hook。

## 6. LangChain 选型决策

推荐用 LangChain 的场景：

- 模型格式遵从度高（GPT-4、Claude）
- 需要快速原型验证
- 团队多人协作（框架提供统一规范）
- 需要丰富的生态集成（VectorStore、Retriever、各种 Memory）

推荐手写的场景：

- 模型格式遵从度低（MiniMax、部分开源模型）
- 需要精细控制 parser 行为
- 性能敏感（框架有额外开销）
- 学习阶段（手写帮助理解原理）

两者不矛盾：先手写理解原理，再用框架提高效率。面试时能对比两者差异的候选人比只会一种的有优势。