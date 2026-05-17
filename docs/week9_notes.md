# Week 9 学习笔记

## 1. LangGraph 的核心抽象

LangGraph 的核心抽象是状态图（StateGraph）：把 Agent 的执行流程定义为一个有向图，节点（Node）是函数，边（Edge）是流转规则，状态（State）是在节点之间流转的共享数据对象。

它解决的问题是：让 Agent 的控制流从隐式（while 循环内部的 if-else）变成显式（图的拓扑结构），从而支持可视化、持久化、中断恢复和多 Agent 协作。

## 2. State / Node / Edge / Reducer 四个概念

**State**：在节点之间流转的共享数据容器。用 TypedDict 定义字段和类型。crypto-agent 里只有一个字段 `messages: Annotated[list[BaseMessage], add_messages]`。

**Node**：普通 Python 函数，输入是 State，返回 dict 作为对 State 的局部更新。crypto-agent 里有两个 Node：`think_node`（调 LLM）和 `tool_node`（执行工具）。

**Edge**：定义节点之间的流转方向。普通边是无条件跳转（tool_node 执行完无条件回到 think_node），条件边（conditional_edge）根据 State 内容决定走哪个分支。

**Reducer**：定义 State 字段在多次更新时的合并策略。`add_messages` 是追加（新消息加到列表末尾），不配 reducer 默认是覆盖（新值替换旧值）。这个区别在第一次实际跑代码时就踩到了：不配 reducer 会导致 messages 每步只剩最新一条。

## 3. conditional_edge 的设计哲学

LangGraph 把分支逻辑抽出来作为一等公民（conditional_edge），是因为 Agent 的核心决策点就是「LLM 输出后做什么」：调工具还是给答案。

在手写版里这个决策隐藏在 while 循环的 if-else 里，看代码不直观。在 LangGraph 里它是图上的一个显式分叉点，可以被可视化、被测试、被替换。

crypto-agent 里的 conditional_edge 判断条件是 `state["messages"][-1].tool_calls` 是否存在。有 tool_calls 走 tools 节点，没有走 END。这个判断之所以简洁，是因为 Function Calling 把 LLM 的工具调用意图结构化了，不需要用 parser 从文本里提取。

## 4. Checkpointer 的工程价值

Checkpointer 把每次 invoke 后的完整 State 持久化到存储介质（内存 / SQLite / Postgres）。下次 invoke 时传入相同的 thread_id，自动恢复上一次的 State 继续执行。

和 LangChain ConversationBufferMemory 的本质区别：

- Memory 只存对话历史（chat_history），是 State 的一个子集
- Checkpointer 存整个 State，包括 messages、中间变量、工具调用记录等
- Memory 在进程内存里，进程重启就丢了
- Checkpointer 可以持久化到磁盘，进程重启后恢复

生产环境下 Checkpointer 解决的真问题：用户和 Agent 聊到一半，后端服务重启（部署新版本、扩缩容），用户重新发消息时 Agent 能接着上次的上下文继续，不是从零开始。

## 5. 三种 Agent 实现的取舍

**手写版**适合学习阶段和模型格式遵从度低的场景。优点是完全可控，能针对特定模型做适配（比如 no_parsed 兜底）。缺点是代码量大、不支持持久化和人工介入。

**LangChain 版**适合模型格式遵从度高（GPT-4、Claude）且需要快速原型的场景。优点是生态丰富、代码量少。缺点是 parser 严格度和模型能力的 gap 在弱模型上会导致成功率骤降。

**LangGraph 版**适合需要状态管理、持久化、多 Agent 协作、HITL 的生产级场景。优点是显式状态图、Checkpointer、interrupt/resume、stream 可观测性。缺点是学习曲线比 LangChain 陡。

如果今天从零做一个生产级 Agent，选 LangGraph。理由是它在状态管理和可恢复执行上的优势是刚需，而 LangChain 生态（@tool、ChatOpenAI、Chroma 等）可以在 LangGraph 里直接复用。

## 6. Function Calling 对 Agent 开发范式的影响

Week 9 最大的认知收获是：Agent 的成功率瓶颈不在框架选择，在工具调用的通信协议。

手写版 + LangChain 版用 ReAct 文本协议，依赖 LLM 在自由文本里遵守格式约定，parser 必须处理格式异常。结果是：同一个模型（MiniMax M2.7），手写版 84% 靠兜底，LangChain 版 0% 因为严格 parser。

LangGraph 版用 Function Calling 协议，工具调用意图通过结构化字段（tool_calls）表达，不需要 parser。结果是 100% 成功率。

这个演变反映了行业趋势：工具调用的复杂度从应用层下沉到了模型层。开发者从「教 LLM 输出特定格式 + 写 parser 解析」变成「定义工具 schema + 读取结构化返回」。

面试时这条线能讲 2 分钟，涵盖「踩过坑 → 理解根因 → 跟上行业演进」三层认知。
