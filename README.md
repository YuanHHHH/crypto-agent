# Crypto Agent

加密货币分析 Agent，支持实时价格查询、批量查询、市场概览和历史数据追踪。基于 FastAPI 构建 RESTful API，使用 CoinGecko 数据源。

学习项目，持续开发中。

## 功能

- 单币种实时价格查询（CoinGecko API）
- 多币种批量价格查询
- 全球市场概览（总市值、BTC/ETH 市占率、24h 变化）
- 价格历史记录（JSONL 持久化，支持按币种筛选）
- 自动生成 API 文档（FastAPI /docs）
- 自定义异常处理（InvalidCoinError 404、APIError 502）
- Pydantic 数据模型校验

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
```

CoinGecko Demo API Key 申请地址：https://www.coingecko.com/en/api

## 使用

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
| `/prices` | GET | 批量查询价格 | `/prices?coins=bitcoin,ethereum,solana` |
| `/market` | GET | 全球市场概览 | `/market` |
| `/history` | GET | 价格历史记录 | `/history?coin=bitcoin&limit=10` |

### 命令行模式

```bash
python -m src.main
```

### 运行测试

```bash
python -m pytest tests/ -v
```

## 项目结构

```
crypto-agent/
    .env                        # API Key（不提交）
    .gitignore
    README.md
    CHANGELOG.md
    requirements.txt
    src/
        api.py                  # FastAPI HTTP 接口入口
        main.py                 # 终端交互入口
        models.py               # Pydantic 数据模型
        exception_handler.py    # 全局异常处理
        tools/
            price.py            # 价格查询、批量查询、历史记录
            market.py           # 市场概览
        utils/
            config.py           # 配置常量（BASE_DIR、HISTORY_FILE）
            decorators.py       # retry 装饰器
            exceptions.py       # 自定义异常（APIError、InvalidCoinError）
    tests/
        test_price.py           # 业务逻辑测试
        test_api.py             # API 接口测试
    data/
        price_history.jsonl     # 价格历史数据
```

## 技术栈

- Python 3.9
- FastAPI + Uvicorn
- Pydantic
- Requests
- python-dotenv
- pytest

## 后续计划

- 接入 LLM（Claude/OpenAI），实现 AI 行情分析
- 添加 Streamlit 前端界面
- 接入交易所 API（Binance/OKX）
- 技术指标计算（RSI/MACD）
- Docker 容器化部署