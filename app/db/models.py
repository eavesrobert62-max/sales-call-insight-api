from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.postgres import Base


class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey("reps.id"))
    tier = Column(String, default="professional")  # professional, business
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    reps = relationship("Rep", back_populates="team")
    manager = relationship("Rep", foreign_keys=[manager_id])


class Rep(Base):
    __tablename__ = "reps"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    tier = Column(String, default="professional")
    api_key_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    team = relationship("Team", back_populates="reps")
    calls = relationship("Call", back_populates="rep")
    usage_logs = relationship("UsageLog", back_populates="rep")


class Call(Base):
    __tablename__ = "calls"
    
    id = Column(Integer, primary_key=True, index=True)
    rep_id = Column(Integer, ForeignKey("reps.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    transcript_text = Column(Text)
    metadata_json = Column(JSON)
    audio_url = Column(String)
    duration_seconds = Column(Integer)
    call_type = Column(String)  # discovery, demo, negotiation, close
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    rep = relationship("Rep", back_populates="calls")
    team = relationship("Team")
    analysis = relationship("AnalysisResult", back_populates="call", uselist=False)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id"), unique=True, nullable=False)
    deal_score = Column(Float)
    intent_classification = Column(String)
    sentiment_timeline_json = Column(JSON)
    objections_json = Column(JSON)
    key_topics_json = Column(JSON)
    talk_ratio_json = Column(JSON)
    next_actions_json = Column(JSON)
    competitor_mentions = Column(JSON)
    decision_makers_identified = Column(JSON)
    budget_mentions = Column(JSON)
    timeline_urgency = Column(JSON)
    confidence_score = Column(Float)
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    call = relationship("Call", back_populates="analysis")


class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    rep_id = Column(Integer, ForeignKey("reps.id"), nullable=False)
    endpoint = Column(String, nullable=False)
    transcript_length = Column(Integer)
    processing_time_ms = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    rep = relationship("Rep", back_populates="usage_logs")
