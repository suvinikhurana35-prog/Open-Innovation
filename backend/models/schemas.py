from pydantic import BaseModel
from typing import Optional, List


class PolicyQuery(BaseModel):
    query: str
    language: str = "en"
    state: Optional[str] = None


class ConversationTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = None   # fixes "chat forgets" bug
    language: str = "en"
    profile: Optional[dict] = None   # user profile -> personalised, no questions


class CompareRequest(BaseModel):
    scheme1: str
    scheme2: str
    language: str = "en"


class RecommendRequest(BaseModel):
    scheme1: str
    scheme2: str
    profile: dict = {}
    language: str = "en"


class ExplainerResponse(BaseModel):
    title: str
    what_is: str
    why_introduced: str
    benefits: List[str]
    eligibility: List[str]
    documents: List[str]
    how_to_apply: str
    deadlines: Optional[str]
    misunderstood_clauses: List[str]
    source: str
    ministry: str
    last_updated: str
    confidence: str
    disclaimer: str


class DashboardStats(BaseModel):
    total_beneficiaries: str
    total_funds_disbursed: str
    state_coverage: List[dict]
    last_updated: str
    source: str
    top_schemes: Optional[List[dict]] = None
    is_illustrative: bool = False   # honest labelling (bug #6)


class ChatResponse(BaseModel):
    reply: str
    sources: List[str]
    confidence: str
    faithfulness: Optional[float] = None     # RAGAS-style grounding score
    grounded: Optional[bool] = None


class ELI5Response(BaseModel):
    story: str
    simple_explanation: str
    everyday_example: str
    key_takeaway: str
