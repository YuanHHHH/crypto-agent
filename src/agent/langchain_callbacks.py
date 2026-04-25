from typing import Any, Optional
from uuid import UUID
import time

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import BaseCallbackHandler
from src.agent.trace import trace_record

class TraceCallback(BaseCallbackHandler):
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.user_question = None
        self.final_answer = None
        self.tool_call_count = 0
        self.total_steps = 0
        self.end_reason = None
        self.status_code = None
        self.total_time = None
        self.log = {}

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        if parent_run_id is None:
            self.tool_call_count = 0
            self.total_steps = 0
            self.status_code = None
            self.end_reason = None
            self.log = {}
            self.start_time = time.time()
            self.user_question = inputs["input"]

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
        inputs: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        self.tool_call_count += 1

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        self.total_steps += 1
        self.tool_call_count += 1

    def on_agent_finish(
            self,
            finish: AgentFinish,
            *,
            run_id: UUID,
            parent_run_id: Optional[UUID] = None,
            **kwargs: Any,
        ) -> Any:
            self.total_steps +=1
            output = finish.return_values.get("output", "")
            if "Agent stopped" in output:
                self.end_reason = "iteration_limit"
            else:
                self.end_reason = "final_answer"

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        self.status_code = "error"

    def on_chain_end(self, outputs, *, run_id, parent_run_id=None, **kwargs):
        if parent_run_id is None:
            self.end_time = time.time()
            self.total_time = self.end_time - self.start_time
            self.final_answer = outputs.get("output", "")
            if not self.end_reason:
                self.end_reason = "unknown"
            trace_record({
                "user_question": self.user_question,
                "final_answer": self.final_answer,
                "total_time": self.total_time,
                "tool_call_count": self.tool_call_count,
                "total_steps": self.total_steps,
                "end_reason": self.end_reason,
            })

