from fastapi import Depends, HTTPException, status, Request
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if token.startswith('demo_mode_token_'):
            # Return a mock user for demo mode so backend features still work
            mock_user = db.query(User).filter(User.id == 9999).first()
            if not mock_user:
                mock_user = User(id=9999, email="demo@example.com", name="Demo User", password_hash="dummy")
                db.add(mock_user)
                try:
                    db.commit()
                    db.refresh(mock_user)
                except Exception:
                    db.rollback()
                    mock_user = db.query(User).filter(User.id == 9999).first()
            return mock_user
            
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        if token.startswith('demo_mode_token_'):
            return db.query(User).filter(User.id == 9999).first()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id:
            return db.query(User).filter(User.id == int(user_id)).first()
    except Exception:
        pass
    return None
