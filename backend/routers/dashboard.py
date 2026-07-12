import logging
from fastapi import APIRouter, HTTPException
from models.schemas import DashboardStats
from services.data_service import get_dashboard_stats, fetch_datagov_scheme_data
from utils.response import success_response, error_response

logger = logging.getLogger("janniti.dashboard")
router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def dashboard_stats():
    try:
        data = await get_dashboard_stats()
        return success_response(DashboardStats(**data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard stats failed: {e}", exc_info=True)
        return error_response("Failed to fetch dashboard statistics.")

@router.get("/scheme-data/{scheme_id}")
async def scheme_data(scheme_id: str):
    try:
        data = await fetch_datagov_scheme_data(scheme_id)
        if data:
            return success_response(data)
        return error_response("API key not configured or data not available", status_code=404)
    except Exception as e:
        logger.error(f"Scheme data fetch failed: {e}", exc_info=True)
        return error_response("Failed to fetch scheme data.")
