# Crypto Agent

加密货币 AI 分析 Agent，支持实时价格查询、市场数据分析、AI 智能行情分析、ReAct Agent 自主工具调用、多轮对话记忆、推理过程可视化。基于 FastAPI + MiniMax LLM + Streamlit 构建。

学习项目，持续开发中。

## 功能

- ReAct Agent 模式：LLM 自主决定调用哪个工具，支持多步推理
- Agent 对话记忆：支持多轮连续提问，理解上下文代词（如「那 ETH 呢」）
- Agent 推理过程可视化：Streamlit 展开每一步的 Thought / Action / Observation
- Agent 质量评估：批量测试 + 自动统计成功率、平均步数、兜底率、耗时
- 深度行情分析工具（analyze_coin）：内部调用 LLM，subagent 雏形
- 单币种/多币种实时价格查询（CoinGecko API）
- 单币种详细市场数据（市值、成交量、24h高低价、ATH）
- 全球市场概览（总市值、BTC/ETH 市占率、24h 变化）
- AI 智能行情分析（MiniMax M2.7 大模型，自动获取数据 + 生成分析报告）
- 多轮对话 CLI 工具（支持连续追问，LLM 保持上下文）
- Agent CLI 工具（自然语言提问，支持 reset 重置对话）
- Streamlit Web 界面（实时分析 + 市场概览 + 历史记录 + Agent 模式 + 推理过程展示）
- 价格历史记录（JSONL 持久化，支持按币种筛选）
- Agent 运行 Trace 日志（JSON 记录每次运行的完整轨迹）
- 自动生成 API 文档（FastAPI /docs）
- 自定义异常处理（InvalidCoinError 404、APIError 502）

## 界面截图

![Crypto Agent 界面](docs/screenshot.png)

## 安装

```bash
git clone https://github.com/YuanHHHH/crypto-agent.git
cd crypto-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

在项目根目录创建 `.env` 文件：

```
CG_API=你的CoinGecko_Demo_API_Key
CG_BASE_URL=https://api.coingecko.com/api/v3
LLM_API_KEY=你的MiniMax_API_Key
LLM_BASE_URL=https://api.minimaxi.com/v1/chat/completions
LLM_MODEL=MiniMax-M2.7
```

API Key 申请：
- CoinGecko: https://www.coingecko.com/en/api
- MiniMax: https://platform.minimaxi.com

## 使用

### 启动 Streamlit 界面（推荐）

```bash
streamlit run src/app.py
```

启动后浏览器自动打开 http://localhost:8501，界面包含三个页面：

- 「实时分析」：选择币种查询价格、AI 分析、Agent 模式（自然语言提问 + 推理过程可视化）
- 「市场概览」：全球市场数据仪表盘 + 单币种详情
- 「历史记录」：历史查询记录表格，支持筛选和条数控制

### Agent CLI 模式

```bash
python -m src.agent_cli
```

输入自然语言问题，Agent 自主决定调用工具并回答。支持多轮连续对话。
- 输入 `reset` 清空对话历史开启新对话
- 输入 `exit` 退出

### Agent 批量测试 + 质量评估

```bash
python -m scripts.batch_test
```

运行 10 个预设测试用例，自动生成 trace 日志并输出评估报告，包含：
- 总运行次数
- 成功率
- 平均步数
- 平均耗时
- 格式错误率
- 兜底率

单独跑 eval：

```bash
python -m src.agent.eval
```

### 启动 API 服务

```bash
uvicorn src.api:app --reload
```

启动后访问 http://127.0.0.1:8000/docs 查看交互式 API 文档。

### API 接口

| 接口 | 方法 | 说明 | 示例 |
|------|------|------|------|
| `/` | GET | 健康检查 | `/` |
| `/price/{coin}` | GET | 查询单个币种价格 | `/price/bitcoin` |
| `/prices` | GET | 批量查询价格 | `/prices?coins=bitcoin,ethereum` |
| `/market` | GET | 全球市场概览 | `/market` |
| `/coin_market` | GET | 单币种市场数据 | `/coin_market?coin=bitcoin` |
| `/history` | GET | 价格历史记录 | `/history?coin=bitcoin&limit=10` |
| `/analyze/{coin}` | GET | AI 智能行情分析 | `/analyze/bitcoin` |

### 运行测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
crypto-agent/
    .env                        # API Key 配置（不提交）
    .gitignore
    README.md
    CHANGELOG.md
    TROUBLESHOOTING.md          # 开发踩坑记录
    requirements.txt
    docs/
        screenshot.png          # 界面截图
    scripts/
        batch_test.py           # Agent 批量测试脚本
    src/
        app.py                  # Streamlit 前端入口
        api.py                  # FastAPI HTTP 接口入口
        main.py                 # 终端交互入口
        agent_cli.py            # Agent 命令行入口
        models.py               # Pydantic 数据模型
        exception_handler.py    # 全局异常处理
        agent/
            __init__.py
            agent_runner.py     # ReAct Agent 核心循环 + 对话记忆 + step_log
            tool_registry.py    # 工具注册和管理
            parser.py           # LLM 输出解析器（纯函数）
            prompts.py          # Agent system prompt
            trace.py            # 运行轨迹记录
            eval.py             # Agent 质量评估
        tools/
            price.py            # 价格查询、批量查询、历史记录
            market.py           # 市场概览、单币种市场数据
            analyzer.py         # 深度分析（内部调用 LLM）
            llm_client.py       # MiniMax LLM API 调用封装
        utils/
            config.py           # 配置常量（BASE_DIR、HISTORY_FILE、TRACE_FILE）
            decorators.py       # retry 装饰器
            exceptions.py       # 自定义异常（APIError、InvalidCoinError）
    tests/
        test_price.py           # 业务逻辑测试
        test_api.py             # API 接口测试
        test_analyze.py         # AI 分析测试
    data/
        price_history.jsonl     # 价格历史数据
        traces/
            trace_record.jsonl  # Agent 运行轨迹日志
```

