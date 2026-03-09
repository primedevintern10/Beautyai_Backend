# routers/routine_builder.py
import logging
from fastapi import APIRouter, HTTPException
from routine_builder_agent.schema import RoutineRequest, RoutineResponse
from routine_builder_agent.executor import build_routine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routine", tags=["routine"])


@router.post("/build", response_model=RoutineResponse)
async def build_routine_endpoint(body: RoutineRequest):
    """
    Build a personalized AM/PM routine from a list of recommended products.

    Expects:
    - concern, skin_type, allergies: collected during the recommender conversation
    - products: raw product list from the recommender agent's query_products result
    """
    try:
        routine = await build_routine(
            concern=body.concern,
            skin_type=body.skin_type,
            allergies=body.allergies,
            products=body.products,
        )
        return RoutineResponse(
            concern=body.concern,
            skin_type=body.skin_type,
            routine=routine,
        )
    except Exception as e:
        logger.error(f"Routine builder endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Routine builder failed. Please try again.")
