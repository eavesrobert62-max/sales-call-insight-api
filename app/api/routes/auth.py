from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from app.db.postgres import get_db
from app.db.models import Rep, Team
from app.api.dependencies import create_access_token, get_current_rep
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    rep_id: int
    name: str
    tier: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    team_name: Optional[str] = None
    tier: str = "professional"  # professional, business


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)


def authenticate_rep(db: Session, email: str, password: str) -> Rep:
    """Authenticate rep credentials"""
    rep = db.query(Rep).filter(Rep.email == email).first()
    if not rep or not verify_password(password, rep.api_key_hash):
        return None
    return rep


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint for reps"""
    
    rep = authenticate_rep(db, login_data.email, login_data.password)
    if not rep:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not rep.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive account"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(rep.id)}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        rep_id=rep.id,
        name=rep.name,
        tier=rep.tier
    )


@router.post("/register", response_model=LoginResponse)
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register new rep (and optionally create team)"""
    
    # Check if email already exists
    existing_rep = db.query(Rep).filter(Rep.email == register_data.email).first()
    if existing_rep:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create team if provided and doesn't exist
    team_id = None
    if register_data.team_name:
        existing_team = db.query(Team).filter(Team.name == register_data.team_name).first()
        if existing_team:
            team_id = existing_team.id
        else:
            # Create new team
            new_team = Team(
                name=register_data.team_name,
                tier=register_data.tier
            )
            db.add(new_team)
            db.commit()
            db.refresh(new_team)
            team_id = new_team.id
    
    # Create new rep
    hashed_password = get_password_hash(register_data.password)
    new_rep = Rep(
        name=register_data.name,
        email=register_data.email,
        team_id=team_id,
        tier=register_data.tier,
        api_key_hash=hashed_password,
        is_active=True
    )
    
    db.add(new_rep)
    db.commit()
    db.refresh(new_rep)
    
    # If this is the first rep in a team, make them the manager
    if team_id:
        team_reps = db.query(Rep).filter(Rep.team_id == team_id).count()
        if team_reps == 1:
            team = db.query(Team).filter(Team.id == team_id).first()
            team.manager_id = new_rep.id
            db.commit()
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(new_rep.id)}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        rep_id=new_rep.id,
        name=new_rep.name,
        tier=new_rep.tier
    )


@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token removal)"""
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(current_rep: Rep = Depends(get_current_rep)):
    """Get current user information"""
    return {
        "id": current_rep.id,
        "name": current_rep.name,
        "email": current_rep.email,
        "team_id": current_rep.team_id,
        "tier": current_rep.tier,
        "is_active": current_rep.is_active
    }
