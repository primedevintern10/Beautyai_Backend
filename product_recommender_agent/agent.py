import logging
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from .prompts import RECOMMENDER_SYSTEM_PROMPT
from .tools import query_products
from .schema import LLMLoggerCallback
from config.config import MODEL_MINI

logger = logging.getLogger(__name__)

# LLM
llm = ChatOpenAI(
    model=MODEL_MINI,
    temperature=0.7,
    callbacks=[LLMLoggerCallback()]
)

# Memory
checkpointer = MemorySaver()

# Agent
agent = create_agent(
    model=llm,
    tools=[query_products],
    checkpointer=checkpointer,
    system_prompt=RECOMMENDER_SYSTEM_PROMPT
)