import json
import time
from pathlib import Path

from src.agent.eval_judge import judge_response
from src.agent.eval_rules import evaluate_rules
from src.agent.eval_runners import (
    run_langchain_for_eval,
    run_handwritten_for_eval,
)

EVAL_SET_PATH = Path("../data/eval/eval_set_v1.jsonl")
BASE_RESULT_PATH = Path("../data/eval/eval_result_merged_3.jsonl")
OUTPUT_PATH = Path("../data/eval/eval_result_target_rerun.jsonl")

# 只重跑这 4 条
TARGETS = {
    (13, "langchain"),
}

AGENT_RUNNERS = {
    "langchain": run_langchain_for_eval,
    "handwritten": run_handwritten_for_eval,
}


def load_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def safe_judge(question, agent_result, expected_answer_points):
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
        question=question,
        agent_output=final_answer,
        actual_tools=actual_tools,
        expected_answer_points=expected_answer_points,
    )


def main():
    cases = load_jsonl(EVAL_SET_PATH)
    records = load_jsonl(BASE_RESULT_PATH)
    case_map = {case["id"]: case for case in cases}

    new_records = []
    rerun_count = 0
    kept_count = 0

    for record in records:
        case_id = record["case_id"]
        agent = record["agent"]
        key = (case_id, agent)

        if key not in TARGETS:
            new_records.append(record)
            kept_count += 1
            continue

        case = case_map[case_id]
        question = record["question"]
        runner = AGENT_RUNNERS[agent]
        expected_answer_points = case["expected_answer_points"]

        print(f"[CASE {case_id}] [{agent}] target rerun agent start")
        agent_result = runner(question)
        print(f"[CASE {case_id}] [{agent}] target rerun agent done")

        time.sleep(30)

        print(f"[CASE {case_id}] [{agent}] target rerun rule start")
        rule_result = evaluate_rules(agent_result, case)
        print(f"[CASE {case_id}] [{agent}] target rerun rule done")

        print(f"[CASE {case_id}] [{agent}] target rerun judge start")
        judge_result = safe_judge(question, agent_result, expected_answer_points)
        print(f"[CASE {case_id}] [{agent}] target rerun judge done")

        new_record = dict(record)
        new_record["agent_result"] = agent_result
        new_record["rule_result"] = rule_result
        new_record["judge_result"] = judge_result
        new_record["rerun_type"] = "target_agent_and_judge"

        new_records.append(new_record)
        rerun_count += 1

        time.sleep(50)

    write_jsonl(OUTPUT_PATH, new_records)

    print("\n=== Target Rerun Done ===")
    print(f"kept: {kept_count}")
    print(f"rerun: {rerun_count}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()