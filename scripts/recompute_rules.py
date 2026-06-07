import json
from src.agent.eval_rules import evaluate_rules

RESULT_PATH = "../data/eval/eval_result.jsonl"
CASE_PATH = "../data/eval/eval_set_v1.jsonl"
OUTPUT_PATH = "../data/eval/eval_result_recomputed_rules.jsonl"


with open(CASE_PATH, "r", encoding="utf-8") as f:
    cases = [json.loads(line) for line in f if line.strip()]

case_map = {case["id"]: case for case in cases}

with open(RESULT_PATH, "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for record in records:
        case_id = record["case_id"]
        case = case_map[case_id]

        record["rule_result"] = evaluate_rules(
            record["agent_result"],
            case,
        )

        f.write(json.dumps(record, ensure_ascii=False) + "\n")

print(f"重新计算 rule_result 完成，输出到：{OUTPUT_PATH}")