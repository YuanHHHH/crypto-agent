# Changelog

## 2026-03-22

- 新增全球市场概览功能（get_market_overview）
- 重构 retry 装饰器到 utils/decorators.py
- 新增自定义异常类（APIError、InvalidCoinError）
- 新增交互式命令行菜单
- 新增 pytest 单元测试

## 2026-03-21

- 接入 CoinGecko Demo API
- 实现单币种和批量价格查询
- 实现 JSONL 价格历史持久化
- 使用 python-dotenv 管理 API Key

## 2026-03-15

- 初始化项目结构
- 完成 hardcode 版 price.py
- 配置 Git 仓库和 .gitignore