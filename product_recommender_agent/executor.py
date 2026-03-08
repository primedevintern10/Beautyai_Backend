import logging
from typing import List, Dict
from .agent import agent
from config.database import _CACHED_CATEGORIES

logger = logging.getLogger(__name__)

async def run_recommender_agent(
    messages: List[Dict[str, str]],
    thread_id: str = "default_session"
) -> str:
    """
    Convert user messages to agent input with chat history.
    """

    logger.info(f"Agent called with {len(messages)} messages")

    last_user_message = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"),
        ""
    )

    # Build chat_history string
    chat_history_lines = []
    for m in messages[:-1]:
        role = "User" if m["role"] == "user" else "Assistant"
        chat_history_lines.append(f"{role}: {m['content']}")
    chat_history = "\n".join(chat_history_lines)

    # Available categories at runtime
    categories_str = ", ".join(_CACHED_CATEGORIES) if _CACHED_CATEGORIES else "face, hair, body, baby"

    try:
        result = await agent.ainvoke(
            {
                "messages": [("user", last_user_message)],
                "input": last_user_message,
                "chat_history": chat_history,
                "available_categories": categories_str
            },
            config={"configurable": {"thread_id": thread_id}}
        )
        return result["messages"][-1].content

    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise