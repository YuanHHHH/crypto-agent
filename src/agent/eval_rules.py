def normalize_tool_name(tool_name: str) -> str:
    """
    统一不同 Agent 版本里的工具名。

    例如：
    handwritten 版可能叫 search_rag_knowledge，
    LangGraph / LangChain 版叫 search_rag。
    评估时应该把它们视为同一个工具。
    """
    alias_map = {
        "search_rag_knowledge": "search_rag",
    }
    return alias_map.get(tool_name, tool_name)

def evaluate_rules(agent_run_result, case):
    """
    对 Agent 的执行结果做规则评估。

    agent_run_result:
    {
        "final_answer": "...",
        "tools_called": ["get_price"],
        "total_steps": 3,
        "tool_results": [{"price": 78000}]
    }

    case:
    {
        "id": 1,
        "question": "BTC 价格是多少？",
        "required_tools": ["get_price"],
        "optional_tools": ["get_coin_detail"],
        "rule_checks": {
            "must_call_tool": true,
            "max_steps": 3,
            "required_response_fields": ["price"],
            "response_contains": []
        }
    }
    """
    results = {}
    details = []

    rule_checks = case.get("rule_checks", {})

    final_answer = agent_run_result.get("final_answer", "") or ""
    tools_called = agent_run_result.get("tools_called", []) or []
    tools_called = [normalize_tool_name(tool) for tool in tools_called]

    tool_results = agent_run_result.get("tool_results", []) or []
    total_steps = agent_run_result.get("total_steps", 0)

    # 1. 是否要求调用工具
    must_call = rule_checks.get("must_call_tool", False)
    actually_called = len(tools_called) > 0

    if must_call:
        results["must_call_tool_pass"] = actually_called
        if not actually_called:
            details.append("规则要求调用工具，但 Agent 没有调用任何工具")
    else:
        # must_call_tool=False 表示不强制调用工具，调用了也不直接判失败
        results["must_call_tool_pass"] = True

    # 2. 是否调用了必要工具
    # 这里读取 case 顶层 required_tools
    required_tools = case.get("required_tools", [])

    if required_tools:
        actual_tools = set(tools_called)
        missing_tools = [tool for tool in required_tools if tool not in actual_tools]

        results["required_tools_pass"] = len(missing_tools) == 0

        if missing_tools:
            details.append(
                f"缺少必要工具调用：{missing_tools}，实际调用：{tools_called}"
            )
    else:
        results["required_tools_pass"] = True

    # 3. 步数是否超限
    max_steps = rule_checks.get("max_steps", 10)
    results["max_steps_pass"] = total_steps <= max_steps

    if not results["max_steps_pass"]:
        details.append(f"步数超限：实际 {total_steps} 步，限制 {max_steps} 步")

    # 4. 工具返回字段检查
    required_fields = rule_checks.get("required_response_fields", [])

    if required_fields:
        all_fields = set()

        for result in tool_results:
            if isinstance(result, dict):
                all_fields.update(result.keys())

        missing_fields = [field for field in required_fields if field not in all_fields]

        results["required_fields_pass"] = len(missing_fields) == 0

        if missing_fields:
            details.append(
                f"工具返回缺少必要字段：{missing_fields}，已有字段：{sorted(all_fields)}"
            )
    else:
        results["required_fields_pass"] = True

    min_tool_calls = rule_checks.get("min_tool_calls")

    if min_tool_calls is not None:
        actual_tool_calls = len(tools_called)
        results["min_tool_calls_pass"] = actual_tool_calls >= min_tool_calls

        if not results["min_tool_calls_pass"]:
            details.append(
                f"工具调用次数不足：实际 {actual_tool_calls} 次，至少需要 {min_tool_calls} 次"
            )
    else:
        results["min_tool_calls_pass"] = True

    # 5. 回答关键词检查
    response_contains = rule_checks.get("response_contains", [])

    if response_contains:
        found_any = any(keyword in final_answer for keyword in response_contains)
        results["response_contains_pass"] = found_any

        if not found_any:
            details.append(f"回答中未包含任何期望关键词：{response_contains}")
    else:
        results["response_contains_pass"] = True

    # 6. 最终回答非空
    results["non_empty_pass"] = len(final_answer.strip()) > 0

    if not results["non_empty_pass"]:
        details.append("Agent 最终回答为空")

    # 7. 错误标记检查
    error_markers = ["[ERROR]", "[FAILED]"]
    results["no_error_pass"] = not any(marker in final_answer for marker in error_markers)

    if not results["no_error_pass"]:
        details.append("Agent 返回错误或失败标记")

    # 8. 汇总
    results["overall_pass"] = all([
        results["must_call_tool_pass"],
        results["required_tools_pass"],
        results["min_tool_calls_pass"],
        results["max_steps_pass"],
        results["required_fields_pass"],
        results["response_contains_pass"],
        results["non_empty_pass"],
        results["no_error_pass"],
    ])

    results["details"] = "; ".join(details) if details else "所有规则检查通过"

    return results