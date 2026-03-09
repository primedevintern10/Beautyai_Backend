import json
import logging
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, ToolMessage
from .agent import agent
from .tools import _keywords_cache
from .prompts import RECOMMENDER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _extract_products(messages: List[Any]) -> Optional[List[Dict]]:
    """Return the products list from the last successful query_products tool call, or None."""
    product_call_ids: set = set()
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "query_products":
                    product_call_ids.add(tc["id"])

    if not product_call_ids:
        return None

    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.tool_call_id in product_call_ids:
            try:
                content = json.loads(msg.content) if isinstance(msg.content, str) else {}
                if content.get("status") == "success" and content.get("products"):
                    return content["products"]
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass

    return None


async def run_recommender_agent(
    messages: List[Dict[str, str]],
    thread_id: str = "default_session"
) -> Dict[str, Any]:
    """
    Build a fully-formatted system prompt + real message history, then invoke the agent.
    Returns {"response": str, "routine": RoutineOutput | None}.
    """
    last_user_message = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        ""
    )

    # Format system prompt with runtime values (template substitution happens HERE, not inside the agent)
    categories_str = ", ".join(_keywords_cache.get("category", [])) or "null"
    keywords_str = (
        f"concerns: {', '.join(_keywords_cache.get('concerns', []))}\n"
        f"skin_types: {', '.join(_keywords_cache.get('skin_types', []))}\n"
        f"hair_types: {', '.join(_keywords_cache.get('hair_types', []))}\n"
        f"exclusions: {', '.join(_keywords_cache.get('exclusions', []))}"
    )
    formatted_system_prompt = RECOMMENDER_SYSTEM_PROMPT.format(
        available_categories=categories_str,
        db_keywords=keywords_str,
    )

    # Build message list: system prompt + real conversation history + current user message
    conversation = [("system", formatted_system_prompt)]
    for m in messages[:-1]:
        role = "human" if m["role"] == "user" else "assistant"
        conversation.append((role, m["content"]))
    conversation.append(("human", last_user_message))

    logger.info(
        f"[EXECUTOR IN] Thread: {thread_id} | History: {len(messages) - 1} msg(s) | "
        f"Total msgs to LLM: {len(conversation)}\n"
        f"  User Message : {last_user_message[:300]}{'...' if len(last_user_message) > 300 else ''}"
    )

    try:
        result = await agent.ainvoke({"messages": conversation})
        agent_reply = result["messages"][-1].content
        logger.info(
            f"[EXECUTOR OUT] Thread: {thread_id}\n"
            f"  Agent Reply  : {agent_reply[:300]}{'...' if len(agent_reply) > 300 else ''}"
        )
    except Exception as e:
        logger.error(f"[EXECUTOR ERROR] Thread: {thread_id} | {e}", exc_info=True)
        raise

    products = _extract_products(result["messages"])
    if products:
        logger.info(f"[EXECUTOR PRODUCTS] Thread: {thread_id} | Extracted {len(products)} product(s) for frontend")

    return {"response": agent_reply, "products": products}