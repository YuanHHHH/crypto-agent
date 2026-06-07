import json
import time
from src.agent.eval_judge import judge_response
from src.agent.eval_rules import evaluate_rules
from src.agent.eval_runners import run_handwritten_for_eval,run_langgraph_for_eval,run_langchain_for_eval

def safe_judge(question, agent_result, expected_answer_points):
    """
    安全调用 judge。

    如果 Agent 本身已经返回 [ERROR] 或 [FAILED]，
    就不再调用 Kimi judge，直接给 0 分。
    """
    final_answer = agent_result.get("final_answer", "") or ""
    actual_tools = agent_result.get("tools_called", []) or []

    if "[ERROR]" in final_answer or "[FAILED]" in final_answer:
        return {
            "reasoning": "Agent 执行失败，跳过 LLM judge",
            "accuracy": 0,
            "completeness": 0,
            "relevance": 0,
        }

    return judge_response(
        question,
        final_answer,
        actual_tools,
        expected_answer_points,
    )

with open("../data/eval/eval_set_v1.jsonl","r", encoding="utf-8") as f:
    cases = [json.loads(line) for line in f if line.strip()]

with open("../data/eval/eval_result.jsonl", "w", encoding="utf-8") as f:
    pass

cases_num = len(cases)
for i in range(cases_num):
    if cases[i].get("capability") == "context":
        continue

    question = cases[i]["question"]

    print(f"[CASE {cases[i]['id']}] run langgraph start")
    res_langgraph = run_langgraph_for_eval(question)
    print(f"[CASE {cases[i]['id']}] run langgraph done")
    time.sleep(30)
    print(f"[CASE {cases[i]['id']}] run langchain start")
    res_langchain = run_langchain_for_eval(question)
    print(f"[CASE {cases[i]['id']}] run langchain done")
    time.sleep(30)
    print(f"[CASE {cases[i]['id']}] run handwritten start")
    res_handwritten = run_handwritten_for_eval(question)
    print(f"[CASE {cases[i]['id']}] run handwritten done")
    time.sleep(30)

    langgraph_agent_output = res_langgraph["final_answer"]
    langchain_agent_output = res_langchain["final_answer"]
    handwritten_agent_output = res_handwritten["final_answer"]

    langgraph_actual_tools = res_langgraph["tools_called"]
    langchain_actual_tools = res_langchain["tools_called"]
    handwritten_actual_tools = res_handwritten["tools_called"]

    expected_answer_points =cases[i]["expected_answer_points"]

    print(f"[CASE {cases[i]['id']}] judge langgraph start")
    judge_langgraph = safe_judge(question, res_langgraph, expected_answer_points)
    print(f"[CASE {cases[i]['id']}] judge langgraph done")
    time.sleep(30)
    print(f"[CASE {cases[i]['id']}] judge langchain start")
    judge_langchain = safe_judge(question, res_langchain, expected_answer_points)
    print(f"[CASE {cases[i]['id']}] judge langchain done")
    time.sleep(30)
    print(f"[CASE {cases[i]['id']}] judge handwritten start")
    judge_handwritten = safe_judge(question, res_handwritten, expected_answer_points)
    print(f"[CASE {cases[i]['id']}] judge handwritten done")
    time.sleep(30)

    rules_langgraph = evaluate_rules(res_langgraph,cases[i])
    rules_langchain = evaluate_rules(res_langchain,cases[i])
    rules_handwritten = evaluate_rules(res_handwritten,cases[i])

    records = [
        {
            "case_id": cases[i]["id"],
            "question": question,
            "capability": cases[i].get("capability"),
            "sub_type": cases[i].get("sub_type"),
            "agent": "langgraph",
            "agent_result": res_langgraph,
            "judge_result": judge_langgraph,
            "rule_result": rules_langgraph,
        },
        {
            "case_id": cases[i]["id"],
            "question": question,
            "capability": cases[i].get("capability"),
            "sub_type": cases[i].get("sub_type"),
            "agent": "langchain",
            "agent_result": res_langchain,
            "judge_result": judge_langchain,
            "rule_result": rules_langchain,
        },
        {
            "case_id": cases[i]["id"],
            "question": question,
            "capability": cases[i].get("capability"),
            "sub_type": cases[i].get("sub_type"),
            "agent": "handwritten",
            "agent_result": res_handwritten,
            "judge_result": judge_handwritten,
            "rule_result": rules_handwritten,
        },
    ]

    with open("../data/eval/eval_result.jsonl","a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record,ensure_ascii=False)+ "\n")
    time.sleep(50)