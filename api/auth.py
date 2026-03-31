"""
auth.py — JWT authentication.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

sys.path.insert(0, str(Path(__file__).parent.parent / "detector"))
from config_loader import cfg

_auth_cfg = cfg["auth"]
SECRET_KEY = _auth_cfg["secret_key"]
ALGORITHM  = _auth_cfg["algorithm"]
EXPIRE_MIN = _auth_cfg["token_expire_minutes"]

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Simple flat user store from config (extend to DB later)
_USERS = {u["username"]: u["password"] for u in _auth_cfg.get("users", [])}


def verify_password(plain: str, username: str) -> bool:
    stored = _USERS.get(username)
    if not stored:
        return False
    # Accept plain text (for dev) or bcrypt hash
    if stored.startswith("$2b$"):
        return pwd_context.verify(plain, stored)
    return plain == stored


def create_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MIN)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username not in _USERS:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception
