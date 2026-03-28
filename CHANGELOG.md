# Changelog

## 2026-03-28 (Week 2 Day 5-6)

- BASE_DIR 重构，消除所有硬编码路径，HISTORY_FILE 从 config.py 动态生成
- 补全所有函数 docstring
- 更新 README 和 CHANGELOG
- .env 中移除 HISTORY_FILE，改由代码自动计算

## 2026-03-27 (Week 2 Day 4)

- 安装 httpx，支持 FastAPI TestClient
- 新增 tests/test_api.py，覆盖所有 API 接口（正常 + 异常场景）
- 测试覆盖：test_root, test_price, test_prices, test_market, test_history, test_price_invalid_coin

## 2026-03-26 (Week 2 Day 3)

- 学习 HTTP 状态码（200/400/404/500/502）
- 新增 src/exception_handler.py，全局异常处理
- InvalidCoinError 返回 404，APIError 返回 502
- retry 装饰器优化：InvalidCoinError 直接抛出不重试

## 2026-03-24 (Week 2 Day 2)

- 新增 src/models.py，定义 CoinPrice / MarketOverview / PriceHistory 数据模型
- 所有接口绑定 response_model，/docs 自动生成完整文档
- 修复字段名不一致问题（coin -> symbol）

## 2026-03-23 (Week 2 Day 1)

- 新增 /prices 批量查询接口（Query 参数 coins）
- 新增 /history 历史记录接口（Query 参数 coin + limit）
- CG_BASE_URL 移入 .env，消除 URL 硬编码
- HISTORY_FILE 移入 .env，消除路径硬编码

## 2026-03-22 (Week 1 Day 6)

- 新增全球市场概览功能（get_market_overview）
- 重构 retry 装饰器到 src/utils/decorators.py
- 新增自定义异常类（CryptoAgentError / APIError / InvalidCoinError）
- 新增交互式命令行菜单（main.py）
- 新增 pytest 单元测试（test_price.py）

## 2026-03-21 (Week 1 Day 5)

- 接入 CoinGecko Demo API（通过 header 认证）
- 实现单币种价格查询（get_crypto_price）
- 实现多币种批量查询（get_multiple_prices）
- 实现 JSONL 价格历史持久化（save_to_history / load_price_history）
- 使用 python-dotenv 管理 API Key

## 2026-03-15 (Week 1 Day 1-4)

- 初始化项目结构（src/tools, src/utils, tests, data）
- Python 基础复习：数据结构、文件 IO、CSV/JSON 读写
- 装饰器实现：@timer, @retry, @log_call
- Git 仓库搭建，.gitignore 配置
- 创建 GitHub 仓库 crypto-agent