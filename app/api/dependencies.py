from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.db.postgres import get_db
from app.db.models import Rep
from app.core.config import settings
from typing import Optional

security = HTTPBearer()


async def get_current_rep(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Rep:
    """Get current authenticated rep"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        rep_id: int = payload.get("sub")
        if rep_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    rep = db.query(Rep).filter(Rep.id == rep_id).first()
    if rep is None:
        raise credentials_exception
    
    if not rep.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive rep"
        )
    
    return rep


async def get_current_manager(current_rep: Rep = Depends(get_current_rep)) -> Rep:
    """Ensure current user is a manager"""
    # In a real implementation, you'd check role/permissions
    # For now, we'll assume reps with team_id are managers
    if not current_rep.team_id:  # Simplified check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_rep


async def check_usage_limit(rep: Rep, transcript_length: int = 0) -> bool:
    """Check if rep has exceeded usage limits"""
    from datetime import datetime, timedelta
    from app.db.models import UsageLog
    
    # Get current month usage
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # This would be implemented with actual database queries
    # For now, return True (within limits)
    return True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
