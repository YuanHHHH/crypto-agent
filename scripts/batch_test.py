from src.agent.agent_runner import AgentRunner
from src.agent.eval import evaluate
from src.utils.config import TRACE_FILE

agent = AgentRunner()
questions = [
    "BTC 现在多少钱",
    "以太坊的市场数据",
    "全球加密市场情况",
    "你是谁",
    "帮我分析 BTC",
    "对比 BTC 和 ETH",
    "SOL 的详细市场信息",
    "今天适合买币吗",
    "dogecoin 的价格和市值",
    "你好"
]

for question in questions:
    agent.run(question)
    agent.reset()

print(evaluate(TRACE_FILE))