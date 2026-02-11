from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os

from app.db.postgres import engine
from app.db.models import Base
from app.api.routes import calls, dashboard, health, auth
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Sales Call Insight API...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Sales Call Insight API",
    description="Production-ready API for analyzing sales call transcripts and generating deal intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
cors_origins = getattr(settings, 'cors_origins', ["*"])
if isinstance(cors_origins, str):
    cors_origins = cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(calls.router, prefix="/calls", tags=["Calls"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(health.router, prefix="", tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sales Call Insight API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
