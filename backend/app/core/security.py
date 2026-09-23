from datetime import datetime, timedelta
from typing import Optional, Union
from jose import jwt, JWTError
import bcrypt
from app.core.config import settings

# bcrypt has a 72-byte password limit - truncate input consistently before hashing
def _prepare(password: str) -> bytes:
    return password.encode("utf-8")[:72]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")

def create_access_token(subject: Union[str, int], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
