# Pydantic 请求/响应 schema
from pydantic import BaseModel
from typing import Any


class ResumeParseResponse(BaseModel):
    resume_id: int
    raw_text: str
    parsed: dict[str, Any]


class ScoreItem(BaseModel):
    name: str
    score: int
    max_score: int
    reason: str


class ScoreResponse(BaseModel):
    record_id: int
    total_score: int
    dimensions: list[ScoreItem]
    summary: str


class OptimizeSuggestion(BaseModel):
    original: str
    improved: str
    reason: str
    type: str          # quantification / wording / structure / keyword
    accepted: bool = False


class OptimizeRequest(BaseModel):
    job_type: str = "product"  # tech / product / operation / design


class OptimizeResponse(BaseModel):
    record_id: int
    job_type: str
    suggestions: list[OptimizeSuggestion]
    optimized_text: str


class MatchRequest(BaseModel):
    jd_text: str


class MatchResponse(BaseModel):
    record_id: int
    match_score: int
    matched: list[str]
    missing: list[str]
    suggestions: list[str]


class ApplySuggestionsRequest(BaseModel):
    accepted_indices: list[int]  # 接受的建议下标
