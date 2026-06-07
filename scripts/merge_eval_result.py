import json
from pathlib import Path

ORIGINAL_PATH = Path("../data/eval/eval_result_merged.jsonl")
RERUN_PATH = Path("../data/eval/eval_result_target_rerun.jsonl")
OUTPUT_PATH = Path("../data/eval/eval_result_final.jsonl")


def record_key(record):
    return (record["case_id"], record["agent"])


def is_better(new_record, old_record):
    """
    判断 rerun 后的新记录是否应该覆盖旧记录。

    覆盖条件：
    1. 新记录 rule overall_pass=True
    2. 或者旧记录 judge 失败，新记录 judge 成功
    3. 或者旧记录是 [ERROR]/[FAILED]，新记录不是
    """
    new_rule = new_record.get("rule_result", {})
    old_rule = old_record.get("rule_result", {})

    new_judge = new_record.get("judge_result", {})
    old_judge = old_record.get("judge_result", {})

    new_answer = new_record.get("agent_result", {}).get("final_answer", "") or ""
    old_answer = old_record.get("agent_result", {}).get("final_answer", "") or ""

    # 1. 新结果规则通过，旧结果规则没通过
    if new_rule.get("overall_pass") is True and old_rule.get("overall_pass") is not True:
        return True

    # 2. 旧 judge 失败，新 judge 成功
    old_judge_failed = "judge 调用失败" in old_judge.get("reasoning", "") or old_judge.get("reasoning", "").startswith("judge 返回异常结构")
    new_judge_ok = not (
        "judge 调用失败" in new_judge.get("reasoning", "")
        or new_judge.get("reasoning", "").startswith("judge 返回异常结构")
    )

    if old_judge_failed and new_judge_ok:
        return True

    # 3. 旧 agent 是错误输出，新 agent 是正常输出
    old_agent_failed = "[ERROR]" in old_answer or "[FAILED]" in old_answer
    new_agent_ok = "[ERROR]" not in new_answer and "[FAILED]" not in new_answer

    if old_agent_failed and new_agent_ok:
        return True

    return False


def load_jsonl(path):
    records = []
    if not path.exists():
        return records

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def main():
    original_records = load_jsonl(ORIGINAL_PATH)
    rerun_records = load_jsonl(RERUN_PATH)

    merged = {record_key(record): record for record in original_records}

    replaced = 0
    kept = 0
    added = 0

    for new_record in rerun_records:
        key = record_key(new_record)

        if key not in merged:
            merged[key] = new_record
            added += 1
            continue

        old_record = merged[key]

        if is_better(new_record, old_record):
            merged[key] = new_record
            replaced += 1
        else:
            kept += 1

    final_records = sorted(
        merged.values(),
        key=lambda x: (x["case_id"], x["agent"])
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for record in final_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("=== Merge Done ===")
    print(f"original: {len(original_records)}")
    print(f"rerun: {len(rerun_records)}")
    print(f"replaced: {replaced}")
    print(f"added: {added}")
    print(f"kept_from_original_or_rerun: {kept}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()