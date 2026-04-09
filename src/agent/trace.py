import os
import json
from src.utils.config import TRACE_FILE
import datetime
def trace_record(new_record):
    """
    记录trace，便于后续评估质量和找错
    :param new_record:
    :return:
    """
    new_record["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(TRACE_FILE), exist_ok=True)
    with open(TRACE_FILE, "a") as f:
        f.write(json.dumps(new_record)+ "\n")
