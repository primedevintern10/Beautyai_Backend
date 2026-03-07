# web_search_agent/tools.py
import logging
from typing import Any, Dict, Optional
from langchain_tavily import TavilySearch
from web_search_agent.schema import TavilyLoggerCallback
from config.config import TAVILY_API_KEY

logger = logging.getLogger(__name__)

search_tool = TavilySearch(
    max_results=6,
    api_key=TAVILY_API_KEY,
    include_domains=[
        "healthline.com",
        "mayoclinic.org",
        "aad.org",
        "webmd.com",
        "paulaschoice.com",
        "dermstore.com",
        "sephora.com"
    ],
    name="web_search",
    description="Search the web for reliable information about skincare products, ingredients, and skin concerns.",
    callbacks=[TavilyLoggerCallback()],  
)