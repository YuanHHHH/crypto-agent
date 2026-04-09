from src.agent.agent_runner import AgentRunner
from src.agent.eval import evaluate
from src.utils.config import TRACE_FILE

agent = AgentRunner()

question1 = "BTC 现在多少钱"
agent.run(question1)
question2 = "以太坊的市场数据"
agent.run(question2)
question3 = "全球加密市场情况"
agent.run(question3)
question4 = "你是谁"
agent.run(question4)
question5 = "帮我分析 BTC"
agent.run(question5)
question6 = "对比 BTC 和 ETH"
agent.run(question6)
question7 = "SOL 的详细市场信息"
agent.run(question7)
question8 = "今天适合买币吗"
agent.run(question8)
question9 = "dogecoin 的价格和市值"
agent.run(question9)
question10 = "你好"
agent.run(question10)

print(evaluate(TRACE_FILE))