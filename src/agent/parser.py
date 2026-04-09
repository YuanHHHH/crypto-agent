import json


def parse_llm_output(client_response):
    if "Action" in client_response:
        info_part = client_response.split("Action:", 1)[1]
        function_name = info_part.split("Action Input:", 1)[0].strip()
        params = client_response.split("Action Input:", 1)[1].strip()
        params_first_line = params.split("\n")[0].strip()
        try:
            params_str = json.loads(params_first_line)
            response_parsed = {
                "type": "action",
                "function_name": function_name,
                "action_input": params_str,
            }
            return response_parsed
        except json.decoder.JSONDecodeError:
            error_notice = f"Action Input 格式不正确，不是合法JSON"
            response_parsed = {
                "type": "error",
                "error_notice": error_notice,
            }
            return response_parsed

    elif "Final Answer" in client_response:
        final_answer = client_response.split("Final Answer:", 1)[1].strip()
        response_parsed = {
            "type": "final_answer",
            "final_answer": final_answer,
        }
        return response_parsed

    else:
        # 兜底
        raw_text = client_response
        response_parsed = {
            "type": "no_parsed",
            "raw_text": raw_text,
        }
        return response_parsed

