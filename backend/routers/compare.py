import logging
from fastapi import APIRouter, HTTPException
from models.schemas import CompareRequest, RecommendRequest
from services.ai_service import compare_schemes, recommend_for_profile
from utils.response import success_response, error_response

logger = logging.getLogger("janniti.compare")
router = APIRouter(prefix="/api/compare", tags=["Compare"])

@router.post("/")
async def compare(request: CompareRequest):
    try:
        result = compare_schemes(request.scheme1, request.scheme2, request.language)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare failed: {e}", exc_info=True)
        return error_response("Comparison failed. Please try again.")


@router.post("/recommend")
async def recommend(request: RecommendRequest):
    try:
        result = recommend_for_profile(request.scheme1, request.scheme2, request.profile, request.language)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommend failed: {e}", exc_info=True)
        return error_response("Recommendation failed. Please try again.")
