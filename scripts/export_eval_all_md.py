# scripts/export_eval_all_md.py

import json
from pathlib import Path

INPUT_PATH = Path("../data/eval/eval_result_final.jsonl")
OUTPUT_PATH = Path("../data/eval/eval_result_all.md")


def load_jsonl(path: Path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def short_text(text, max_len=1200):
    text = text or ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n\n...（已截断）"


def main():
    records = load_jsonl(INPUT_PATH)

    lines = []
    lines.append("# Eval Result All Records\n")
    lines.append(f"- 总记录数：{len(records)}\n")

    for r in records:
        case_id = r.get("case_id")
        agent = r.get("agent")
        question = r.get("question")
        capability = r.get("capability")
        sub_type = r.get("sub_type")

        agent_result = r.get("agent_result", {}) or {}
        judge_result = r.get("judge_result", {}) or {}
        rule_result = r.get("rule_result", {}) or {}

        final_answer = agent_result.get("final_answer", "") or ""
        tools_called = agent_result.get("tools_called", []) or []
        total_steps = agent_result.get("total_steps")
        tool_results = agent_result.get("tool_results", []) or []

        rule_pass = rule_result.get("overall_pass")
        rule_details = rule_result.get("details", "")

        accuracy = judge_result.get("accuracy")
        completeness = judge_result.get("completeness")
        relevance = judge_result.get("relevance")
        reasoning = judge_result.get("reasoning", "") or ""

        lines.append(f"## CASE {case_id} - {agent}\n")
        lines.append(f"- **question**：{question}")
        lines.append(f"- **capability**：{capability}")
        lines.append(f"- **sub_type**：{sub_type}")
        lines.append(f"- **rule_pass**：{rule_pass}")
        lines.append(f"- **rule_details**：{rule_details}")
        lines.append(f"- **tools_called**：`{tools_called}`")
        lines.append(f"- **total_steps**：{total_steps}")
        lines.append(f"- **judge_score**：accuracy={accuracy}, completeness={completeness}, relevance={relevance}")

        if r.get("rerun_type"):
            lines.append(f"- **rerun_type**：{r.get('rerun_type')}")

        lines.append("\n### Agent Answer\n")
        lines.append("```text")
        lines.append(short_text(final_answer, 1500))
        lines.append("```")

        lines.append("\n### Tool Results\n")
        lines.append("```json")
        lines.append(json.dumps(tool_results, ensure_ascii=False, indent=2))
        lines.append("```")

        lines.append("\n### Judge Reasoning\n")
        lines.append("```text")
        lines.append(short_text(reasoning, 1500))
        lines.append("```")

        lines.append("\n---\n")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("=== Export Done ===")
    print(f"input: {INPUT_PATH}")
    print(f"output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()