# Crypto Agent

加密货币分析 Agent，支持实时价格查询和市场概览。学习项目，持续开发中。

## 功能

- 单币种实时价格查询（CoinGecko API）
- 多币种批量价格查询
- 全球市场概览（总市值、BTC/ETH 市占率）
- 价格历史记录（JSONL 持久化）

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
```

## 使用
```bash
python -m src.main
```

## 项目结构
```
crypto-agent/
    src/
        main.py              # 入口，交互式菜单
        tools/
            price.py          # 价格查询、历史记录
            market.py         # 市场概览
        utils/
            config.py         # 配置常量
            decorators.py     # retry 装饰器
            exception.py      # 自定义异常
    tests/
        test_price.py         # 单元测试
    data/                     # 价格历史数据
    requirements.txt
```