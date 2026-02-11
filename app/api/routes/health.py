from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.postgres import get_db
import os

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    """
    health_status = {
        "status": "healthy",
        "service": "sales-call-insight-api",
        "version": "1.0.0",
        "environment": "production" if os.getenv("RAILWAY_ENVIRONMENT") else "development"
    }
    
    # Check database connectivity
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
        health_status["database_error"] = str(e)[:100]
    
    return health_status


@router.get("/status")
async def simple_status():
    """
    Simple status check - always returns 200
    """
    return {"status": "ok"}
