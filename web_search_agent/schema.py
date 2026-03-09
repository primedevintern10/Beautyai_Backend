# web_search_agent/schema.py
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class SearchQuery(BaseModel):
    query: str = Field(..., description="The user's question about skincare, beauty, or products")


class BeautyInsightResponse(BaseModel):
    concern_summary: str = Field(..., description="Explanation of the skin concern or product")
    possible_causes: List[str] = Field(..., description="List of likely reasons/causes")
    beauty_tips: List[str] = Field(..., description="Practical, safe beauty tips or routine suggestions")
    when_to_see_doctor: Optional[str] = Field(None, description="When to consult a dermatologist")
    sources: List[str] = Field(..., description="List of source URLs/domains used")


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

        last_user = next(
            (m for m in reversed(all_msgs) if getattr(m, "type", "") == "human"),
            None
        )
        last_system = next(
            (m for m in reversed(all_msgs) if getattr(m, "type", "") == "system"),
            None
        )

        def truncate(text: str, limit: int = 200) -> str:
            return text[:limit] + "..." if len(text) > limit else text

        user_content = truncate(getattr(last_user, "content", "N/A")) if last_user else "N/A"
        system_content = truncate(getattr(last_system, "content", "N/A")) if last_system else "N/A"

        logger.info(
            f"[LLM START] Model: {model_name} | Run ID: {run_id} | Messages: {message_count}\n"
            f"  Last User   : {user_content}\n"
            f"  Last System : {system_content}"
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


class TavilyLoggerCallback(BaseCallbackHandler):
    """
    Custom callback handler specifically for logging Tavily search tool calls.
    Implements only the methods relevant to tool execution.
    """

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **__: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        logger.info(
            f"[Tavily START] Tool: {tool_name} | "
            f"Run ID: {run_id} | "
            f"Query: {input_str[:500]}{'...' if len(input_str) > 500 else ''}"
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        if isinstance(output, list):
            count = len(output)
            sample = output[0].get("url", "no url") if output else "empty"
            logger.info(
                f"[Tavily END] Success |"
                f"Found {count} results | Sample URL: {sample}"
            )
        else:
            logger.info(
                f"[Tavily END] Success | RUN ID: {run_id} | "
                f"Output: {str(output)[:500]}{'...' if len(str(output)) > 500 else ''}"
            )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: str,
        parent_run_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> None:
        logger.error(
            f"[Tavily ERROR] Run ID: {run_id} | "
            f"Error: {str(error)}",
            exc_info=True
        )
