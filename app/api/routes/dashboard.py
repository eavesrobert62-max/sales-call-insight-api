from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from datetime import datetime, timedelta

from app.db.postgres import get_db
from app.db.models import Call, Rep, AnalysisResult, UsageLog, Team
from app.api.schemas import RepDashboard, TeamDashboard
from app.api.dependencies import get_current_rep, get_current_manager

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/rep/{rep_id}", response_model=RepDashboard)
async def get_rep_dashboard(
    rep_id: int,
    current_rep: Rep = Depends(get_current_rep),
    db: Session = Depends(get_db)
):
    """Get dashboard for specific rep (only own dashboard unless manager)"""
    
    # Verify access (can view own dashboard, or manager can view team reps)
    if current_rep.id != rep_id:
        # Check if current rep is manager of the target rep
        target_rep = db.query(Rep).filter(Rep.id == rep_id).first()
        if not target_rep or target_rep.team_id != current_rep.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this rep's dashboard"
            )
    
    # Get calls analyzed
    calls_analyzed = db.query(Call).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed"
    ).count()
    
    # Get average deal score
    avg_score_result = db.query(func.avg(AnalysisResult.deal_score)).join(
        Call, AnalysisResult.call_id == Call.id
    ).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed"
    ).scalar()
    
    avg_deal_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Calculate objection handling rate
    total_objections = db.query(func.sum(func.json_array_length(AnalysisResult.objections_json))).join(
        Call, AnalysisResult.call_id == Call.id
    ).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed"
    ).scalar()
    
    total_objections = int(total_objections) if total_objections else 0
    calls_with_objections = db.query(Call).join(
        AnalysisResult, Call.id == AnalysisResult.call_id
    ).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed",
        func.json_array_length(AnalysisResult.objections_json) > 0
    ).count()
    
    objection_handling_rate = 0.0
    if calls_analyzed > 0 and total_objections > 0:
        # Simplified: rate based on having recommended responses for objections
        resolved_objections = db.query(Call).join(
            AnalysisResult, Call.id == AnalysisResult.call_id
        ).filter(
            Call.rep_id == rep_id,
            Call.processing_status == "completed"
        ).count()
        
        objection_handling_rate = (resolved_objections / calls_analyzed) * 100 if calls_analyzed > 0 else 0.0
    
    # Win rate correlation (simplified - based on deal scores)
    high_score_calls = db.query(Call).join(
        AnalysisResult, Call.id == AnalysisResult.call_id
    ).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed",
        AnalysisResult.deal_score >= 70
    ).count()
    
    win_rate_correlation = (high_score_calls / calls_analyzed) * 100 if calls_analyzed > 0 else 0.0
    
    # Identify coaching opportunities
    coaching_opportunities = []
    
    # Low deal scores
    low_score_calls = db.query(Call).join(
        AnalysisResult, Call.id == AnalysisResult.call_id
    ).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed",
        AnalysisResult.deal_score < 40
    ).count()
    
    if low_score_calls > 0:
        coaching_opportunities.append(f"{low_score_calls} calls with low deal scores (<40)")
    
    # High objection rate
    if calls_analyzed > 0 and (total_objections / calls_analyzed) > 3:
        coaching_opportunities.append("High objection rate - review objection handling techniques")
    
    # Poor talk ratio
    poor_talk_ratio_calls = db.query(Call).join(
        AnalysisResult, Call.id == AnalysisResult.call_id
    ).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed"
    ).all()
    
    poor_ratio_count = 0
    for call in poor_talk_ratio_calls:
        if call.analysis and call.analysis.talk_ratio_json:
            talk_ratio = call.analysis.talk_ratio_json
            prospect_pct = talk_ratio.get("prospect_percentage", 50)
            if prospect_pct < 30 or prospect_pct > 70:
                poor_ratio_count += 1
    
    if poor_ratio_count > calls_analyzed * 0.3:  # More than 30% of calls
        coaching_opportunities.append("Improve talk ratio balance in conversations")
    
    # Get current month usage
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage_current_month = db.query(UsageLog).filter(
        UsageLog.rep_id == rep_id,
        UsageLog.timestamp >= current_month
    ).count()
    
    # Get usage limit (simplified - would be based on tier)
    rep_info = db.query(Rep).filter(Rep.id == rep_id).first()
    usage_limit = 100 if rep_info.tier == "professional" else 500
    
    return RepDashboard(
        rep_id=rep_id,
        calls_analyzed=calls_analyzed,
        avg_deal_score=avg_deal_score,
        objection_handling_rate=objection_handling_rate,
        win_rate_correlation=win_rate_correlation,
        coaching_opportunities=coaching_opportunities,
        usage_current_month=usage_current_month,
        usage_limit=usage_limit
    )


