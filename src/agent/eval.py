import json

def evaluate(file_path):
    """
统计以下指标：

总运行次数
成功率（有 final_answer 且不为空的比例）
平均步数
平均耗时
工具调用成功率（调用了工具且没有报错的比例）
兜底率（走了 else 分支的比例）
    :param file_path:
    :return: 返回评估数据
    """
    with open(file_path) as f:
        json_list = [json.loads(line) for line in f if line.strip()]
        total_count = len(json_list)
        if total_count == 0:
            print("没有trace记录")
            return
        successful_list = [line for line in json_list if line["end_reason"]=="final_answer"]
        success_rate = len(successful_list) / total_count
        steps = 0
        total_time=0
        else_count = 0
        tool_call_count = 0
        parse_error_count = 0
        for line in json_list:
            steps += line["total_steps"]
            total_time += line["total_time"]
            tool_call_count += line.get("tool_call_count",0)
            parse_error_count += line.get("parse_error_count",0)
            if line["end_reason"] == "no_parsed":
                else_count += 1

        res_steps = steps / total_count
        res_time = total_time / total_count
        if tool_call_count != 0:
            parse_error_rate = parse_error_count / tool_call_count
        else:
            parse_error_rate = 0
        res_else = else_count / total_count

    return {
        "总运行次数":total_count,
        "成功率":success_rate,
        "平均步数":res_steps,
        "平均耗时":res_time,
        "格式错误率":parse_error_rate,
        "兜底率":res_else
    }


if __name__ == "__main__":
    from src.utils.config import TRACE_FILE
    result = evaluate(TRACE_FILE)
    if result:
        for key, value in result.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2%}" if "率" in key else f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
