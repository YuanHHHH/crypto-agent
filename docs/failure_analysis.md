# failure_analysis.md

> Week 10 Eval 失败案例根因分析
> 基于 `data/eval/eval_result_final.jsonl`，12 个非 context case，三版 Agent

---

## 一、总体数据

| 版本 | 规则 pass | 通过率 | judge 有效 case | avg accuracy | avg completeness | avg relevance |
|------|----------|--------|----------------|-------------|-----------------|--------------|
| 手写版 | 10/12 | 83% | 10 | 8.9 | 9.4 | 9.7 |
| LangGraph | 9/12 | 75% | 12 | 8.9 | 8.9 | 9.8 |
| LangChain | 4/12 | 33% | 5 | 7.6 | 10.0 | 9.8 |

LangChain 的 judge 分数基于 5 个有效 case，代表性有限。completeness 10.0 说明它成功时回答质量不差，核心问题在工具调用路径上，而不是回答组织能力上。

---

## 二、失败案例逐条分析

### Case1 LangChain — 工具失败后编造数据（高危失败模式）

**失败类型**：规则失败（required_tools、required_response_fields）+ 数据编造

**现象**：

- `tools_called = ["_Exception"]`，工具实际未执行
- 但 `final_answer` 里出现了完整的 BTC 价格（$105,842.37）、24h 涨跌幅（+2.45%）、市值（$2.09 万亿）、交易量（$894.32 亿）
- 这些数字来自 LLM 幻觉，不是工具返回

**根因**：

LangChain 的 `ReActOutputParser` 无法解析 MiniMax 的输出，报 `Invalid or incomplete response`，把这次解析失败标记为 `_Exception` 工具调用。在 `handle_parsing_errors=True` 的配置下，AgentExecutor 继续重试，但模型随后直接生成了行情数据作为最终答案，绕过了工具调用路径。

**危险程度**：高。编造的数据表面上完整（含价格、市值、涨跌），在没有规则评估的情况下，这类回答很难被发现是虚假的。

**后续处理**：

- LangChain 版归入对照组，不作为主线
- 后续可以增加规则：如果 tools_called 里只有 `_Exception`，且回答里包含数字，判定为「工具失败后编造数据」

---

### Case2 LangGraph — 工具选择漂移

**失败类型**：规则失败（required_tools，实际调用 `analyze_coin` 而非 `get_coin_detail`）

**现象**：

- Case2 要求查询 ETH 市场详情，required_tools = `["get_coin_detail"]`
- LangGraph 版实际调用了 `analyze_coin`，返回了 ETH 行情分析报告
- 报告内容本身质量很高（judge 给 8/7/10），但 `market_cap` 字段在 tool_results 里不存在

**根因**：

`analyze_coin` 是一个封装了价格 + 分析的复合工具，返回的是文本报告（`{"raw": "..."}` 格式），而不是结构化的 `market_cap` 字段。LLM 认为 `analyze_coin` 更适合「市场详情」这类问题，但它的输出格式和 required_response_fields 不匹配。

**是 Agent 逻辑问题还是标注问题**：

两者都有。工具描述可以更明确地区分 `get_coin_detail`（结构化数据）和 `analyze_coin`（文本报告）。标注上也可以把 `analyze_coin` 加入 `optional_tools`。

**后续处理**：

- Case2 标注：`optional_tools` 增加 `analyze_coin`
- `get_coin_detail` 和 `analyze_coin` 的工具描述加以区分

---

### Case3 LangChain — ReAct parser 崩溃，达到 iteration limit

**失败类型**：规则失败（step 超限、`[FAILED]` 标记）

**现象**：

- 调用 `get_market` 成功，拿到了市场数据
- 但 MiniMax 的下一步输出不符合 ReAct 格式，parser 报 `Missing 'Action:' after 'Thought:'`
- `handle_parsing_errors=True` 让模型继续重试
- 重试 5 次后达到 max_iterations，返回 `[FAILED] Agent stopped due to iteration limit or time limit`

**根因**：

MiniMax-M2.7 在拿到工具结果后，倾向于直接输出分析结论，而不再写 `Thought: Do I need to use a tool? No / Final Answer: ...` 的格式前缀。LangChain 的 parser 要求精确格式，失配就报错。

这是 Week 7 发现的核心问题：**LangChain ReAct parser 的严格度和 MiniMax 的格式遵从度之间存在 gap**。

**后续处理**：

- LangChain 版保留为对照组，此问题不投入修复资源
- 在 failure_analysis 里明确归类为「ReAct 文本协议结构性失败」

---

### Case4 LangChain — 多工具场景全程 _Exception

**失败类型**：规则失败（required_tools、`[FAILED]` 标记）

**现象**：

- Case4 要求对比 BTC 和 ETH 价格，需要调用 `get_price` 两次
- LangChain 版 5 次 intermediate_steps 全是 `_Exception`，没有成功执行任何工具
- 最终 `[FAILED] Agent stopped due to iteration limit or time limit`

**根因**：

MiniMax 在 multi-tool 场景下更难遵守 ReAct 格式。第一次工具调用格式就出问题，parser 失败，后续重试也无法恢复。

---

### Case9 全三版 — 拼写错误场景没有友好提示

**失败类型**：规则失败（response_contains 检查未命中）

**现象**：

