# Crypto Agent

加密货币 AI 分析 Agent，支持实时价格查询、市场数据分析、AI 智能行情分析、ReAct Agent 自主工具调用、多轮对话记忆、RAG 知识库检索、推理过程可视化、LangGraph 状态图编排、Function Calling 工具调用、interrupt/resume 人工审核。基于 MiniMax LLM + LangGraph + LangChain 生态 + Streamlit + Chroma 构建。

学习项目，持续开发中。

## 三版 Agent 实现

本项目包含同一业务（加密货币分析）的三种 Agent 实现，用于对比不同抽象层级和工具调用协议的差异。v0.9 基于 12 个非 context 评估 case 的测试结果：

| 版本 | 框架 | 工具调用协议 | Eval 规则通过率 | judge avg（acc/comp/rel）|
|------|------|-------------|----------------|------------------------|
| 手写版（Week 5-6） | 纯 Python | ReAct 文本协议 | 83% (10/12) | 8.9 / 9.4 / 9.7 |
| LangGraph 版（Week 9） | LangGraph + LangChain 生态 | Function Calling | 75% (9/12) | 8.9 / 8.9 / 9.8 |
| LangChain 版（Week 7） | LangChain 0.3 | ReAct 文本协议 | 33% (4/12) | 7.6 / 10.0 / 9.8* |

*LangChain 版 judge 分数仅基于 5 个执行成功的 case，其余因 ReAct parser 格式失败、工具调用失败或运行失败跳过。详见 [docs/failure_analysis.md](docs/failure_analysis.md)

说明：Eval 规则通过率指 `eval_rules.py` 中 `overall_pass=True` 的比例，主要衡量工具调用路径、字段完整性、步数限制、错误标记和关键词检查；judge avg 衡量成功输出后的语义质量。

从 Week 10 评估结果看，手写版在当前 12 个非 context case 中 Eval 规则通过率最高，但 LangGraph 版在工具调用协议、并行工具调用、状态管理和后续扩展性上更适合作为主线版本。LangGraph 的失败主要来自工具选择偏差（Case2）和步数口径不一致（Case14）；手写版的失败集中在边界错误直接冒泡（Case9/10）；LangChain ReAct 版在 MiniMax-M2.7 上存在明显格式遵从问题，工具调用场景容易出现 `_Exception`、parser error 或虚构数据，因此保留为失败模式对照组。

## 功能

- LangGraph 状态图 Agent（主版本）：StateGraph + Function Calling + ToolNode + Checkpointer
- interrupt/resume 人工审核：工具调用前暂停等待用户确认
- Parallel tool calls：一次 LLM 推理同时调用多个工具
- Checkpointer 多轮对话：跨 invoke 状态持久化，支持会话恢复
- RAG 知识库检索：10 篇加密货币概念文档，Chroma 向量数据库
- Agent 智能路由：概念类走 RAG，实时数据走 API，复合问题串行调用
- **Eval 体系（v0.9 新增）**：15 个标注 case + 规则评估 + LLM-as-judge 三维评分 + 失败自动分类重跑
- 深度行情分析工具：内部调用 LLM，subagent 雏形
- 单币种/多币种实时价格查询（CoinGecko API）
- 全球市场概览 + 单币种详细市场数据
- Streamlit Web 界面 + Agent CLI + FastAPI API

## 安装

```bash
git clone https://github.com/YuanHHHH/crypto-agent.git
cd crypto-agent
python3.11 -m venv .venv        # 需要 Python 3.11+（LibreSSL 问题见 TROUBLESHOOTING.md）
source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_rag_index.py  # 首次使用需构建向量数据库
```

`.env` 配置：
```
CG_API=你的CoinGecko_Demo_API_Key
CG_BASE_URL=https://api.coingecko.com/api/v3
LLM_API_KEY=你的MiniMax_API_Key
LLM_BASE_URL=https://api.minimaxi.com/v1/chat/completions
LLM_MODEL=MiniMax-M2.7
KIMI_API_KEY=你的Kimi_API_Key          # eval judge 用
KIMI_BASE_URL=https://api.moonshot.cn/v1/chat/completions
```

## 使用

```bash
python -m src.agent.langgraph_agent    # LangGraph Agent CLI（推荐）
python scripts/run_eval.py             # 运行评估集（三版对比）
python scripts/rerun_failed_eval.py    # 重跑失败样本
streamlit run src/app.py               # Streamlit 界面
python -m src.agent_cli                # 手写版 Agent CLI
uvicorn src.api:app --reload           # API 服务
```

## Eval 体系

v0.9 新增轻量 Eval 体系，支持对三版 Agent 做持续回归测试。

**评估集**：`data/eval/eval_set_v1.jsonl`，15 个 case，覆盖四类能力：

| 类型 | case 数 | 说明 |
|------|--------|------|
| basic | 5 | 单工具、多工具、无工具调用 |
| context | 3 | 多轮对话上下文记忆 |
| boundary | 4 | 拼写错误、不存在币种、超出范围问题、模糊问题 |
| complex | 3 | 概念解释 + 实时数据组合、多工具串行 |

**双轨制评估**：

- 规则评估：工具路径、字段完整性、步数、错误标记（确定性，零成本）
- LLM-as-judge：accuracy / completeness / relevance 三维评分（语义质量）

**运行方式**：

```bash
python scripts/run_eval.py             # 完整跑一遍
python scripts/rerun_failed_eval.py    # 只重跑失败样本
```

## 技术栈

LangGraph + LangChain 0.3 + MiniMax M2.7（Function Calling） + ChromaDB + sentence-transformers + FastAPI + Streamlit + Pydantic + pytest

## Agent 架构（LangGraph 版）

```
用户输入 → graph.stream(messages, config={thread_id})
  ↓
think_node → llm_with_tools.invoke(messages)
  ↓
conditional_edge → tool_calls 存在？
  ├→ 是 → interrupt_node（人工审核）
  │         ├→ yes → tool_node → 回到 think_node
  │         └→ no  → reject_node → END
  └→ 否 → END（content = 最终答案）
  ↓
Checkpointer 自动持久化 State
```

## 开发进度

- Week 1-2: Python + FastAPI + CoinGecko API
- Week 3: MiniMax LLM 接入 + AI 分析
- Week 4: Streamlit 前端
- Week 5-6: 手写 ReAct Agent + 质量评估
- Week 7: LangChain 重构 + 框架对比
- Week 8: RAG 知识库 + Agent 路由
- Week 9: LangGraph + Function Calling + Checkpointer + interrupt/resume + 三版对比
- **Week 10: Eval 体系（标注集 + 规则评估 + LLM-as-judge + 失败分类重跑）** ← 当前

## 后续计划

- Week 11-12: 多交易所聚合 + 技术指标 + 链上数据
- Week 13-14: Multi-Agent（Researcher + Analyst + Reporter）
- Week 15-17: Docker + LangSmith + Streaming + v2.0 发布