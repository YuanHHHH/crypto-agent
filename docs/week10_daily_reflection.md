# Week 10 反思

**时间**：2026/05/18 - 2026/06/07

---

## 一、本周做了什么

和 Week 5-9 每周都在加功能不一样，Week 10 整周都在建「检验功能的体系」。

具体做了：

- 设计 15 个评估 case，覆盖 basic/context/boundary/complex 四类能力
- 实现规则评估 + LLM judge 双轨制
- 实现三版 Agent 的统一 runner
- 完成批量评估跑完 12 个非 context case
- 实现失败样本重跑和合并脚本
- 分析失败原因，完成 failure_analysis.md

这周最难受的部分不是写代码，而是前两天一直在设计 case 结构，不确定字段要怎么定义，纠结 expected_tools 和 required_tools 的区别，感觉在原地打转。后来明确了「设计 case 结构就是在设计评估标准」之后，才有了方向感。

---

## 二、最大的认知跳跃

这周最大的认知跳跃发生在分析 Case1 LangChain 的时候。

它的工具调用失败了（tools_called 只有 `_Exception`），但最终输出了完整的 BTC 价格、市值和交易量。第一眼看文本输出会以为它回答得不错，直到规则评估显示「required_tools 未命中」才意识到这些数字是 LLM 编造的。

这让我真正理解了「为什么不能只看回答文本」：

回答质量 ≠ 工具调用是否执行 ≠ 数据是否来自真实 API

三件事在文本层面是解耦的，必须在执行路径层面分别验证，才能建立可信的评估结论。

---

## 三、对三版 Agent 的重新认识

**LangGraph 版**：比预期更稳，但不是完美的。主要问题是工具选择有时漂移（Case2 选了 analyze_coin 而不是 get_coin_detail），以及 step 数计算方式和手写版不一致导致在复杂 case 上被误判。

**手写版**：正常路径上出人意料地好，5 个 basic case 全通，3 个 complex case 全通。它的问题集中在边界错误处理：InvalidCoinError 直接冒泡，没有生成用户友好的解释。这是一个明确的 bug，修起来不复杂。

**LangChain ReAct 版**：在涉及工具调用的 case 里失败率约 70%，Case1 还出现了编造数据。它的 judge completeness 平均 10.0（成功时回答质量很好），说明模型本身没有问题，问题出在 ReAct 文本协议和 MiniMax 格式遵从度之间的 gap 上。这是 Week 7 发现的问题，Week 10 的数据再次确认了它。

---

## 四、遇到了什么问题

**最费时的问题：网络不稳定**

CoinGecko、MiniMax、Kimi 三个外部服务都出现过 SSL 错误、代理超时、API 异常。最难受的时候是三个服务同时挂，连 judge 都跑不了。后来通过 VPN 分流（国内 API 直连、海外 API 走代理）解决了大部分问题，但仍然需要 sleep 30 秒甚至更长。

这也让我设计了 `rerun_failed_eval.py`：自动识别哪些是网络失败（可以重跑）、哪些是 Agent 逻辑失败（需要修复），分开处理。

**其次：Python 3.9 + LibreSSL 的 SSL 问题**

Mac 自带的 Python 3.9 用的是 LibreSSL 2.8.3，和 CoinGecko 的 SSL 证书不兼容，频繁报 SSLEOFError。升级到 Python 3.11（Homebrew，带 OpenSSL 3.x）之后彻底解决。

**还有：eval_result.jsonl 循环写入被覆盖**

最初用 `"w"` 模式写文件，每次循环都覆盖前面的结果。这个 bug 在第一次完整跑之前就暴露了，但提醒我：每次批量写文件都要先确认是 `"w"`（清空写入）还是 `"a"`（追加写入）。

---

## 五、对 Eval 体系设计的反思

设计 case 结构比写代码难。

写 `eval_rules.py` 只花了两三个小时，但设计 15 个 case 花了将近两天，而且有一段时间感觉完全不知道怎么下手。

回过头来看，卡住的原因是「不知道一个 case 应该验证什么」。后来想清楚了：每个 case 都是在问「这个 Agent 在这个场景下是否真的做到了它应该做的事」。把问题从「设计数据结构」变成「定义场景期望」之后，case 就写出来了。

另外，response_contains 关键词的覆盖不全暴露了一个问题：同一个语义可以有很多不同的表达方式。Case9 的 LangGraph 版回答「系统未能识别 BTCC」，语义上完全正确，但没命中任何关键词。这提醒我评估标准和 Agent 输出之间需要有一定的「软匹配」，而不是严格字符串匹配。

---

## 六、Week 11 的策略调整

基于这周的结论，Week 11 的策略做一些调整：

**主线：LangGraph**

继续在 LangGraph 主线上增加工具，不再为 LangChain ReAct 版投入修复资源。

**首先修：手写版边界错误恢复**

`InvalidCoinError` 不应该直接冒泡，应该作为 observation 传回 LLM。这个改动小，但对边界场景的用户体验影响大。

**回归测试：每次加工具前跑一遍 eval**

新工具上线前，先跑 `python scripts/run_eval.py`，确认旧 case 通过率没有下降，再继续。

**标注维护：更新 Case2、Case9、Case14 的标注**

Case2 optional_tools 加 analyze_coin；Case9 response_contains 扩充同义词；Case14 max_steps 改为 8。

---

## 七、一句话总结

Week 10 的核心发现是：**没有评估体系，功能越多越不知道哪里坏了。有了评估体系，每次改动才有回归测试的地基。**
