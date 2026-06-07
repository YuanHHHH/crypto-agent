import json
from collections import Counter, defaultdict

RESULT_PATH = "../data/eval/eval_result_final.jsonl"


def is_network_error(text: str) -> bool:
    markers = [
        "SSLError",
        "ProxyError",
        "Read timed out",
        "Connection error",
        "Tunnel connection failed",
        "Max retries exceeded",
        "UNEXPECTED_EOF",
    ]
    return any(m in text for m in markers)


def is_agent_failed(record: dict) -> bool:
    final_answer = record.get("agent_result", {}).get("final_answer", "") or ""
    return "[ERROR]" in final_answer or "[FAILED]" in final_answer


def is_judge_failed(record: dict) -> bool:
    reasoning = record.get("judge_result", {}).get("reasoning", "") or ""
    return "judge 调用失败" in reasoning


def main():
    records = []

    with open(RESULT_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    counter = Counter()
    failed_by_case = defaultdict(list)

    for r in records:
        case_id = r["case_id"]
        agent = r["agent"]
        final_answer = r.get("agent_result", {}).get("final_answer", "") or ""
        judge_reasoning = r.get("judge_result", {}).get("reasoning", "") or ""
        overall_pass = r.get("rule_result", {}).get("overall_pass", False)

        if is_network_error(final_answer):
            category = "agent_network_error"
        elif is_agent_failed(r):
            category = "agent_runtime_failed"
        elif is_judge_failed(r) or is_network_error(judge_reasoning):
            category = "judge_failed"
        elif not overall_pass:
            category = "rule_failed"
        else:
            category = "passed"

        counter[category] += 1

        if category != "passed":
            failed_by_case[case_id].append({
                "agent": agent,
                "category": category,
                "details": r.get("rule_result", {}).get("details", ""),
                "final_answer": final_answer[:120],
            })

    print("=== Eval Result Summary ===")
    for k, v in counter.items():
        print(f"{k}: {v}")

    print("\n=== Failed Cases ===")
    for case_id, items in failed_by_case.items():
        print(f"\nCASE {case_id}")
        for item in items:
            print(f"- {item['agent']} | {item['category']} | {item['details']}")
            print(f"  answer: {item['final_answer']}")


if __name__ == "__main__":
    main()