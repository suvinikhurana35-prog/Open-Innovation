"""
Data service — honest version (fixes bug #6).

Before: the dashboard returned hard-typed numbers presented as live data.gov.in
data, and search returned a hand-typed scheme list that didn't match the actual
PDFs. Now:
  * search_schemes() is driven by the REAL scheme names derived from the PDFs
    in data/chroma/policies/ (single source of truth: ingest_pdfs).
  * get_dashboard_stats() is explicitly flagged is_illustrative=True and counts
    the real number of indexed schemes; it no longer pretends to be live.
  * fetch_datagov_scheme_data() only returns data if a real DATAGOV_API_KEY +
    dataset id are configured, else None (the placeholder ids returned nothing).
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict

import requests

import config

# ingest_pdfs pulls in pypdf/langchain (heavy). In lite deployment those aren't
# installed, so fall back to listing schemes from the curated KB instead.
try:
    from scripts.ingest_pdfs import list_known_schemes
except Exception:  # pragma: no cover - lite mode
    def list_known_schemes():
        try:
            from services import kb_service
            return kb_service.scheme_names()
        except Exception:
            return []

logger = logging.getLogger("janniti.data")

DATAGOV_BASE = "https://api.data.gov.in/resource"
# Real dataset ids only — left empty by design. Add a verified id + key to enable.
SCHEME_DATASETS: Dict[str, str] = {}


def _ministry_guess(name: str) -> str:
    n = name.lower()
    if any(w in n for w in ("kisan", "fasal", "bima yojna", "samman nidhi")):
        return "Ministry of Agriculture & Farmers Welfare"
    if any(w in n for w in ("scholarship", "talent", "research fellowship", "single girl")):
        return "Ministry of Education"
    if any(w in n for w in ("kaushal", "skill", "rozgar")):
        return "Ministry of Skill Development & Entrepreneurship"
    if any(w in n for w in ("mudra", "jan dhan", "jeevan jyoti", "suraksha", "stand up", "loan")):
        return "Ministry of Finance"
    if "garib kalyan" in n:
        return "Ministry of Consumer Affairs, Food & Public Distribution"
    if "pension" in n:
        return "Ministry of Finance (PFRDA)"
    return "Government of India"


async def fetch_datagov_scheme_data(scheme_id: str) -> Optional[Dict]:
    if not config.DATAGOV_API_KEY:
        return None
    dataset_id = SCHEME_DATASETS.get(scheme_id)
    if not dataset_id:
        return None
    try:
        resp = requests.get(f"{DATAGOV_BASE}/{dataset_id}",
                            params={"api-key": config.DATAGOV_API_KEY, "format": "json", "limit": 100},
                            timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"data.gov.in fetch failed: {e}")
    return None


async def search_schemes(query: str) -> List[Dict]:
    """Search the REAL ingested schemes (from the PDF filenames)."""
    schemes = []
    for name in list_known_schemes():
        slug = name.lower().replace(" ", "-")
        schemes.append({"id": slug, "name": name, "ministry": _ministry_guess(name),
                        "type": "Central", "source": "Ingested official PDF"})
    q = query.lower().strip()
    if not q:
        return schemes[:10]
    hits = [s for s in schemes if q in s["name"].lower()]
    if not hits:
        words = q.split()
        hits = [s for s in schemes if any(w in s["name"].lower() for w in words)]
    return hits[:10]


async def get_dashboard_stats() -> Dict:
    """Illustrative dashboard — clearly flagged, with the real indexed count."""
    real_schemes = list_known_schemes()
    return {
        "total_beneficiaries": "Illustrative — not live data",
        "total_funds_disbursed": "Illustrative — not live data",
        # Honest coverage: these are CENTRAL schemes available across all states.
        # We do not invent per-state beneficiary counts (that would be hallucination).
        "state_coverage": [
            {"state": "All India (Central scheme)", "schemes": len(real_schemes), "beneficiaries": "See official portal"}
        ],
        "last_updated": datetime.now().strftime("%B %d, %Y"),
        "source": (f"JanNiti knowledge base: {len(real_schemes)} official scheme documents indexed. "
                   "Headline figures are illustrative placeholders, not live government statistics. "
                   "For live data see data.gov.in / myscheme.gov.in."),
        "top_schemes": [{"name": n, "beneficiaries": "See official portal", "funds": "See official portal"}
                        for n in real_schemes[:6]],
        "is_illustrative": True,
    }
