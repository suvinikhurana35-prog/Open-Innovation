"""
Explainer routes.

Fixes:
  * /explain previously called generate_explainer(user_query, context, language)
    — wrong signature; `context` landed in the `language` slot. Now calls it
    correctly (it does its own RAG internally) and returns via success_response.
  * /conditions, /eli5, /search were imported but never registered, so the
    frontend got 404s on every search. They're registered here.
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from models.schemas import PolicyQuery
from services.ai_service import generate_explainer, detect_conditions, generate_eli5
from services.data_service import search_schemes
from services.rag_service import rag_service
from utils.response import success_response, error_response

logger = logging.getLogger("janniti.explainer")
router = APIRouter(prefix="/api/explainer", tags=["Explainer"])


@router.post("/explain")
async def explain_scheme(query: PolicyQuery):
    try:
        result = generate_explainer(query.query, query.language, query.state)
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Explainer failed: {e}", exc_info=True)
        return error_response("Failed to generate explanation. Please try again.")


@router.post("/conditions")
async def conditions(query: PolicyQuery):
    try:
        return success_response(detect_conditions(query.query, query.language))
    except Exception as e:
        logger.error(f"Conditions failed: {e}", exc_info=True)
        return error_response("Failed to analyze conditions. Please try again.")


@router.post("/eli5")
async def eli5(query: PolicyQuery):
    try:
        return success_response(generate_eli5(query.query, query.language))
    except Exception as e:
        logger.error(f"ELI5 failed: {e}", exc_info=True)
        return error_response("Failed to generate explanation. Please try again.")


@router.get("/search")
async def search(q: str = Query(..., description="Search text")):
    try:
        results = await search_schemes(q)
        return success_response({"results": results})
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        return error_response("Search failed. Please try again.")
