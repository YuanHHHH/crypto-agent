# Week 11 Day 5：Multi-Agent Eval 对比报告

**实验日期**：2026-06-29
**实验目标**：验证 Multi-Agent 在不同复杂度任务中的表现，并比较单 LangGraph Agent、固定流程 Multi-Agent 与 Supervisor Multi-Agent 的执行差异。
**结论状态**：Day 5 验收完成。本轮不继续打磨 Agent 路由逻辑，已发现的问题记录为后续可选优化项。

---

## 1. 实验对象与方法

### 1.1 对比架构

| 架构 | 说明 |
|---|---|
| `langgraph_single_agent` | 单个 LangGraph Agent 同时承担工具选择、事实获取、分析与回答生成 |
| `fixed_flow_multi_agent` | 固定执行 `Researcher → Analyst → Reporter` |
| `supervisor_multi_agent` | Supervisor 根据共享 State 路由到 Researcher、Analyst、Reporter 或结束 |

### 1.2 评估维度

- **Rule Eval**：必要工具、工具字段、步骤上限、回答非空与错误标记。
- **Routing Trace**：记录 `agent_path`、工具调用和节点执行轨迹，验证是否按任务复杂度分派角色。
- **LLM-as-Judge**：已在原始 JSONL 记录中保留回答质量评分；本报告重点分析可复现的执行路径与规则结果。

### 1.3 测试集

共 4 个 case、12 次运行：

| Case | 问题类型 | 关键观察点 |
|---|---|---|
| 101 | BTC 当前价格查询 | Supervisor 是否跳过 Analyst |
| 102 | 加密市场整体概览 | 市场工具选择与重复调度 |
| 103 | BTC 价格、24h 涨跌与市场综合分析 | 多工具获取与完整三角色协作 |
| 104 | DeFi 知识库解释 | RAG 检索与资料型问题处理 |

---

## 2. 总体结果

| 架构 | Rule Pass | 通过率 | 主要表现 |
|---|---:|---:|---|
| 单 LangGraph Agent | 3 / 4 | 75% | 简单任务链路短；复杂分析时工具选择未满足预期 |
| 固定流程 Multi-Agent | 3 / 4 | 75% | 路径稳定、职责清晰；简单任务也会经过 Analyst |
| Supervisor Multi-Agent | 3 / 4 | 75% | 能跳过不必要角色；复杂任务工具覆盖最完整；存在重复 Researcher 调度风险 |

三种架构在这组小样本上的 Rule Pass 都是 75%，因此不能得出“Supervisor 整体通过率更高”的结论。真正的差异在于：**任务编排方式、工具选择完整度和失败模式不同。**

---

## 3. 分 Case 结果

### Case 101：BTC 当前价格是多少？

| 架构 | 工具调用 | Agent 路径 | Rule Pass |
|---|---|---|---|
| 单 LangGraph | `get_price` | 无角色拆分 | ✅ |
| 固定流程 Multi-Agent | `get_price` | `researcher → analyst → reporter` | ✅ |
| Supervisor Multi-Agent | `get_price` | `researcher → reporter` | ✅ |

**结论**

Supervisor 正确识别这是简单事实查询，在获取价格后跳过 Analyst，直接交给 Reporter 生成最终回答。

这证明动态路由有效，但不能把它表述为“Supervisor 一定更快”：Supervisor 本身仍需要多次协调决策。更准确的结论是：

> Supervisor 能减少不必要的业务分析角色，但是否更快、更省调用成本，取决于协调节点开销与任务复杂度。

---

### Case 102：现在加密市场整体行情如何？

| 架构 | 工具调用 | Agent 路径 | Rule Pass |
|---|---|---|---|
| 单 LangGraph | `get_market` | 无角色拆分 | ✅ |
| 固定流程 Multi-Agent | `get_market` | `researcher → analyst → reporter` | ✅ |
| Supervisor Multi-Agent | `get_market → get_market` | `researcher → researcher → analyst → reporter` | ❌ |

Supervisor 在已获取市场概览后再次派发 Researcher，导致 `get_market` 重复调用，并因总步骤超过测试上限而 Rule Eval 失败。

**失败分析**

- 根因不是 LangGraph 图连错，而是 Supervisor 的 LLM 路由对“已有市场数据是否足够”的判断存在波动。
- 当前 State 虽然保存了 `market_data`，但没有把“已调用工具”和“已完成的事实获取任务”显式建模为可强约束的路由状态。
- 当前 routing check 没有把“Researcher 不能重复超过一次”设为失败条件，因此该问题主要由步骤上限捕获。

**后续可选优化，不在本轮实现**

1. 在 State 中记录已调用工具或已完成任务；
2. 对同一工具设定重复调用上限；
3. 对 Supervisor 增加确定性规则兜底：已有满足需求的数据时，不再派发 Researcher。

---

### Case 103：分析一下 BTC 当前价格、24 小时涨跌和市场情况

| 架构 | 工具调用 | Agent 路径 | Rule Pass |
|---|---|---|---|
| 单 LangGraph | `analyze_coin` | 无角色拆分 | ❌ |
| 固定流程 Multi-Agent | `get_price → get_market` | `researcher → analyst → reporter` | ❌ |
| Supervisor Multi-Agent | `get_price → get_coin_detail → get_market` | `researcher → analyst → reporter` | ✅ |

