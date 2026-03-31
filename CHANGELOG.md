# Changelog

## Week 4: Streamlit 前端界面

### Day 1

- 新增 src/app.py，Streamlit 前端入口
- 实现单币种价格查询页面（st.text_input + st.button + st.spinner）
- st.set_page_config 设置页面标题和 wide 布局

### Day 2

- 加入 st.selectbox 币种下拉选择（预设 6 个主流币种）
- 加入 st.text_input 自定义币种输入
- 接入 AI 分析功能，st.markdown 渲染 LLM 返回的分析报告
- 加入 st.sidebar 侧边栏（项目信息、版本号、GitHub 链接）

### Day 3

- 新增 st.tabs 多标签页：「实时分析」「市场概览」
- 市场概览页面：st.metric 展示总市值、BTC 市占率、24h 市值变化（delta 涨跌颜色）
- 单币种详情：st.columns 两列布局展示价格、涨跌、市值、高低价、ATH
- 新增 st.expander 折叠面板展示总成交量等补充数据

### Day 4

- 新增「历史记录」tab，st.dataframe 展示 JSONL 历史数据
- 支持按币种筛选（st.selectbox）和条数控制（st.number_input）
- 加入 @st.cache_data 缓存：市场概览 ttl=60s，历史记录 ttl=30s

### Day 5

- 异常处理分类：InvalidCoinError / APIError / Exception 分别给出不同提示
- 加入 st.session_state 记住用户上次选择的币种
- 加入 st.radio 开发模式/正常模式切换
- 开发模式下用 st.exception 显示完整 Python traceback
- 加入 st.toast / st.success 操作反馈提示

### Day 6

- 更新 requirements.txt，加入 streamlit
- 修复依赖版本冲突（packaging 版本与 streamlit 不兼容）
- 修复 test_get_crypto_price_invalid 测试（加入 pytest.raises）
- 从零验证：删除 .venv 重建，pip install，全流程跑通
- pytest 12 个测试全部通过
- 补充 app.py 模块级 docstring

### Day 7

- 更新 README：加入 Streamlit 启动说明、三个 tab 功能描述、界面截图
- 更新项目结构：加入 src/app.py 和 docs/screenshot.png
- 更新 CHANGELOG
- GitHub 发布 v0.3 tag

## 2026-03-28 (Week 3 Day 5-7)

- 新增 /analyze/{coin} 接口，AI 智能行情分析
- 新增 Analysis Pydantic 模型（symbol + content）
- 新增 CoinMarket Pydantic 模型，/coin_market 接口绑定 response_model
- 优化 system prompt，输出结构更稳定、分析更专业
- 优化 analyzer.py 数据格式，拆分字段传入 LLM
- 新增 test_analysis 和 test_coin_market 测试用例
- 更新 README 和 CHANGELOG

## 2026-03-28 (Week 3 Day 4)

- 新增 src/tools/analyzer.py，组装价格 + 市场数据生成 prompt
- 新增 src/tools/llm_client.py，封装 MiniMax LLM API 调用
- main.py 新增 AI 分析菜单选项，集成 analyzer + llm_client
- 新增 /coin_market 接口，查询单币种详细市场数据
- 新增 get_coin_market 函数（CoinGecko /coins/markets 接口）

## 2026-03-28 (Week 3 Day 3)

- 实现多轮对话 CLI 工具，messages 列表追加历史消息
- 支持连续追问，LLM 保持上下文
- 用户输入「没有了」退出对话

## 2026-03-28 (Week 3 Day 2)

- 设计 system prompt，LLM 扮演加密货币数据分析师
- 实现结构化 JSON 输出，json.loads 验证解析
- 处理 LLM 返回的 think 标签、markdown 标记、Extra data

## 2026-03-28 (Week 3 Day 1)

- 接入 MiniMax M2.7 LLM API（OpenAI 兼容格式）
- 理解 messages 格式（system/user/assistant）
- API key 移入 .env，消除硬编码
- 测试 temperature 参数对输出随机性的影响

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

## 2026-03-22 (Week 1)

- 接入 CoinGecko Demo API（通过 header 认证）
- 实现单币种价格查询（get_crypto_price）
- 实现多币种批量查询（get_multiple_prices）
- 实现 JSONL 价格历史持久化（save_to_history / load_price_history）
- 新增全球市场概览功能（get_market_overview）
- 重构 retry 装饰器到 src/utils/decorators.py
- 新增自定义异常类（CryptoAgentError / APIError / InvalidCoinError）
- 新增 FastAPI 基础接口（/, /price/{coin}, /market）
- 新增交互式命令行菜单（main.py）
- 新增 pytest 单元测试（test_price.py）
- Git 仓库搭建，.gitignore 配置
- 创建 GitHub 仓库 crypto-agent