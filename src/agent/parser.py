import json

def extract_thought(text):
    """
    提取llm返回的thought
    :param text:
    :return: 返回从完整回答中提取出的thought
    """
    if "Thought:" not in text:
        return ""
    after_thought = text.split("Thought:", 1)[1]
    for stop_word in ["Action:", "Final Answer:"]:
        if stop_word in after_thought:
            after_thought = after_thought.split(stop_word)[0]
    return after_thought.strip()

def parse_llm_output(client_response):
    """
    解析llm的输出，格式化的返回给agent循环，解耦功能
    :param client_response:
    :return: 返回格式化的llm回答
    """
    thought = extract_thought(client_response)
    if "Action" in client_response:
        info_part = client_response.split("Action:", 1)[1]
        function_name = info_part.split("Action Input:", 1)[0].strip()
        params = client_response.split("Action Input:", 1)[1].strip()
        params_first_line = params.split("\n")[0].strip()
        try:
            params_str = json.loads(params_first_line)
            response_parsed = {
                "type": "action",
                "thought": thought,
                "function_name": function_name,
                "action_input": params_str,
            }
            return response_parsed
        except json.decoder.JSONDecodeError:
            error_notice = f"Action Input 格式不正确，不是合法JSON"
            response_parsed = {
                "type": "error",
                "thought": thought,
                "error_notice": error_notice,
            }
            return response_parsed

    elif "Final Answer" in client_response:
        final_answer = client_response.split("Final Answer:", 1)[1].strip()
        response_parsed = {
            "type": "final_answer",
            "thought": thought,
            "final_answer": final_answer,
        }
        return response_parsed

    else:
        # 兜底
        raw_text = client_response
        response_parsed = {
            "type": "no_parsed",
            "thought": thought,
            "raw_text": raw_text,
        }
        return response_parsed

