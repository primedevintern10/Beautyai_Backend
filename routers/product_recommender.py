# routers/product_recommender.py
import logging
from fastapi import APIRouter, HTTPException
from product_recommender_agent.schema import RecommendRequest
from product_recommender_agent.executor import run_recommender_agent
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.post("/chat")
async def recommend_chat(body: RecommendRequest):
    try:
        messages = [{"role": m.role, "content": m.content} for m in body.messages]
        response = await run_recommender_agent(messages)
        return {"response": response}
    except Exception as e:
        logger.error(f"Recommender endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Recommender agent failed. Please try again.")
