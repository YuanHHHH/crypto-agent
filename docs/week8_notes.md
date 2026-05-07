# Week 8 学习笔记

## 1. RAG 的 5 个组件和数据流

RAG（Retrieval Augmented Generation）解决的是 LLM 训练数据过时、缺乏特定领域知识的问题。通过检索外部知识库增强 LLM 的回答质量。

5 个核心组件：

- Chunk：把长文档切成 500 字符左右的小段。原因一是 embedding 模型有输入长度限制（MiniLM 最大 256 word pieces），二是整篇文档 embedding 会变成多个主题的「平均值」，和具体问题的匹配度低
- Embedding：用 sentence-transformers 的 all-MiniLM-L6-v2 把文本转成 384 维向量。语义相近的文本在向量空间中方向接近（cosine similarity 高）。这是训练出来的能力，不是天然的
- Vector Store：向量数据库（Chroma），用 L2 距离做近似最近邻（ANN）检索。和 MySQL 的区别是按「语义相似度」搜索而不是精确匹配
- Retrieval：把用户 query embedding 后在向量库里找 top-k 最相似的 chunk
- Generation：把检索到的 chunk 和用户问题拼成增强 prompt，让 LLM 基于真实资料回答

数据流：用户问题 → embed → 向量检索 → top-k chunk → 拼入 prompt → LLM 生成答案

## 2. chunk_size 和 chunk_overlap 的 tradeoff

选择 chunk_size=500 字符、chunk_overlap=50 字符。

chunk_size 太大（如 2000）：一个 chunk 包含多个主题，embedding 变成多主题的平均向量，检索精度下降。而且可能超过 embedding 模型的输入限制。

chunk_size 太小（如 100）：一个 chunk 不包含完整语义，检索回来的片段缺乏上下文，LLM 无法基于它给出有意义的回答。

chunk_overlap=50：相邻 chunk 有 50 字符重叠，防止一个完整句子被切断后两个 chunk 都缺乏完整信息。

500 字符大约 100-150 英文 token，远小于 MiniLM 的 256 word pieces 限制，给复杂句子留了余量。实际测试 bitcoin.md（约 8000 字符）切成约 50 个 chunk，每个 chunk 语义基本完整。

## 3. 为什么选 all-MiniLM-L6-v2

选型理由：

- 体积小（~90MB），适合本地开发和快速迭代
- 384 维输出，存储和计算成本低
- HuggingFace 生态最流行的轻量级 embedding 模型之一

跨语言能力测试结果：

- "bitcoin" vs "BTC"：cosine similarity = 0.72（英文同义词，高相似度）
- "bitcoin" vs "比特币"：cosine similarity = 0.10（中英跨语言，极低）
- "bitcoin" vs "python programming"：cosine similarity 很低（不相关，符合预期）

结论：MiniLM 的跨语言能力不行。中文 query 检索英文语料效果差。本项目语料是英文，所以在 prompt 里引导 Agent 用英文关键词检索。如果需要中英混合检索，应该换 multilingual-e5-base 或 BGE-M3。

## 4. 检索结果相关性判断

Day 4 CLI 测试 5 个 query 的 top-1 distance 分布：

- "What is Bitcoin"：0.35（精准命中 bitcoin.md）
- "What is DEX"：0.30（精准命中 dex.md）
- "difference between PoS and PoW"：0.80（命中 proof_of_stake.md）
- "What is Ethereum gas"：0.90（命中 ethereum.md，距离偏大因为 gas 是子概念）
- "What is the weather today"：1.45（无关，距离明显大）

相关 query 的 distance 范围：0.30 - 0.90
无关 query 的 distance 范围：1.45+
两组之间有明显 gap，阈值可设在 1.2 左右

Chroma 默认用 L2 距离（欧氏距离），不是余弦距离。但因为 MiniLM 输出的向量是归一化的，L2 和余弦距离在归一化向量上是单调关系，结论一致：越小越相似。

## 5. Agent + RAG 路由策略

在 SYSTEM_PROMPT 里加了三条路由规则：

- 有实时数据需求（价格、市值、24h 变化）→ 用 get_price / get_market 等 API 工具
- 有概念性问题（什么是、原理、区别、特点）→ 用 search_rag_knowledge
- 复合问题 → 先查知识库再查 API

Agent 的路由决策发生在 LLM 的 Thought 阶段。LLM 先看 SYSTEM_PROMPT 里的工具列表和使用规则，再结合用户问题，在 Thought 里决定调哪个工具。这个决策完全由 LLM 自主完成，不是硬编码的 if-else。

加了示例 3（「什么是 BTC」走 search_rag_knowledge）帮助 LLM 理解路由模式。

## 6. 5 个路由测试结果

| 测试 | 期望路由 | 实际路由 | 结果 |
|------|---------|---------|------|
| 什么是 PoS | search_rag_knowledge | search_rag_knowledge | 正确，答案引用了知识库内容 |
| BTC 现在多少钱 | get_price | get_price | 正确，返回真实价格 $81,576 |
| 对比 BTC 和 ETH 价格 | get_price 两次 | get_price(BTC) → LLM 编造 ETH 数据 | 失败，LLM 自己伪造了 Observation |
| DeFi 概念 + 总市值 | search + get_market | search + get_market | 正确，复合路由成功 |
| 以太坊原理 + 价格 | search + get_price | get_price + search | 正确，顺序和 prompt 要求相反但两个工具都调了 |

关键发现：

- 单工具路由（测试 1、2）：100% 正确
- 复合路由（测试 4、5）：工具选择正确，顺序可能和 prompt 要求不一致
- 测试 3 失败的根因不是 RAG，是 MiniMax 的老问题——LLM 在一次输出里同时编造了 Observation 和 Final Answer，绕过了工具调用

面试素材：「我的 Agent 是双模态的，能根据问题类型自动选择走 API 还是知识库检索。单工具路由准确率 100%，复合路由也能正确串行调用不同工具。」
