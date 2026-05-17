# Week 9 Daily Reflection

## Day 1

今天学了什么新东西：LangGraph 的四个核心概念（State / Node / Edge / Graph），以及 StateGraph vs while 循环的工程差异。

今天最大的困惑：为什么用 LangGraph 而不是 AgentExecutor？说不出来它的具体优势。后来通过对比 interrupt/resume、checkpointer、显式状态图这些特性，理解了 LangGraph 在生产级场景下的不可替代性。

明天要做什么：Day 2 设计文档，画状态图 + 写伪代码，不写真实代码。

## Day 2

今天学了什么新东西：对比了自己设计的 8 个 State 字段和官方的 1 个字段（messages），理解了 LangGraph 的 Message 类型系统（HumanMessage / AIMessage / ToolMessage）把工具调用信息全部编码在消息对象里。

今天最大的困惑：Function Calling 到底怎么工作？模型怎么知道有哪些工具？查了 MiniMax 文档确认支持 OpenAI 兼容的 tools 参数和 tool_calls 返回。

明天要做什么：Day 3 最简单的 LangGraph hello 图，祛魅 LangGraph。

## Day 3

今天学了什么新东西：compile 做了三件事（校验完整性、确定执行顺序、返回可执行对象），invoke 和 stream 的区别（一口气跑完 vs 每步 yield）。

今天最大的困惑：TypedDict 传错类型（string 而不是 list）不会报错，行为会静默偏离预期。这是 TypedDict 运行时不校验的问题。

明天要做什么：Day 4 把 hello 图替换成真实 crypto-agent。

## Day 4

今天学了什么新东西：bind_tools + ToolNode + tools_condition 三件套替代了手写版的 ToolRegistry + parse_llm_output + prompts 三件套。MiniMax M2.7 支持 parallel tool calls，一次返回两个 tool_calls。

今天最大的困惑：一开始 State 还是写了 8 个字段（沿用手写版心智模型），review 后砍到只剩 messages 一个字段。同时理解了 start_node 不该在 graph 里，用户交互应该在 graph 外面。

明天要做什么：Day 5 加 Checkpointer + interrupt/resume。

## Day 5

今天学了什么新东西：InMemorySaver 做 checkpointer，thread_id 区分会话。interrupt() 可以暂停图执行，Command(resume=...) 恢复。实现了工具调用前人工审核流程。

今天最大的困惑：interrupt 之后的 resume 循环里 trace 记录逻辑和主循环重复，抽取成 record_step 函数解决了。还有 parallel tool calls 时 interrupt 只确认一次但执行多个工具的设计取舍。

明天要做什么：Day 6 三版对比测试 + 对比文档。

## Day 6

今天学了什么新东西：用 compare_agents.py 批量测试三版 Agent，拿到了真实对比数据。手写版 3/5、LangChain 版 2/5、LangGraph 版 5/5。核心发现：手写版测试 3 失败因为 MiniMax 混入了 `<minimax:tool_call>` 标签，LangGraph 版完全不受影响。

今天最大的收获：三版差异的根因不在框架层，在工具调用协议层。Function Calling 消除了 ReAct 文本协议的 parser 脆弱性。这个认知是 Week 9 最有价值的产出。

明天要做什么：Day 7 文档收尾 + v0.8 发布。

## Day 7

Week 9 整体反思：

Week 9 比 Week 7 顺利很多。Week 7 卡在 MiniMax 格式遵从度问题上（ReAct parser 成功率 0%），Week 9 切到 Function Calling 后这类问题完全消失。

Day 2 强制写伪代码的机制有效吗？有效。Day 2 画完状态图后 Day 3-4 写代码时很清楚「我在实现哪个 node、这个 node 对应图里哪个位置」，没有出现 Week 7 那种「边写边想」的混乱。

哪个 Day 收获最大？Day 4（真实 Agent 跑通）和 Day 6（三版对比数据）。Day 4 是技术层面的里程碑，Day 6 是认知层面的里程碑。

Week 10 节奏要快还是慢？应该稳。Week 10 重点是 Eval 体系，不引入新框架，把已有的三版 Agent 在标注集上做系统化评估。
