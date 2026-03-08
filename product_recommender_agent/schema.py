# product_recommender_agent/schema.py
import logging
from typing import Any, Dict, List, Literal, Optional
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
        message_count = sum(len(m) for m in messages)
        logger.info(
            f"[LLM START] Model: {model_name} | "
            f"Run ID: {run_id} | "
            f"Messages: {message_count}"
        )

    def on_llm_new_token(self, token: str, *, run_id: str, **__: Any) -> None:
        logger.debug(f"[LLM TOKEN] Run ID: {run_id} | Token: {repr(token)}")

    def on_llm_end(self, response: Any, *, run_id: str, **__: Any) -> None:
        usage = {}
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
        logger.info(
            f"[LLM END] Run ID: {run_id} | "
            f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')} | "
            f"Completion tokens: {usage.get('completion_tokens', 'N/A')} | "
            f"Total tokens: {usage.get('total_tokens', 'N/A')}"
        )

    def on_llm_error(self, error: BaseException, *, run_id: str, **__: Any) -> None:
        logger.error(
            f"[LLM ERROR] Run ID: {run_id} | Error: {str(error)}",
            exc_info=True
        )
