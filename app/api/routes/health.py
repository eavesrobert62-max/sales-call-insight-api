from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from app.db.postgres import get_db, engine
from app.db.redis_cache import redis_client
from app.core.config import settings
from app.tasks.celery_app import celery_app

router = APIRouter(tags=["health"])

# Prometheus metrics
total_calls_processed = Counter('sales_calls_processed_total', 'Total calls processed')
processing_time = Histogram('sales_call_processing_seconds', 'Time spent processing calls')
active_reps = Gauge('sales_active_reps', 'Number of active reps')
queue_depth = Gauge('celery_queue_depth', 'Number of tasks in queue')


@router.get("/health")
async def health_check(db: Session = None):
    """Comprehensive health check"""
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        if db is None:
            db = next(get_db())
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis connectivity
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "connected"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Celery worker status
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            active_workers = len(stats)
            health_status["checks"]["celery"] = f"{active_workers} workers active"
        else:
            health_status["checks"]["celery"] = "no workers found"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["celery"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Queue depth
    try:
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        if active_tasks:
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            queue_depth.set(total_active)
            health_status["checks"]["queue_depth"] = total_active
        else:
            health_status["checks"]["queue_depth"] = 0
    except Exception as e:
        health_status["checks"]["queue_depth"] = f"error: {str(e)}"
    
    # Processing latency
    try:
        # This would be calculated from recent processing times
        # For now, return a placeholder
        health_status["checks"]["processing_latency_ms"] = 0
    except Exception as e:
        health_status["checks"]["processing_latency_ms"] = f"error: {str(e)}"
    
    return health_status


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    # Update active reps gauge
    from app.db.postgres import SessionLocal
    db = SessionLocal()
    try:
        from app.db.models import Rep
        active_rep_count = db.query(Rep).filter(Rep.is_active == True).count()
        active_reps.set(active_rep_count)
    finally:
        db.close()
    
    return generate_latest()


@router.get("/status")
async def get_status():
    """Simple status endpoint"""
    return {
        "service": "Sales Call Insight API",
        "version": "1.0.0",
        "status": "running",
        "environment": "production"  # Would be dynamic in real deployment
    }
