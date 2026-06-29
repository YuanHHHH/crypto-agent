# 题 6：Multi-Agent 设计与协作

## 1. 两分钟回答框架

我在 crypto-agent 里实现并对比了固定流程 Multi-Agent 和 Supervisor Multi-Agent 两种协作方式。

角色按职责划分为四类：Researcher 只负责调用价格、市场和知识库工具获取可验证事实；Analyst 只根据已有事实区分数据、推断、风险和信息缺口；Reporter 不调用工具，只生成面向用户的最终报告；Supervisor 不做分析，也不调工具，只根据共享 State 决定下一步交给谁。

我先做了固定流程 `Researcher → Analyst → Reporter`，它作为稳定基线，优点是可预测、容易调试，适合需要标准化完整报告的复杂问题。但缺点是简单问题也会经过 Analyst，存在过度编排。

之后我加了 Supervisor 路由。它读取 `market_data`、`research_notes`、`analysis_result`、`final_report`、错误信息和路由次数，并通过结构化 JSON 输出 `next_agent`。Python 对结果做白名单校验，再用 LangGraph `Command(goto=...)` 跳转。为了避免循环，我加了最终报告生成后强制 END、最大路由次数、非法路由值校验三层保护。

Eval 结果显示：简单价格查询里，Supervisor 能走 `Researcher → Reporter` 并跳过 Analyst；复杂 BTC 市场分析里，Supervisor 能完成 `get_price + get_coin_detail + get_market`，再走完整三角色路径。但 Eval 也暴露过市场概览任务重复派 Researcher、重复调用工具的问题。因此我的结论不是 Multi-Agent 一定更好，而是它适合复杂、步骤不固定、需要职责隔离和可解释编排的任务；简单事实查询仍然优先单 Agent 或轻量流程。

---

## 2. 三种架构模式对比

| 模式 | 核心特点 | 适用场景 | 风险 |
|---|---|---|---|
| Supervisor | 中央协调者按 State 调度专家 | 步骤不固定、存在条件分支的复杂任务 | 路由不稳定、循环、协调开销 |
| Hierarchical | 多层 Supervisor 分层拆解 | 长链路、多团队、多子任务 | 摘要失真、延迟高、调试难 |
| Swarm | Agent 直接 handoff，无中心调度 | 角色对等、目标开放的协作 | 上下文丢失、责任边界不清、难收敛 |

本项目选择 Supervisor，因为“先查数据、是否分析、是否输出报告”是清晰的动态决策链；Hierarchical 对当前三角色任务过重，Swarm 的无中心 handoff 也不利于稳定控制与 Eval。

---

## 3. 追问：为什么不让一个 Agent 调所有工具？

单 Agent 的优点是链路短、简单任务成本低。但工具、分析和报告都集中在一个 Prompt 时，工具选择、事实处理和表达容易互相干扰。Multi-Agent 把 Researcher 的工具集限制在事实获取，把 Analyst 和 Reporter 与工具隔离，使复杂任务更容易定位错误、审计路由和扩展角色。

---

## 4. 追问：Agent 如何传递信息？

通过 LangGraph 共享 State，而不是只依赖消息历史。

- `market_data` 保存结构化价格、币种详情和市场总览；
- `research_notes` 保存 RAG 资料；
- `analysis_result` 保存分析结论；
- `final_report` 保存最终回答；
- `messages` 保留协议消息和工具调用轨迹。

这样 Analyst 和 Reporter 都读取明确字段，而不是从长消息历史中猜事实。

---

## 5. 追问：如何防止 Supervisor 死循环？

我做了三层保护：

1. `final_report` 生成后由 Python 强制 `END`；
2. State 记录每个阶段是否有产出，路由应向“数据 → 分析 → 报告”推进；
3. `route_count` 达到 `max_route_count` 后强制交给 Reporter 基于已有信息收敛。

此外还校验 JSON 是否可解析、`next_agent` 是否在允许白名单内。框架层的 recursion limit 只作为最终兜底，不替代业务状态机。

---

## 6. 追问：Eval 得到了什么结论？

我没有只评最终答案，而是组合了：

- Rule Eval：是否调用必要工具、工具字段是否齐全、是否步骤超限；
- LLM-as-Judge：准确性、完整性、相关性；
- Routing Trace：记录工具调用、角色路径和路由决策。

结果显示：Supervisor 能避免简单任务走完整固定流程，在复杂市场分析中工具覆盖更完整；但也出现过重复派发 Researcher 的失败案例。因此 Multi-Agent 的收益是职责隔离和复杂任务编排，不是无条件提升准确率或降低成本。
