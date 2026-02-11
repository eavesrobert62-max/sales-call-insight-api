from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CallType(str, Enum):
    discovery = "discovery"
    demo = "demo"
    negotiation = "negotiation"
    close = "close"


class ProcessingStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class IntentClassification(str, Enum):
    researching = "researching"
    comparing = "comparing"
    ready_to_buy = "ready_to_buy"
    stalled = "stalled"


class CallMetadata(BaseModel):
    prospect_company: Optional[str] = None
    deal_value: Optional[float] = None
    call_duration: Optional[int] = None
    call_type: Optional[CallType] = None


class CallUpload(BaseModel):
    transcript_text: Optional[str] = None
    metadata: Optional[CallMetadata] = None
    audio_url: Optional[str] = None


class CallResponse(BaseModel):
    id: int
    rep_id: int
    processing_status: ProcessingStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class Objection(BaseModel):
    text: str
    timestamp: Optional[float] = None
    category: Optional[str] = None
    recommended_response: Optional[str] = None


class TalkRatio(BaseModel):
    rep_percentage: float
    prospect_percentage: float
    total_words: int


class SentimentPoint(BaseModel):
    timestamp: float
    sentiment_score: float  # -1 to 1
    engagement_level: float  # 0 to 1


class NextAction(BaseModel):
    action: str
    priority: int  # 1-5, 1 being highest
    due_date: Optional[str] = None
    owner: Optional[str] = None


class AnalysisRequest(BaseModel):
    call_id: Optional[int] = None
    transcript_text: Optional[str] = None


class AnalysisResponse(BaseModel):
    call_id: int
    deal_score: float = Field(ge=0, le=100)
    intent_classification: IntentClassification
    detected_objections: List[Objection]
    talk_ratio: TalkRatio
    sentiment_timeline: List[SentimentPoint]
    key_topics: List[str]
    decision_makers_identified: List[str]
    budget_mentions: List[str]
    timeline_urgency: List[str]
    competitor_mentions: List[str]
    next_best_actions: List[NextAction]
    confidence_score: float = Field(ge=0, le=1)
    processing_time_ms: int


class RepDashboard(BaseModel):
    rep_id: int
    calls_analyzed: int
    avg_deal_score: float
    objection_handling_rate: float
    win_rate_correlation: float
    coaching_opportunities: List[str]
    usage_current_month: int
    usage_limit: int


class TeamDashboard(BaseModel):
    team_id: int
    total_calls_analyzed: int
    avg_deal_score: float
    deals_at_risk: int  # score < 40
    common_objections: List[Dict[str, Any]]
    rep_leaderboard: List[Dict[str, Any]]
    pipeline_health_distribution: Dict[str, int]


class HealthResponse(BaseModel):
    status: str
    queue_depth: int
    processing_latency_ms: int
    database_connected: bool
    redis_connected: bool


class MetricsResponse(BaseModel):
    total_calls_processed: int
    avg_processing_time_ms: float
    deal_score_distribution: Dict[str, int]
    objection_type_counts: Dict[str, int]
    active_reps: int
    api_calls_last_hour: int