Supervisor Multi-Agent 是本 case 中唯一满足全部预期工具与字段要求的实现：

- `get_price`：BTC 当前价格与 24h 涨跌；
- `get_coin_detail`：BTC 市值、成交量、24h 高低点等单币数据；
- `get_market`：全市场市值、交易量、BTC Dominance 等市场概览；
- `Researcher → Analyst → Reporter`：事实获取、分析、报告职责分离。

**结论**

对于同时需要“单币实时数据 + 单币详情 + 市场概览 + 解释性分析”的复杂任务，Supervisor 路由下的 Researcher 在本次运行中选择了最完整的工具组合。

固定流程版本失败并不表示其架构不成立，而是说明 Researcher 的单次工具规划仍存在随机性：本次未选择 `get_coin_detail`，因而缺少测试要求的单币市值等字段。

---

### Case 104：请用知识库解释什么是 DeFi

| 架构 | 工具调用 | Agent 路径 | Rule Pass |
|---|---|---|---|
| 单 LangGraph | `search_rag × 3` | 无角色拆分 | ✅ |
| 固定流程 Multi-Agent | `search_rag` | `researcher → analyst → reporter` | ✅ |
| Supervisor Multi-Agent | `search_rag` | `researcher → reporter` | ✅ |

**结论**

三种架构都完成了规则要求的知识库检索。单 Agent 出现三次检索，说明其 Tool → Think 循环可以继续补检索，但也带来调用次数不可控的问题。固定流程和 Supervisor 版本均只进行一次检索，链路更可控。

由于 RAG 召回结果会受检索排序、上下文和模型调用随机性影响，单次实验不足以据此判断哪种架构在知识问答质量上绝对更优。该 case 更适合证明：

> 单 Agent 更容易形成多轮自我修正；固定流程 Multi-Agent 更强调流程边界与调用可控性；Supervisor 可以根据任务复杂度选择是否进入 Analyst。

---

## 4. 关键结论

### 4.1 Multi-Agent 不是单 Agent 的替代品

简单价格查询中，单 Agent 的链路最短；固定流程 Multi-Agent 存在明显的过度编排；Supervisor 能跳过 Analyst，但仍有协调调用开销。

因此，简单事实查询优先使用单 Agent 或轻量路由更合理。

### 4.2 Supervisor 的价值在复杂任务编排

复杂 BTC 分析中，Supervisor Multi-Agent 以完整工具组合通过 Rule Eval，并形成 Researcher、Analyst、Reporter 的职责分离。

它的主要价值不是“必然更高分”，而是：

- 将数据获取、分析推断、面向用户表达拆开；
- 使每个角色的 prompt 与工具集更聚焦；
- 能根据 State 动态跳过非必要角色；
- 为复杂任务提供可追踪的路由过程。

### 4.3 Supervisor 仍需要工程化约束

Case 102 的重复 `get_market` 表明，仅依赖 LLM 输出路由目标仍可能出现重复调度。

当前版本已经具备：

- `route_count` / `max_route_count` 防循环保险；
- `final_report` 生成后强制 `END`；
- 非法路由值校验；
- State 驱动的路由上下文。

后续若进入生产级迭代，再补充任务完成标记、工具去重和规则路由兜底即可。当前阶段不继续扩展，避免在项目冻结前陷入功能打磨。

---

## 5. 面试表达版本

> 我在同一套加密市场问题上对比了单 LangGraph Agent、固定流程 Multi-Agent 和 Supervisor Multi-Agent，并通过 Rule Eval、LLM-as-Judge 和路由轨迹共同评估。
>
> 结果显示：简单价格查询中，固定流程会产生过度编排，Supervisor 能跳过 Analyst，但协调节点本身仍有开销；复杂市场分析中，Supervisor 版能更完整地选择价格、单币详情和全市场工具，并通过 Researcher、Analyst、Reporter 的职责隔离输出结构化报告。
>
> 同时 Eval 也暴露了 Supervisor 的失败模式：市场概览任务中曾重复派发 Researcher，导致重复调用工具和步骤超限。因此我没有把 Multi-Agent 描述为万能方案，而是将其定位为复杂任务的可解释编排机制，并为后续的工具去重和规则兜底留下扩展点。

---

## 6. Day 5 验收

- [x] 建立独立 Multi-Agent Eval 测试集；
- [x] 对比单 LangGraph、固定流程 Multi-Agent、Supervisor Multi-Agent；
- [x] 记录工具调用、Agent 路径与路由轨迹；
- [x] 识别简单任务过度编排、Supervisor 重复调度、复杂任务工具选择不足等失败模式；
- [x] 形成可复用的对比结论与面试表达；
- [x] Day 5 完成，不再进行本轮 Agent 逻辑打磨。

---

## 7. 相关文件

```text
data/eval/eval_set_multi_agent_v1.jsonl
data/eval/eval_result_multi_agent_v1.jsonl
scripts/run_multi_agent_eval.py
docs/week11_multi_agent_eval.md
```
