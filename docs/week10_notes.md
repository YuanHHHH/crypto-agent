# Week 10 学习笔记：Eval 体系深度升级

**时间**：2026/05/18 - 2026/06/07
**版本**：v0.9

---

## 一、本周目标

Week 10 不新增功能，核心任务是为 crypto-agent 建立一套轻量但可信的 Eval 体系，回答一个 Week 9 还没有定量答案的问题：三版 Agent 到底在哪类问题上强、在哪类问题上弱？

**产出清单**

| 文件 | 作用 |
|------|------|
| `data/eval/eval_set_v1.jsonl` | 15 个标注 case |
| `src/agent/eval_rules.py` | 规则评估模块 |
| `src/agent/eval_judge.py` | LLM-as-judge 模块 |
| `src/agent/eval_runners.py` | 三版 Agent 统一 runner |
| `scripts/run_eval.py` | 批量评估脚本 |
| `scripts/rerun_failed_eval.py` | 失败样本重跑脚本 |
| `docs/failure_analysis.md` | 失败案例根因分析 |

---

## 二、设计取舍

### 1. 为什么不用只看成功率

只看 pass/fail 成功率会丢失大量信息。同样是「失败」，背后可能是完全不同的原因：

- Agent 没有调用工具，直接编造了数据
- 工具调用成功但 LLM 遗漏了关键字段
- 工具抛出异常后 Agent 返回了友好的错误说明（合理失败）
- 网络抖动导致 API 超时（外部失败，不代表 Agent 能力差）
- 回答内容正确，但 step 数超过标注限制（规则问题，不是 Agent 问题）

如果把这五种情况都统计成「失败」，成功率就成了噪声。

所以本周的 Eval 体系设计了「失败分类」：分清楚是 Agent 逻辑失败、工具失败、网络失败还是标注问题，才能做有意义的改进决策。

---

### 2. 为什么引入 LLM judge

规则评估擅长判断结构化事实：

- 是否调用了 required_tools
- 是否调用了正确的工具名
- 工具返回是否包含必要字段
- 步数是否超限
- 回答是否包含特定关键词

但规则评估有盲区：它无法判断回答是否真的有用。例如：

- 回答包含所有期望字段，但叙述混乱用户看不懂
- 回答简洁完整，但用的是 RAG 知识库里过时的说法
- 回答跑偏，混入了大量不相关内容，但 response_contains 还是命中了

LLM judge 补足了这个语义层面的判断，从三个维度打分：

- **accuracy**：数据是否来自工具，是否基于真实返回
- **completeness**：是否覆盖 expected_answer_points 里的关键点
- **relevance**：回答是否切题，有没有跑偏

judge 不验证实时价格的真伪（它不知道 BTC 当前真实价格），accuracy 主要看 Agent 是否真的调了工具。

---

### 3. 为什么规则评估和 judge 混合，而不是只用其中一个

| | 规则评估 | LLM judge |
|---|---|---|
| 擅长 | 工具路径、字段、步数、错误标记 | 语义质量、覆盖度、相关性 |
| 不擅长 | 回答是否真正有用 | 实时数据真伪、工具调用路径 |
| 成本 | 几乎零 | 每次一个 API 调用 |
| 稳定性 | 完全确定性 | 偶尔漂移 |

混合使用的好处是两者互补：

- 规则评估先过滤明显失败的 case（工具没调用、回答有 `[ERROR]`），避免让 judge 给废话评分
- judge 再对规则通过的 case 做语义质量评分

这样的双轨制评估比任何一方单独使用都更可信。

---

### 4. required_tools 和 optional_tools 分层的好处

最初的设计是单一的 `expected_tools` 列表，用了哪个就算哪个。但这会有两个问题：

**问题一：过于死板**

用户问「ETH 市场详情怎么样」，Agent 调了 `analyze_coin` 返回了完整的 ETH 分析报告，但标注的 required_tools 是 `get_coin_detail`。这种情况不应该被判失败，因为分析报告本身已经包含了市值、涨跌幅等信息。

**问题二：无法区分核心能力缺失和辅助能力不足**

比如 Case1（BTC 价格查询），`get_price` 是核心必须工具，`get_coin_detail` 是可以提升回答质量的辅助工具。如果不分层，这两个工具的失败后果就没有区别。

拆成 `required_tools` + `optional_tools` 之后：

- `required_tools`：缺少任何一个直接判规则失败
- `optional_tools`：调了是加分，不调不扣分
- 评估更公平，也更能找到真实的能力边界

---

## 三、实验结论

### 1. 三版 Agent 的规则通过率

在 12 个非 context case 上的测试结果（final 合并版本）：

| 版本 | 规则 pass | 通过率 |
|------|----------|--------|
| 手写版 | 10/12 | **83%** |
| LangGraph | 9/12 | 75% |
| LangChain | 4/12 | 33% |

judge 平均分（只计算执行成功的 case，ACC/COMP/REL）：

| 版本 | accuracy | completeness | relevance | 有效 case 数 |
|------|----------|-------------|-----------|------------|
| LangGraph | 8.9 | 8.9 | 9.8 | 12 |
| 手写版 | 8.9 | 9.4 | 9.7 | 10 |
| LangChain | 7.6 | 10.0 | 9.8 | 5 |

LangChain 的 judge 分数只有 5 个有效 case，代表性有限；completeness 10.0 说明它成功时回答质量不差，问题主要在工具调用路径上。

---

### 2. 哪一版在哪类问题更强

#### basic（基础工具调用）

| 版本 | 通过率 |
|------|--------|
| 手写版 | 5/5 ✅ |
| LangGraph | 4/5 |
| LangChain | 2/5 |

