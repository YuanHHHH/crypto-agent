# Crypto Agent

加密货币 AI 分析 Agent，支持实时价格查询、市场数据分析、AI 智能行情分析、ReAct Agent 自主工具调用、多轮对话记忆、RAG 知识库检索、推理过程可视化、LangGraph 状态图编排、Function Calling 工具调用、interrupt/resume 人工审核。基于 MiniMax LLM + LangGraph + LangChain 生态 + Streamlit + Chroma 构建。

学习项目，持续开发中。

## 三版 Agent 实现

本项目包含同一业务（加密货币分析）的三种 Agent 实现，用于对比不同抽象层级和工具调用协议的差异：

| 版本 | 框架 | 工具调用协议 | 成功率 | 代码量 |
|------|------|-------------|--------|--------|
| 手写版（Week 5-6） | 纯 Python | ReAct 文本协议 | 84% | ~300 行 |
| LangChain 版（Week 7） | LangChain 0.3 | ReAct 文本协议 | 0%* | ~170 行 |
| LangGraph 版（Week 9） | LangGraph + LangChain 生态 | Function Calling | 100% | ~100 行 |

*LangChain 版成功率详见 [docs/three_versions_comparison.md](docs/three_versions_comparison.md)

## 功能

- LangGraph 状态图 Agent（主版本）：StateGraph + Function Calling + ToolNode + Checkpointer
- interrupt/resume 人工审核：工具调用前暂停等待用户确认
- Parallel tool calls：一次 LLM 推理同时调用多个工具
- Checkpointer 多轮对话：跨 invoke 状态持久化，支持会话恢复
- RAG 知识库检索：10 篇加密货币概念文档，Chroma 向量数据库
- Agent 智能路由：概念类走 RAG，实时数据走 API，复合问题串行调用
- Agent 质量评估：批量测试 + 三版对比 + 成功率/步数/耗时统计
- 深度行情分析工具：内部调用 LLM，subagent 雏形
- 单币种/多币种实时价格查询（CoinGecko API）
- 全球市场概览 + 单币种详细市场数据
- Streamlit Web 界面 + Agent CLI + FastAPI API

## 安装

```bash
git clone https://github.com/YuanHHHH/crypto-agent.git
cd crypto-agent
python3 -m venv .venv
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
```

## 使用

```bash
python -m src.agent.langgraph_agent    # LangGraph Agent CLI（推荐）
python scripts/compare_agents.py       # 三版对比测试
streamlit run src/app.py               # Streamlit 界面
python -m src.agent_cli                # 手写版 Agent CLI
uvicorn src.api:app --reload           # API 服务
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

## 后续计划

- Week 10: Eval 体系升级（标注集 + LLM-as-judge）
- Week 11-12: 多交易所聚合 + 技术指标 + 链上数据
- Week 13-14: Multi-Agent（Researcher + Analyst + Reporter）
- Week 15-17: Docker + LangSmith + Streaming + v2.0 发布