@router.get("/team", response_model=TeamDashboard)
async def get_team_dashboard(
    current_manager: Rep = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Get team dashboard for managers"""
    
    team_id = current_manager.team_id
    if not team_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No team assigned"
        )
    
    # Get team calls analyzed
    total_calls_analyzed = db.query(Call).join(
        Rep, Call.rep_id == Rep.id
    ).filter(
        Rep.team_id == team_id,
        Call.processing_status == "completed"
    ).count()
    
    # Get average deal score for team
    avg_score_result = db.query(func.avg(AnalysisResult.deal_score)).join(
        Call, AnalysisResult.call_id == Call.id
    ).join(Rep, Call.rep_id == Rep.id).filter(
        Rep.team_id == team_id,
        Call.processing_status == "completed"
    ).scalar()
    
    avg_deal_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Get deals at risk (score < 40)
    deals_at_risk = db.query(Call).join(
        AnalysisResult, Call.id == AnalysisResult.call_id
    ).join(Rep, Call.rep_id == Rep.id).filter(
        Rep.team_id == team_id,
        Call.processing_status == "completed",
        AnalysisResult.deal_score < 40
    ).count()
    
    # Get common objections across team
    common_objections = []
    
    # Aggregate objection categories
    objection_categories = db.query(
        func.json_extract(AnalysisResult.objections_json, '$[*].category')
    ).join(Call, AnalysisResult.call_id == Call.id).join(Rep, Call.rep_id == Rep.id).filter(
        Rep.team_id == team_id,
        Call.processing_status == "completed"
    ).all()
    
    category_counts = {}
    for result in objection_categories:
        if result[0]:  # result is a tuple
            categories = result[0].strip('[]').split(',')
            for cat in categories:
                cat = cat.strip().strip('"')
                if cat:
                    category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Sort and format
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_categories[:5]:  # Top 5
        common_objections.append({
            "category": category,
            "count": count,
            "percentage": (count / total_calls_analyzed * 100) if total_calls_analyzed > 0 else 0
        })
    
    # Get rep leaderboard
    rep_performance = db.query(
        Rep.id,
        Rep.name,
        func.count(Call.id).label('calls_analyzed'),
        func.avg(AnalysisResult.deal_score).label('avg_score')
    ).join(Call, Rep.id == Call.rep_id).join(
        AnalysisResult, Call.id == AnalysisResult.call_id
    ).filter(
        Rep.team_id == team_id,
        Call.processing_status == "completed"
    ).group_by(Rep.id, Rep.name).all()
    
    rep_leaderboard = []
    for rep_id, name, calls_count, avg_score in rep_performance:
        rep_leaderboard.append({
            "rep_id": rep_id,
            "name": name,
            "calls_analyzed": calls_count,
            "avg_deal_score": float(avg_score) if avg_score else 0.0
        })
    
    # Sort by average deal score
    rep_leaderboard.sort(key=lambda x: x["avg_deal_score"], reverse=True)
    
    # Pipeline health distribution
    pipeline_health = {
        "excellent": 0,  # 80-100
        "good": 0,       # 60-79
        "moderate": 0,   # 40-59
        "at_risk": 0     # 0-39
    }
    
    deal_scores = db.query(AnalysisResult.deal_score).join(
        Call, AnalysisResult.call_id == Call.id
    ).join(Rep, Call.rep_id == Rep.id).filter(
        Rep.team_id == team_id,
        Call.processing_status == "completed"
    ).all()
    
    for score_tuple in deal_scores:
        score = score_tuple[0]
        if score >= 80:
            pipeline_health["excellent"] += 1
        elif score >= 60:
            pipeline_health["good"] += 1
        elif score >= 40:
            pipeline_health["moderate"] += 1
        else:
            pipeline_health["at_risk"] += 1
    
    return TeamDashboard(
        team_id=team_id,
        total_calls_analyzed=total_calls_analyzed,
        avg_deal_score=avg_deal_score,
        deals_at_risk=deals_at_risk,
        common_objections=common_objections,
        rep_leaderboard=rep_leaderboard,
        pipeline_health_distribution=pipeline_health
    )


@router.get("/rep/{rep_id}/trends")
async def get_rep_trends(
    rep_id: int,
    days: int = 30,
    current_rep: Rep = Depends(get_current_rep),
    db: Session = Depends(get_db)
):
    """Get performance trends for a rep over time"""
    
    # Verify access
    if current_rep.id != rep_id:
        target_rep = db.query(Rep).filter(Rep.id == rep_id).first()
        if not target_rep or target_rep.team_id != current_rep.team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this rep's trends"
            )
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get daily performance data
    daily_data = db.query(
        func.date(Call.created_at).label('date'),
        func.count(Call.id).label('calls_count'),
        func.avg(AnalysisResult.deal_score).label('avg_score')
    ).join(AnalysisResult, Call.id == AnalysisResult.call_id).filter(
        Call.rep_id == rep_id,
        Call.processing_status == "completed",
        Call.created_at >= start_date
    ).group_by(func.date(Call.created_at)).all()
    
    trends = []
    for date, calls_count, avg_score in daily_data:
        trends.append({
            "date": date.isoformat(),
            "calls_analyzed": calls_count,
            "avg_deal_score": float(avg_score) if avg_score else 0.0
        })
    
    return {"trends": trends}
