# routers/web_search_agent.py
import logging
from fastapi import APIRouter, HTTPException
from web_search_agent.schema import SearchQuery, BeautyInsightResponse
from web_search_agent.agent import run_search_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search-agent", tags=["search-agent"])


@router.post("/query")
async def query_search_agent(body: SearchQuery):
    try:
        response = await run_search_agent(body.query)
        return {"query": body.query, "response": response}
    except Exception as e:
        logger.error(f"Search agent endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Search agent failed. Please try again.")
