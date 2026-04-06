# Changelog

## Week 5: 手写 ReAct Agent

### Day 1

- 创建 src/agent/ 模块目录
- 新增 prompts.py，设计 Agent system prompt 模板
- 定义 LLM 输出格式：Thought/Action/Action Input/Final Answer
- 学习 ReAct 论文核心思想和 OpenAI Function Calling 文档

### Day 2

- 新增 tool_registry.py，实现 ToolRegistry 类
- 三个方法：register（注册工具）、call（调用工具）、get_tool_descriptions（生成工具描述）
- 注册 3 个工具：get_price、get_market、get_coin_detail
- 工具存储为函数引用而非字符串，支持动态注册

### Day 3

- 新增 agent_runner.py，实现 AgentRunner 核心 ReAct 循环
- LLM 自主决定调用工具，代码解析 Thought/Action/Action Input 并执行
- conversation 每轮累加 LLM 回复和 Observation，保持上下文连贯
- 修改 llm_client.py 支持传入 system_prompt 参数
- 解决 system prompt 冲突：Agent prompt 和分析师 prompt 分离

### Day 4

- 5 个测试用例验证 Agent 行为：
  - 单币种价格查询：正常调用 get_price
  - 市场概览查询：正常调用 get_market
  - 币种详情查询：正常调用 get_coin_detail
  - 非工具问题（你好）：直接 Final Answer，不调用工具
  - 多币种对比：触发多步工具调用
- 处理 LLM 输出格式不稳定：
  - LLM 一次输出多个 Action：只取第一行 Action Input 解析
  - JSON 解析失败：try/except 兜底，提示 LLM 重新输出
  - 工具名不存在：检查 registry 后告知 LLM 可用工具
  - 格式完全不对：兜底直接返回原始内容

### Day 5

- 新增 trace.py，记录 Agent 每次运行的完整轨迹
- Trace 内容：用户问题、最终答案、完整对话、总步数、总耗时
- 保存为 JSONL 格式到 data/traces/
- 新增 agent_cli.py，Agent 命令行交互入口
- 支持连续提问，输入 exit 退出

### Day 6

- Agent 模式接入 Streamlit：新增「Agent 模式」按钮
- 用户输入自然语言问题，Agent 自主调用工具并返回结果
- 优化 prompts.py：
  - 加入「每次只调用一个工具」规则
  - 加入「不要编造数据，必须通过工具获取」规则
  - 加入多币种对比的 few-shot 示例
  - LLM 多步调用成功率显著提升

### Day 7

- 更新 README：加入 Agent 架构说明、CLI 使用方式、新增文件结构
- 更新 CHANGELOG
- 新增 TROUBLESHOOTING.md：开发踩坑记录
- GitHub 发布 v0.4 tag

## Week 4: Streamlit 前端界面

### Day 1

- 新增 src/app.py，Streamlit 前端入口
- 实现单币种价格查询页面（st.text_input + st.button + st.spinner）

### Day 2

- 加入 st.selectbox 币种下拉选择
- 接入 AI 分析功能，st.markdown 渲染 LLM 分析报告
- 加入 st.sidebar 侧边栏

### Day 3

- 新增 st.tabs 多标签页：「实时分析」「市场概览」
- st.metric 展示总市值、BTC 市占率、24h 变化（delta 涨跌颜色）
- st.columns 两列布局 + st.expander 折叠面板

### Day 4

- 新增「历史记录」tab，st.dataframe 展示 JSONL 历史数据
- 支持按币种筛选和条数控制
- @st.cache_data 缓存优化

### Day 5

- 异常处理分类：InvalidCoinError / APIError / Exception 分别提示
- st.session_state 记住用户选择的币种
- st.radio 开发模式/正常模式切换
- 开发模式显示 st.exception 完整 traceback

### Day 6

- 更新 requirements.txt，修复依赖版本冲突
- 修复 test_get_crypto_price_invalid 测试
- 从零验证：删 .venv 重建，全流程跑通

### Day 7

- 更新 README 和 CHANGELOG
- GitHub 发布 v0.3 tag

## Week 3

- MiniMax LLM API 接入（OpenAI 兼容格式）
- AI 智能行情分析（analyzer.py + llm_client.py）
- 多轮对话 CLI（messages 列表保持上下文）
- /analyze/{coin} 接口
- think 标签清理、markdown 反引号处理
- system prompt 设计

## Week 2

- Pydantic 数据模型（CoinPrice / MarketOverview / PriceHistory）
- 全局异常处理（InvalidCoinError 404 / APIError 502）
- retry 装饰器（InvalidCoinError 不重试）
- pytest + httpx TestClient 测试
- 代码重构、docstring 补充

## Week 1

- CoinGecko Demo API 接入
- 单币种 / 多币种价格查询
- JSONL 价格历史持久化
- 全球市场概览
- FastAPI 基础接口
- 交互式命令行菜单
- pytest 单元测试
- Git 仓库搭建