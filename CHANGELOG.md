# Changelog

## Week 6: Agent 深化 + 对话记忆 + 质量评估

### Day 1

- 新增 analyze_coin 工具到 ToolRegistry，Agent 可自主触发深度行情分析
- 改造 analyzer.py：内部调用 llm_client 生成分析报告（不再只返回 prompt 字符串）
- 这相当于 Agent 中的 subagent 雏形：主 Agent 调工具，工具内部再调一次 LLM 做专业分析
- Agent 现有 4 个工具：get_price / get_market / get_coin_detail / analyze_coin
- 验证工具扩展性：加新工具只需调 register()，agent_runner.py 零改动

### Day 2

- AgentRunner 新增 self.chat_history（list of dict）支持多轮对话记忆
- 每次 run() 时把历史问答拼接到 conversation 开头
- 历史只保留 user_question 和 final_answer，不保留中间的 Thought/Action/Observation，避免污染上下文
- 新增 reset() 方法清空对话历史
- agent_cli.py 支持 `reset` 命令重置对话
- 多轮连续提问测试通过：「BTC 多少钱」→「那 ETH 呢」→「对比这两个」

### Day 3

- 新增 src/agent/parser.py，抽取 LLM 输出解析逻辑为纯函数
- parse_llm_output 返回结构化 dict：type / function_name / action_input / final_answer / error_notice / raw_text
- 字段名统一 snake_case
- 支持 4 种解析结果：action / final_answer / error / no_parsed
- 新增 extract_thought 辅助函数，安全提取 Thought 内容，处理缺失情况
- agent_runner 主循环大幅简化：解析逻辑不再混在业务代码里，只按 type 分发
- parser 独立测试跑通 4 种 case
- 这一层抽象的价值：未来切换到 Function Calling 格式只需重写 parser.py

### Day 4

- 新增 src/agent/eval.py，Agent 质量评估模块
- 统计指标：总运行次数、成功率、平均步数、平均耗时、格式错误率、兜底率
- trace 记录新增字段：end_reason / tool_call_count / parse_error_count
- end_reason 默认 "max_steps"，final_answer 和 no_parsed 分支显式赋值
- 发现并修复 steps 计数 bug：final_answer / no_parsed 分支 break 前缺少 steps+1，导致平均步数偏小
- 新增 scripts/batch_test.py 批量测试脚本
- 10 个测试用例覆盖：单工具 / 多工具 / 无工具 / 深度分析 / 寒暄
- 每个用例之间调用 agent.reset() 隔离，避免历史干扰
- 首轮评估结果：成功率 ~85%，平均步数 1.59，兜底率 ~15%
- 通过 eval 发现隐藏问题：LLM 有时输出答案但省略 Final Answer 前缀，被误判为兜底。这是只靠人工测试发现不了的

### Day 5

- AgentRunner 新增 step_log 列表，记录每一步的完整信息
- 每个 step 包含：step / type / thought / action / action_input / observation / final_answer / raw_text
- run() 方法返回 (final_answer, step_log) 二元组
- Streamlit Agent 模式新增推理过程可视化
- 用 st.expander 展示每一步的 Thought / Action / Action Input / Observation
- 修复 st.expander(step_log) 用法错误：expander 参数是标题字符串，不是内容
- 最终答案单独展示在步骤下方
- 同步更新 agent_cli.py 适配 tuple 返回值

### Day 6

- 发现 requirements.txt 漏装 httpx（test_api.py 需要）
- pip install httpx 并补到 requirements.txt
- pytest 12 个测试全部通过
- 代码清理：
  - 删除 agent_runner.py 里注释掉的旧 run() 方法
  - 清理 tool_registry.py 未使用的 get_crypto_price / get_market_overview import
  - 清理 api.py 未使用的 llm_client import
  - 清理 app.py 未使用的 llm_client / CryptoAgentError import

### Day 7

- 更新 README：Week 6 新功能、Agent 架构图增加 chat_history 和 step_log、4 个工具说明、核心模块说明
- 更新 CHANGELOG：Week 6 每天的变更
- 更新 TROUBLESHOOTING.md：Week 6 新遇到的问题
- GitHub 发布 v0.5 tag

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