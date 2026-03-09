import logging
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from .tools import query_products
from .schema import LLMLoggerCallback
from config.config import MODEL

logger = logging.getLogger(__name__)

# LLM
llm = ChatOpenAI(
    model=MODEL,
    temperature=0.7,
    callbacks=[LLMLoggerCallback()]
)

agent = create_agent(
    model=llm,
    tools=[query_products],
)