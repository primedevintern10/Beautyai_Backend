# product_recommender_agent/schema.py
import logging
from typing import Any, Dict, List, Literal
from pydantic import BaseModel, Field
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class RecommendRequest(BaseModel):
    messages: List[ChatMessage] = Field(
        ..., description="Full conversation history including the latest user message"
    )


class RecommendResponse(BaseModel):
    response: str


class LLMLoggerCallback(BaseCallbackHandler):
    """Tracks LLM call lifecycle: start, token streaming, completion, and errors."""

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        *,
        run_id: str,
        **__: Any,
    ) -> None:
        model_name = serialized.get("kwargs", {}).get("model_name", "unknown_model")
        all_msgs = [msg for batch in messages for msg in batch]
        message_count = len(all_msgs)

        last_system = next(
            (m for m in reversed(all_msgs) if getattr(m, "type", "") == "system"),
            None
        )

        # Show only first line of system prompt to keep log clean
        raw_system = getattr(last_system, "content", "") if last_system else ""
        system_summary = (raw_system.split("\n")[0])[:120]

        logger.info(
            f"[LLM START] Model: {model_name} | Run ID: {run_id} | Messages: {message_count} | "
            f"System: {system_summary}"
        )

    def on_llm_new_token(self, token: str, *, run_id: str, **__: Any) -> None:
        logger.debug(f"[LLM TOKEN] Run ID: {run_id} | Token: {repr(token)}")

    def on_llm_end(self, response: Any, *, run_id: str, **__: Any) -> None:
        usage = {}
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})

        tokens = (
            f"Prompt: {usage.get('prompt_tokens', 'N/A')} | "
            f"Completion: {usage.get('completion_tokens', 'N/A')} | "
            f"Total: {usage.get('total_tokens', 'N/A')}"
        )

        # Only log output for tool calls — text replies are already shown in [EXECUTOR OUT]
        gens = getattr(response, "generations", None)
        tool_call_label = ""
        if gens and gens[0]:
            msg = getattr(gens[0][0], "message", None)
            tool_calls = getattr(msg, "tool_calls", [])
            if tool_calls:
                names = [tc.get("name", "?") for tc in tool_calls]
                tool_call_label = f" | Output: [tool call] -> {', '.join(names)}"

        logger.info(f"[LLM END] Run ID: {run_id} | {tokens}{tool_call_label}")

    def on_llm_error(self, error: BaseException, *, run_id: str, **__: Any) -> None:
        logger.error(
            f"[LLM ERROR] Run ID: {run_id} | Error: {str(error)}",
            exc_info=True
        )