- Case9 问「BTCC 多少钱」，expected_answer_points 是「提示未找到该币种」+「建议是否指 BTC」
- response_contains 关键词：`["未找到", "不存在", "无法识别", "无法查询"]`
- LangGraph 版回答：「系统未能识别 BTCC 作为一个加密货币代币」— 语义上正确，但没有命中关键词
- 手写版直接返回 `[ERROR] BTCC`
- LangChain 版 `[FAILED]`

**根因**：

这是一个标注问题和 Agent 能力问题的混合：

1. **标注问题**：response_contains 关键词列表不够全面，「系统未能识别」是同等语义但没有被纳入关键词
2. **Agent 问题（手写版）**：`InvalidCoinError` 抛出后直接冒泡，没有继续生成用户友好提示

**后续处理**：

- 标注更新：response_contains 增加「未能识别」「未能找到」等同义词
- 手写版修复：`InvalidCoinError` 作为可恢复工具错误，把错误信息传回 LLM 继续生成

---

### Case10 手写版、LangChain — 不存在币种没有友好回答

**失败类型**：规则失败（response_contains 未命中、`[ERROR]` 标记）

**现象**：

- 手写版：`[ERROR] fakedog`
- LangChain：`[FAILED] Agent stopped due to iteration limit or time limit`
- LangGraph 版通过（回答「未能在数据库中找到名为 FAKEDOG 的加密货币」）

**根因**：

和 Case9 手写版问题一致。`InvalidCoinError` 异常直接冒泡，没有进入错误恢复路径。

---

### Case14 LangGraph — max_steps 标注偏严

**失败类型**：规则失败（step 超限：实际 7 步，限制 5 步）

**现象**：

- LangGraph 版的 `total_steps` 是 `graph.stream()` 的 yield 次数
- think_node 每次都是一步，tool_node 每次也是一步
- Case14 调用了 3 次 search_rag（三次检索 PoS/PoW 知识），共 7 步
- judge 给了 9/10/10，回答质量很好

**根因**：

这是标注问题。LangGraph 的 step 计算方式和手写版不同，统一 max_steps=5 对 LangGraph 不公平。

**后续处理**：

- Case14 标注：max_steps 改为 8
- 长期：引入按 Agent 版本差异化的 max_steps 配置

---

## 三、失败模式分类汇总

| 失败模式 | 涉及 case | 版本 | 根因 |
|---------|-----------|------|------|
| ReAct parser 严格度失败 | 3, 4, 9, 10, 13, 14, 15 | LangChain | MiniMax 不稳定遵守 ReAct 文本格式 |
| 工具失败后编造数据 | 1 | LangChain | AgentExecutor 在 parsing error 后绕过工具直接生成答案 |
| 可恢复工具错误未处理 | 9, 10 | 手写版 | InvalidCoinError 直接冒泡，没有错误恢复路径 |
| 工具选择漂移 | 2 | LangGraph | analyze_coin vs get_coin_detail 工具描述不够区分 |
| max_steps 标注偏严 | 14 | LangGraph | step 计算方式差异导致误判 |
| response_contains 关键词覆盖不全 | 9 | 全三版 | 标注问题，关键词未覆盖语义等价表达 |

---

## 四、后续修复优先级

### P0：立即修复

1. **手写版 InvalidCoinError 恢复路径**

   在 `agent_runner.py` 的 tool call 异常捕获里，区分可恢复错误（InvalidCoinError）和致命错误（网络失败），把可恢复错误作为 observation 传回 LLM 继续生成。

2. **边界 case response_contains 扩充**

   Case9/10 的 response_contains 加入：「未能识别」「未能找到」「没有找到」等同义词。

### P1：本周内修复

3. **LangGraph `<think>` 输出清洗**

   在 `run_langgraph_for_eval` 提取 final_answer 时，清除 `<think>...</think>` 内容，避免影响 judge 评分和用户体验。

4. **Case14 max_steps 标注修正**

   将 Case14 的 max_steps 从 5 改为 8。

### P2：Week 11 之前修复

5. **LangChain ReAct 版归档**

   在 README 和代码注释里明确 LangChain 版为「对照组」，不参与主线回归测试。

6. **Case2 工具描述和标注优化**

   区分 `analyze_coin`（文本报告）和 `get_coin_detail`（结构化数据），Case2 optional_tools 加入 `analyze_coin`。

---

## 五、对面试的价值

这批失败数据说明了几个对面试很有价值的工程结论：

**结论一：工具调用协议决定 Agent 成功率上限**

LangChain ReAct 版（文本协议）在工具调用场景失败率 ~70%，LangGraph（function calling）在同样场景失败率 ~10%。差异不来自 prompt 质量，而来自协议层。

**结论二：编造数据是高危失败模式，纯文本评估无法发现**

Case1 LangChain 的编造数据只有通过规则评估（检查 tools_called 和 required_response_fields）才能发现。如果只看文本输出，会误判为成功。

**结论三：边界场景需要专门设计，不能靠主流程兜底**

三版 Agent 在 Case9/10 边界场景的通过率（0/3）说明，「拼写错误识别」和「友好错误提示」不会自动出现，需要明确设计工具错误恢复路径。

**结论四：评估体系本身需要持续迭代**

max_steps 口径不一致、response_contains 关键词不全面、Case2 标注和实际工具输出不匹配——这些说明 Eval 体系设计本身需要和 Agent 一起迭代，不是一次性建好就完成了。
