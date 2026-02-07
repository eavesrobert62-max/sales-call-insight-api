from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.db.postgres import engine
from app.db.models import Base
from app.api.routes import calls, dashboard, health, auth
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting Sales Call Insight API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created")
    
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(calls.router)
app.include_router(dashboard.router)
app.include_router(health.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Sales Call Insight API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return HTTPException(status_code=404, detail="Endpoint not found")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
