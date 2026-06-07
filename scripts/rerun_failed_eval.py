import json
import time
from pathlib import Path

from src.agent.eval_judge import judge_response
from src.agent.eval_rules import evaluate_rules
from src.agent.eval_runners import (
    run_langgraph_for_eval,
    run_langchain_for_eval,
    run_handwritten_for_eval,
)


EVAL_SET_PATH = Path("../data/eval/eval_set_v1.jsonl")
EVAL_RESULT_PATH = Path("../data/eval/eval_result_merged_2.jsonl")
OUTPUT_PATH = Path("../data/eval/eval_result_rerun_3.jsonl")


AGENT_RUNNERS = {
    "langgraph": run_langgraph_for_eval,
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
    """
    安全调用 judge。

    Agent 自身已经失败时，直接给 0 分。
    这样可以减少无意义 judge 调用，也减少 Kimi 网络压力。
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
        question=question,
        agent_output=final_answer,
        actual_tools=actual_tools,
        expected_answer_points=expected_answer_points,
    )


def classify_record(record):
    """
    只用于判断是否需要重跑。

    分类优先级：
    1. judge_failed：Agent 正常，judge 调用失败
    2. agent_network_error：Agent 结果里有网络/API错误
    3. other：其他情况原样保留
    """
    agent_result = record.get("agent_result", {}) or {}
    judge_result = record.get("judge_result", {}) or {}
    rule_result = record.get("rule_result", {}) or {}

    final_answer = agent_result.get("final_answer", "") or ""
    judge_reasoning = judge_result.get("reasoning", "") or ""
    rule_details = rule_result.get("details", "") or ""

    network_markers = [
        "HTTPSConnectionPool",
        "SSLError",
        "ProxyError",
        "Read timed out",
        "Connection error",
        "LLM API 网络错误",
        "Max retries exceeded",
        "Tunnel connection failed",
        "api.minimaxi.com",
        "api.coingecko.com",
        "api.moonshot.cn",
    ]

    if "judge 调用失败" in judge_reasoning or "judge 返回异常结构" in judge_reasoning:
        return "judge_failed"

    if any(marker in final_answer for marker in network_markers):
        return "agent_network_error"

    if any(marker in rule_details for marker in network_markers):
        return "agent_network_error"

    return "other"


def build_case_map(cases):
    return {case["id"]: case for case in cases}


def rerun_judge_only(record, case, sleep_seconds=30):
    """
    只重跑 judge，复用原来的 agent_result 和 rule_result。
    """
    case_id = record["case_id"]
    agent = record["agent"]
    question = record["question"]
    agent_result = record["agent_result"]
    expected_answer_points = case["expected_answer_points"]

    print(f"[CASE {case_id}] [{agent}] rerun judge only start")
    judge_result = safe_judge(question, agent_result, expected_answer_points)
    print(f"[CASE {case_id}] [{agent}] rerun judge only done")

    new_record = dict(record)
    new_record["judge_result"] = judge_result
    new_record["rerun_type"] = "judge_only"

    time.sleep(sleep_seconds)
    return new_record


def rerun_agent_and_judge(record, case, sleep_seconds=30):
    """
    重跑对应 agent，然后重新计算 rule 和 judge。
    """
    case_id = record["case_id"]
    agent = record["agent"]
    question = record["question"]
    expected_answer_points = case["expected_answer_points"]

    runner = AGENT_RUNNERS.get(agent)
    if runner is None:
        print(f"[CASE {case_id}] [{agent}] unknown agent, keep original")
        return record

    print(f"[CASE {case_id}] [{agent}] rerun agent start")
    agent_result = runner(question)
    print(f"[CASE {case_id}] [{agent}] rerun agent done")

    time.sleep(sleep_seconds)

    print(f"[CASE {case_id}] [{agent}] rerun rule start")
    rule_result = evaluate_rules(agent_result, case)
    print(f"[CASE {case_id}] [{agent}] rerun rule done")

    print(f"[CASE {case_id}] [{agent}] rerun judge start")
    judge_result = safe_judge(question, agent_result, expected_answer_points)
    print(f"[CASE {case_id}] [{agent}] rerun judge done")

    new_record = dict(record)
    new_record["agent_result"] = agent_result
    new_record["rule_result"] = rule_result
    new_record["judge_result"] = judge_result
    new_record["rerun_type"] = "agent_and_judge"

    time.sleep(sleep_seconds)
    return new_record


def main():
    cases = load_jsonl(EVAL_SET_PATH)
    records = load_jsonl(EVAL_RESULT_PATH)
    case_map = build_case_map(cases)

    new_records = []

    stats = {
        "kept": 0,
        "judge_only": 0,
        "agent_and_judge": 0,
    }

    for record in records:
        case_id = record["case_id"]
        case = case_map.get(case_id)

        if case is None:
            print(f"[CASE {case_id}] case not found, keep original")
            new_records.append(record)
            stats["kept"] += 1
            continue

        record_type = classify_record(record)

        if record_type == "judge_failed":
            new_record = rerun_judge_only(record, case)
            new_records.append(new_record)
            stats["judge_only"] += 1

        elif record_type == "agent_network_error":
            new_record = rerun_agent_and_judge(record, case)
            new_records.append(new_record)
            stats["agent_and_judge"] += 1

        else:
            new_records.append(record)
            stats["kept"] += 1

    write_jsonl(OUTPUT_PATH, new_records)

    print("\n=== Rerun Done ===")
    print(f"kept: {stats['kept']}")
    print(f"judge_only: {stats['judge_only']}")
    print(f"agent_and_judge: {stats['agent_and_judge']}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()