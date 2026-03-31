# Crypto Agent

加密货币 AI 分析 Agent，支持实时价格查询、市场数据分析、AI 智能行情分析。基于 FastAPI + MiniMax LLM + Streamlit 构建。

学习项目，持续开发中。

## 功能

- 单币种/多币种实时价格查询（CoinGecko API）
- 单币种详细市场数据（市值、成交量、24h高低价、ATH）
- 全球市场概览（总市值、BTC/ETH 市占率、24h 变化）
- AI 智能行情分析（MiniMax M2.7 大模型，自动获取数据 + 生成分析报告）
- 多轮对话 CLI 工具（支持连续追问，LLM 保持上下文）
- Streamlit Web 界面（三个功能页面，支持开发模式切换）
- 价格历史记录（JSONL 持久化，支持按币种筛选）
- 自动生成 API 文档（FastAPI /docs）
- 自定义异常处理（InvalidCoinError 404、APIError 502）
- Pydantic 数据模型校验

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

- 「实时分析」：选择或输入币种，查询价格、触发 AI 智能分析
- 「市场概览」：全球市场数据仪表盘 + 单币种详情（st.metric 涨跌颜色）
- 「历史记录」：历史查询记录表格，支持按币种筛选和条数控制

侧边栏支持「开发模式/正常模式」切换，开发模式下显示完整错误信息。

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

### 命令行模式

```bash
python -m src.main
```

支持功能：查询价格、查看市场概览、AI 分析（自动获取数据 + LLM 生成报告）。

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
    requirements.txt
    docs/
        screenshot.png          # Streamlit 界面截图
    src/
        app.py                  # Streamlit 前端入口
        api.py                  # FastAPI HTTP 接口入口
        main.py                 # 终端交互入口
        models.py               # Pydantic 数据模型
        exception_handler.py    # 全局异常处理
        tools/
            price.py            # 价格查询、批量查询、历史记录
            market.py           # 市场概览、单币种市场数据
            analyzer.py         # 数据组装 + prompt 构建
            llm_client.py       # MiniMax LLM API 调用封装
        utils/
            config.py           # 配置常量（BASE_DIR、HISTORY_FILE）
            decorators.py       # retry 装饰器
            exceptions.py       # 自定义异常（APIError、InvalidCoinError）
    tests/
        test_price.py           # 业务逻辑测试
        test_api.py             # API 接口测试
        test_analyze.py         # AI 分析测试
    data/
        price_history.jsonl     # 价格历史数据
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

## 开发进度

- Week 1: Python 基础、Git、CoinGecko API 接入、FastAPI 基础接口
- Week 2: Pydantic 模型、异常处理、TestClient 测试、代码重构
- Week 3: MiniMax LLM API 接入、AI 分析功能、多轮对话、/analyze 接口
- Week 4: Streamlit 前端界面（三页面 + 仪表盘 + 历史记录 + 错误处理 + 缓存）

## 后续计划

- 手写 ReAct Agent（Tool Use 机制）
- 接入交易所 API（Binance/OKX）
- 技术指标计算（RSI/MACD）
- RAG 知识库（加密研报检索）
- Docker 容器化部署