from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import time

from app.db.postgres import get_db
from app.db.models import Call, Rep, AnalysisResult, UsageLog
from app.api.schemas import (
    CallUpload, CallResponse, AnalysisRequest, AnalysisResponse,
    ProcessingStatus
)
from app.api.dependencies import get_current_rep, check_usage_limit
from app.services.insight_generator import insight_generator
from app.tasks.celery_tasks import process_call_analysis

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/upload", response_model=CallResponse)
async def upload_call(
    call_data: CallUpload,
    current_rep: Rep = Depends(get_current_rep),
    db: Session = Depends(get_db)
):
    """Upload a new call transcript for analysis"""
    
    # Validate transcript length
    if call_data.transcript_text and len(call_data.transcript_text) > 50000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript too long (max 50,000 characters)"
        )
    
    # Check usage limits
    transcript_length = len(call_data.transcript_text) if call_data.transcript_text else 0
    if not await check_usage_limit(current_rep, transcript_length):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Usage limit exceeded"
        )
    
    # Create call record
    call = Call(
        rep_id=current_rep.id,
        team_id=current_rep.team_id,
        transcript_text=call_data.transcript_text,
        metadata_json=call_data.metadata.dict() if call_data.metadata else None,
        audio_url=call_data.audio_url,
        duration_seconds=call_data.metadata.call_duration if call_data.metadata else None,
        call_type=call_data.metadata.call_type.value if call_data.metadata and call_data.metadata.call_type else None,
        processing_status=ProcessingStatus.pending
    )
    
    db.add(call)
    db.commit()
    db.refresh(call)
    
    # Log usage
    usage_log = UsageLog(
        rep_id=current_rep.id,
        endpoint="/calls/upload",
        transcript_length=transcript_length,
        processing_time_ms=0
    )
    db.add(usage_log)
    db.commit()
    
    # Start async processing if transcript provided
    if call_data.transcript_text:
        process_call_analysis.delay(call.id)
    
    return CallResponse(
        id=call.id,
        rep_id=call.rep_id,
        processing_status=call.processing_status,
        created_at=call.created_at
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_call(
    request: AnalysisRequest,
    current_rep: Rep = Depends(get_current_rep),
    db: Session = Depends(get_db)
):
    """Analyze a call (by ID or inline transcript)"""
    
    start_time = time.time()
    
    if request.call_id:
        # Analyze existing call
        call = db.query(Call).filter(
            Call.id == request.call_id,
            Call.rep_id == current_rep.id
        ).first()
        
        if not call:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Call not found"
            )
        
        if not call.transcript_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for this call"
            )
        
        transcript = call.transcript_text
        metadata = call.metadata_json
        call_id = call.id
        
    elif request.transcript_text:
        # Analyze inline transcript
        transcript = request.transcript_text
        metadata = None
        call_id = None
        
        # Check usage limits
        if not await check_usage_limit(current_rep, len(transcript)):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Usage limit exceeded"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either call_id or transcript_text must be provided"
        )
    
    try:
        # Generate analysis
        analysis = await insight_generator.generate_comprehensive_analysis(transcript, metadata)
        
        # If analyzing existing call, save results
        if request.call_id:
            # Update call status
            call.processing_status = ProcessingStatus.completed
            call.updated_at = datetime.utcnow()
            
            # Save analysis results
            existing_analysis = db.query(AnalysisResult).filter(
                AnalysisResult.call_id == call_id
            ).first()
            
            if existing_analysis:
                # Update existing analysis
                existing_analysis.deal_score = analysis.get("deal_score")
                existing_analysis.intent_classification = analysis.get("intent_classification")
                existing_analysis.sentiment_timeline_json = analysis.get("sentiment_timeline")
                existing_analysis.objections_json = analysis.get("detected_objections")
                existing_analysis.key_topics_json = analysis.get("key_topics")
                existing_analysis.talk_ratio_json = analysis.get("talk_ratio")
                existing_analysis.next_actions_json = analysis.get("next_best_actions")
                existing_analysis.competitor_mentions = analysis.get("competitor_mentions")
                existing_analysis.decision_makers_identified = analysis.get("decision_makers_identified")
                existing_analysis.budget_mentions = analysis.get("budget_mentions")
                existing_analysis.timeline_urgency = analysis.get("timeline_urgency")
                existing_analysis.confidence_score = analysis.get("confidence_score")
                existing_analysis.processing_time_ms = analysis.get("processing_time_ms")
            else:
                # Create new analysis record
                analysis_result = AnalysisResult(
                    call_id=call_id,
                    deal_score=analysis.get("deal_score"),
                    intent_classification=analysis.get("intent_classification"),
                    sentiment_timeline_json=analysis.get("sentiment_timeline"),
                    objections_json=analysis.get("detected_objections"),
                    key_topics_json=analysis.get("key_topics"),
                    talk_ratio_json=analysis.get("talk_ratio"),
                    next_actions_json=analysis.get("next_best_actions"),
                    competitor_mentions=analysis.get("competitor_mentions"),
                    decision_makers_identified=analysis.get("decision_makers_identified"),
                    budget_mentions=analysis.get("budget_mentions"),
                    timeline_urgency=analysis.get("timeline_urgency"),
                    confidence_score=analysis.get("confidence_score"),
                    processing_time_ms=analysis.get("processing_time_ms")
                )
                db.add(analysis_result)
            
            db.commit()
        
        # Log usage
        processing_time = int((time.time() - start_time) * 1000)
        usage_log = UsageLog(
            rep_id=current_rep.id,
            endpoint="/calls/analyze",
            transcript_length=len(transcript),
            processing_time_ms=processing_time
        )
        db.add(usage_log)
        db.commit()
        
        # Return response
        return AnalysisResponse(
            call_id=call_id or 0,
            deal_score=analysis.get("deal_score", 0),
            intent_classification=analysis.get("intent_classification", "researching"),
            detected_objections=analysis.get("detected_objections", []),
            talk_ratio=analysis.get("talk_ratio", {"rep_percentage": 50, "prospect_percentage": 50, "total_words": 0}),
            sentiment_timeline=analysis.get("sentiment_timeline", []),
            key_topics=analysis.get("key_topics", []),
            decision_makers_identified=analysis.get("decision_makers_identified", []),
            budget_mentions=analysis.get("budget_mentions", []),
            timeline_urgency=analysis.get("timeline_urgency", []),
            competitor_mentions=analysis.get("competitor_mentions", []),
            next_best_actions=analysis.get("next_best_actions", []),
            confidence_score=analysis.get("confidence_score", 0),
            processing_time_ms=analysis.get("processing_time_ms", 0)
        )
        
    except Exception as e:
        # Update call status to failed if applicable
        if request.call_id:
            call.processing_status = ProcessingStatus.failed
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/{call_id}/insights", response_model=AnalysisResponse)
async def get_call_insights(
    call_id: int,
    current_rep: Rep = Depends(get_current_rep),
    db: Session = Depends(get_db)
):
    """Get processed analysis for a specific call"""
    
    # Verify call belongs to current rep
    call = db.query(Call).filter(
        Call.id == call_id,
        Call.rep_id == current_rep.id
    ).first()
    
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    
    # Get analysis results
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.call_id == call_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this call"
        )
    
    return AnalysisResponse(
        call_id=call_id,
        deal_score=analysis.deal_score or 0,
        intent_classification=analysis.intent_classification or "researching",
        detected_objections=analysis.objections_json or [],
        talk_ratio=analysis.talk_ratio_json or {"rep_percentage": 50, "prospect_percentage": 50, "total_words": 0},
        sentiment_timeline=analysis.sentiment_timeline_json or [],
        key_topics=analysis.key_topics_json or [],
        decision_makers_identified=analysis.decision_makers_identified or [],
        budget_mentions=analysis.budget_mentions or [],
        timeline_urgency=analysis.timeline_urgency or [],
        competitor_mentions=analysis.competitor_mentions or [],
        next_best_actions=analysis.next_actions_json or [],
        confidence_score=analysis.confidence_score or 0,
        processing_time_ms=analysis.processing_time_ms or 0
    )


@router.get("/", response_model=List[CallResponse])
async def list_calls(
    skip: int = 0,
    limit: int = 50,
    current_rep: Rep = Depends(get_current_rep),
    db: Session = Depends(get_db)
):
    """List calls for current rep"""
    
    calls = db.query(Call).filter(
        Call.rep_id == current_rep.id
    ).offset(skip).limit(limit).all()
    
    return [
        CallResponse(
            id=call.id,
            rep_id=call.rep_id,
            processing_status=call.processing_status,
            created_at=call.created_at
        )
        for call in calls
    ]