## 技术栈

- Python 3.9
- FastAPI + Uvicorn
- Streamlit
- Pydantic
- Requests
- python-dotenv
- pytest + httpx
- MiniMax M2.7 LLM API

## Agent 架构

```
用户输入
  ↓
AgentRunner.run()
  ↓
拼接 chat_history + 用户问题    ← 多轮对话记忆
  ↓
构建 system prompt（含工具描述）
  ↓
while 循环（max_steps=5）：
  ├→ 发送 conversation 给 LLM
  ├→ parse_llm_output 解析为结构化 dict
  ├→ type == "action"       → 调用 ToolRegistry.call() → 追加 Observation
  ├→ type == "final_answer" → 返回答案，break
  ├→ type == "error"        → 反馈给 LLM 重试（JSON 解析失败）
  └→ type == "no_parsed"    → 兜底分支
  ├→ 每一步记录到 step_log（供可视化使用）
  ↓
trace_record 写入 trace_record.jsonl
  ↓
更新 chat_history
  ↓
返回 (final_answer, step_log)
```

### 核心模块

- **ToolRegistry**：工具注册表，支持动态注册和调用。加新工具只需调用 `register()`，AgentRunner 零改动
- **parse_llm_output**：纯函数解析器，把 LLM 的字符串输出转成结构化 dict。如果未来切换到 Function Calling 格式，只需重写这一个函数
- **AgentRunner**：ReAct 主循环，包含 chat_history（对话记忆）、step_log（过程记录）、trace 记录
- **trace.py**：可观测性层，记录每次运行的完整轨迹到 JSONL
- **eval.py**：质量评估层，读取 trace 统计核心指标

### 已注册工具（4 个）

- `get_price`：查询币种实时价格
- `get_market`：查询全球市场概览
- `get_coin_detail`：查询币种详细市场数据
- `analyze_coin`：深度行情分析（内部调用 LLM 生成报告，subagent 雏形）

## 开发进度

- Week 1: Python 基础、Git、CoinGecko API 接入、FastAPI 基础接口
- Week 2: Pydantic 模型、异常处理、TestClient 测试、代码重构
- Week 3: MiniMax LLM API 接入、AI 分析功能、多轮对话、/analyze 接口
- Week 4: Streamlit 前端界面（三页面 + 仪表盘 + 历史记录 + 错误处理 + 缓存）
- Week 5: 手写 ReAct Agent（ToolRegistry + AgentRunner + Trace + CLI + Streamlit 集成）
- Week 6: Agent 深化（analyze 工具 + 对话记忆 + parser 抽取 + 质量评估 + 推理过程可视化）

## 后续计划

- LangChain / LangGraph 框架重构
- RAG 知识库（加密研报检索 + ChromaDB）
- 接入交易所 API（Binance/OKX）
- 技术指标计算（RSI/MACD）
- Docker 容器化部署
- MCP 协议集成
- 多 Agent 协作 / Subagent 架构

## Week 7: LangChain 重构
 
本周用 LangChain 0.3.28 重构了手写的 ReAct Agent，对比两种实现在同一个模型（MiniMax-M2.7）、同一套工具、同一个任务上的表现。
 
### 实现
 
使用 LangChain 的 `create_react_agent` + `AgentExecutor` 替代 Week 5-6 的手写 while 循环：
 
- Prompt：自定义中文 PromptTemplate，保留了手写版的 MiniMax 适配规则（禁止 tool_call 块、禁止代码块围栏、Action Input 纯文本约束）
- 工具：用 `@tool` 装饰器包装原有 4 个函数，加 `_sanitize` 防 LLM 参数污染
- 记忆：`ConversationBufferMemory` 集成多轮对话，通过 `chat_history` 占位符和 prompt 对接
- 观测：自定义 `TraceCallback`（继承 `BaseCallbackHandler`）实现 trace 记录，字段结构与手写版一致，可共用 `eval.py`
### 测试对比
 
在 MiniMax-M2.7 上实测三轮对话：
 
- 手写版（Week 6 eval）：成功率 84.4%，平均步数 1.59，兜底率 15.6%
- LangChain 版：工具调用全部成功，但最终答案全部被 ReActOutputParser 判定为 iteration_limit
根因：MiniMax 拿到工具结果后不写 `Final Answer:` 前缀，LangChain 的严格 parser 识别失败；而手写版 parser 有「长文本兜底」策略，在弱模型上更鲁棒。
 
详细分析见 [docs/custom_vs_langchain.md](docs/custom_vs_langchain.md)。
 
### 关键收获
 
- AgentExecutor 源码级理解：`_call` 主循环、`_should_continue` 终止条件、`_take_next_step` 单步执行、`return_direct` fast-path、`early_stopping_method` 兜底
- LangChain 10 层抽象：Runnable、Messages、Prompts、Parsers、Tools、Memory、Retrievers、Chains、Agents、Callbacks
- 框架 vs 手写的真实 tradeoff：框架不是银弹，弱模型场景下手写的针对性适配可能更有效
### 代码变化
 
- 新增 `src/agent/langchain_agent.py`：LangChain Agent 入口
- 新增 `src/agent/langchain_tools.py`：@tool 包装 + sanitize
- 新增 `src/agent/langchain_callbacks.py`：TraceCallback 实现
- 新增 `docs/custom_vs_langchain.md`：手写 vs 框架对比
- 新增 `docs/week7_notes.md`：Week 7 学习笔记（6 个核心问题）
- 更新 `docs/TROUBLESHOOTING.md`：7 条新条目（#15-21）