手写版在基础场景全通。LangGraph 的失败是 Case2：用了 `analyze_coin` 而不是 `get_coin_detail`，工具选择上有漂移。LangChain 在 Case1、Case3、Case4 上因为 ReAct parser 错误或编造数据而失败。

#### boundary（边界场景）

| 版本 | 通过率 |
|------|--------|
| LangGraph | 3/4 |
| LangChain | 2/4 |
| 手写版 | 2/4 |

三版在边界场景都有问题。Case9（BTCC 拼写错误）和 Case10（FAKEDOG 不存在）上，三版全部无法通过 `response_contains` 检查，因为回答里没有出现「未找到」「不存在」等关键词。

手写版的额外问题是直接返回 `[ERROR] BTCC` / `[ERROR] fakedog`，没有让 LLM 生成用户友好的解释。

#### complex（概念 + 数据组合）

| 版本 | 通过率 |
|------|--------|
| 手写版 | 3/3 ✅ |
| LangGraph | 2/3 |
| LangChain | 0/3 |

手写版复杂场景全通，令人意外。LangGraph 的失败是 Case14（PoS vs PoW）step 数超限（实际 7 步，限制 5 步）。LangChain 在三个复杂 case 上全部失败。

---

### 3. 哪类问题退化最明显

退化最明显的是两类：

**第一类：LangChain 在工具调用场景全面退化**

Case3/4/13/15 是典型案例，根因是 MiniMax-M2.7 在 ReAct 文本格式下不稳定，parser 经常报 `Missing 'Action:' after 'Thought:'`，导致整个 Agent 陷入 parsing error 循环直到 iteration limit。

这是 Week 7 发现的核心问题（LangChain 版成功率 0%）在更大规模 case 上的再次验证。

**第二类：所有版本在边界错误提示上退化**

Case9、Case10 三版全部未通过 `response_contains` 检查。这说明当前的 Prompt 和工具调用逻辑里，没有显式设计「拼写错误识别」和「友好错误提示」的路径。这是一个结构性短板，不只是某一个版本的问题。

---

### 4. 评估后发现的结构性短板

**短板一：LangChain ReAct 工具协议在 MiniMax 上不可靠**

文本 ReAct 协议要求模型严格按照 `Thought/Action/Action Input/Final Answer` 格式输出。MiniMax-M2.7 做不到这一点，导致 LangChain 在工具调用场景大量失败。这不是 prompt 能完全解决的问题，是协议层面的结构性缺陷。

**短板二：手写版的工具错误恢复路径缺失**

手写版 `agent_runner.py` 当工具抛出 `InvalidCoinError` 时，异常直接冒泡到顶层返回 `[ERROR] BTCC`，没有把错误传回给 LLM 让它生成用户友好的解释。正确的逻辑应该是：工具报错 → 把错误作为 observation 传给 LLM → LLM 生成解释 → 输出友好回答。

**短板三：边界错误提示机制缺失**

三版 Agent 都没有针对「不存在币种」「拼写错误」的专门处理路径。这类场景在真实用户使用中频率很高，需要在 Week 11 修复。

**短板四：LangGraph step 数统计方式和手写版不一致**

LangGraph 的 `total_steps` 是 `graph.stream()` 的 yield 次数（think_node + tool_node 各算一步），而手写版的 `total_steps` 是 `step_log` 的长度。相同任务 LangGraph 天然多 1-2 步，被统一 max_steps 误伤了 Case14。

---

## 四、演进价值

### 1. Week 10 为什么必须先做评估

Week 9 完成了三版 Agent 的基础实现，每版都有 5 个 case 的验证数据。但这 5 个 case 都是基础场景，没有边界测试、没有复杂组合、没有错误输入。

如果跳过 Week 10 直接进 Week 11 加新工具，会遇到这个问题：加了多交易所聚合、技术指标之后，不知道旧的 BTC 价格查询功能有没有退化，也不知道哪种错误来自新工具、哪种来自旧代码。

Week 10 先建立 Eval 体系，建立「加任何新功能前，旧 case 全部通过」的回归测试地基。

---

### 2. 它如何支撑 Week 11 以后的工具扩展

Week 11 计划增加的工具：

- 多交易所价格聚合（Binance/OKX/Bybit）
- 套利检测工具
- 技术指标（RSI/MACD/布林带）

这些新工具会让 Agent 的工具选择空间从 5 个扩展到 10+，工具之间的路由逻辑变复杂，失败模式也会增多。

Eval 体系的支撑方式：

1. 每次加新工具后，运行 `python scripts/run_eval.py` 跑旧的 15 个 case
2. 如果旧 case 通过率下降，说明新工具影响了旧能力
3. 同时可以在 `eval_set_v1.jsonl` 里增加新 case 覆盖新工具场景
4. `rerun_failed_eval.py` 可以自动重跑因网络问题失败的 case，减少人工成本

这让后续开发从「感觉能跑」变成「有量化证据地迭代」。

---

## 五、本周总结

Week 10 最大的收获是：**Agent 不能只看「能不能回答」，还要看「回答是否来自真实工具结果」**。

LangChain Case1 是典型反例：工具调用失败，Agent 仍然生成了完整的 BTC 价格、市值和交易量数据。表面上回答完整，实际上是编造的。没有规则评估，这种失败很难被发现。

三版 Agent 的最终定位：

| 版本 | 定位 |
|------|------|
| LangGraph | 主线版本，继续扩展 |
| 手写版 | 可控基线，需修复边界错误处理 |
| LangChain ReAct | 失败模式对照组，不再主线维护 |

下周优先修复：

1. 手写版 `InvalidCoinError` 恢复路径
2. 边界 case 的「未找到」友好提示
3. LangGraph 输出中 `<think>` 泄露
4. Case14 的 max_steps 标注（改为 7）