from src.agent.agent_runner import AgentRunner

agent_runner = AgentRunner()
while True:
    user_input = input("请输入你想问的问题：\n")
    if user_input == "exit":
        print("感谢使用，已结束")
        break
    agent_runner.run(user_input)
