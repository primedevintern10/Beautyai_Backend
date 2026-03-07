# web_search_agent/agent.py
import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from config.config import OPENAI_API_KEY, MODEL_MINI
from .prompts import SEARCH_AGENT_SYSTEM_PROMPT
from .tools import search_tool
from .schema import LLMLoggerCallback

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=MODEL_MINI,
    temperature=0.7,
    api_key=OPENAI_API_KEY,
    max_retries=2,
    callbacks=[LLMLoggerCallback()],
)

agent = create_agent(
    llm,
    tools=[search_tool],
    system_prompt=SEARCH_AGENT_SYSTEM_PROMPT,
)


async def run_search_agent(query: str) -> str:
    logger.info(f"Search agent received query: {query}")
    try:
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": query}]
        })
        output = result["messages"][-1].content
        logger.info("Search agent completed successfully")
        return output
    except Exception as e:
        logger.error(f"Search agent execution failed: {e}", exc_info=True)
        raise RuntimeError(f"Agent failed to process query: {e}")
