from celery import current_task
from sqlalchemy.orm import Session
from app.tasks.celery_app import celery_app
from app.db.postgres import SessionLocal, engine
from app.db.models import Call, AnalysisResult
from app.services.insight_generator import insight_generator
from app.api.schemas import ProcessingStatus
import time
import traceback


@celery_app.task(bind=True)
def process_call_analysis(self, call_id: int):
    """Async task to process call analysis"""
    
    # Update task state
    self.update_state(state="PROGRESS", meta={"status": "Starting analysis"})
    
    db = SessionLocal()
    try:
        # Get call from database
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            raise Exception(f"Call {call_id} not found")
        
        # Update status to processing
        call.processing_status = ProcessingStatus.processing
        db.commit()
        
        self.update_state(state="PROGRESS", meta={"status": "Analyzing transcript"})
        
        # Generate comprehensive analysis
        analysis = insight_generator.generate_comprehensive_analysis(
            call.transcript_text, 
            call.metadata_json
        )
        
        self.update_state(state="PROGRESS", meta={"status": "Saving results"})
        
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
        
        # Update call status to completed
        call.processing_status = ProcessingStatus.completed
        db.commit()
        
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Analysis completed",
                "deal_score": analysis.get("deal_score"),
                "processing_time_ms": analysis.get("processing_time_ms")
            }
        )
        
        return {
            "status": "completed",
            "call_id": call_id,
            "deal_score": analysis.get("deal_score"),
            "processing_time_ms": analysis.get("processing_time_ms")
        }
        
    except Exception as e:
        # Update call status to failed
        call = db.query(Call).filter(Call.id == call_id).first()
        if call:
            call.processing_status = ProcessingStatus.failed
            db.commit()
        
        error_msg = f"Analysis failed: {str(e)}"
        self.update_state(
            state="FAILURE",
            meta={"status": error_msg, "error": traceback.format_exc()}
        )
        
        raise Exception(error_msg)
        
    finally:
        db.close()


@celery_app.task
def cleanup_old_analyses():
    """Cleanup task to remove old analysis data (retention policy)"""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Delete analyses older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        old_calls = db.query(Call).filter(
            Call.created_at < cutoff_date,
            Call.processing_status == ProcessingStatus.completed
        ).all()
        
        deleted_count = 0
        for call in old_calls:
            # Delete associated analysis
            analysis = db.query(AnalysisResult).filter(
                AnalysisResult.call_id == call.id
            ).first()
            if analysis:
                db.delete(analysis)
            
            # Delete call
            db.delete(call)
            deleted_count += 1
        
        db.commit()
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        raise Exception(f"Cleanup failed: {str(e)}")
        
    finally:
        db.close()


@celery_app.task
def generate_team_report(team_id: int):
    """Generate comprehensive team performance report"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        # Get team performance data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Query team metrics
        team_metrics = db.query(
            func.count(Call.id).label('total_calls'),
            func.avg(AnalysisResult.deal_score).label('avg_score'),
            func.count(func.case([(AnalysisResult.deal_score < 40, 1)])).label('at_risk_calls')
        ).join(Call, AnalysisResult.call_id == Call.id).filter(
            Call.team_id == team_id,
            Call.created_at >= start_date,
            Call.processing_status == ProcessingStatus.completed
        ).first()
        
        # Get top objections
        objections_data = db.query(
            func.json_extract(AnalysisResult.objections_json, '$[*].category')
        ).join(Call, AnalysisResult.call_id == Call.id).filter(
            Call.team_id == team_id,
            Call.created_at >= start_date,
            Call.processing_status == ProcessingStatus.completed
        ).all()
        
        # Process objections
        objection_counts = {}
        for result in objections_data:
            if result[0]:
                categories = str(result[0]).strip('[]').split(',')
                for cat in categories:
                    cat = cat.strip().strip('"')
                    if cat:
                        objection_counts[cat] = objection_counts.get(cat, 0) + 1
        
        report = {
            "team_id": team_id,
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "metrics": {
                "total_calls": team_metrics.total_calls or 0,
                "avg_deal_score": float(team_metrics.avg_score) if team_metrics.avg_score else 0.0,
                "at_risk_calls": team_metrics.at_risk_calls or 0
            },
            "top_objections": sorted(objection_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return report
        
    except Exception as e:
        raise Exception(f"Report generation failed: {str(e)}")
        
    finally:
        db.close()
