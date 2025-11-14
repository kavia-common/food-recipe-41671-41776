from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from src.app.core.config import get_settings
from src.app.db.session import get_sessionmaker
from src.app.models.user import User
from sqlalchemy import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")  # not used directly by frontend, but required


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta_minutes: Optional[int] = None) -> str:
    """Create a signed JWT for the given subject (user id)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[User]:
    """Return current user from token if provided and valid, else None."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, get_settings().JWT_SECRET_KEY, algorithms=[get_settings().JWT_ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            return None
    except JWTError:
        return None

    async with get_sessionmaker()() as session:
        result = await session.execute(select(User).where(User.id == int(sub)))
        user = result.scalar_one_or_none()
        return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from JWT or raise 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_settings().JWT_SECRET_KEY, algorithms=[get_settings().JWT_ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with get_sessionmaker()() as session:
        result = await session.execute(select(User).where(User.id == int(sub)))
        user = result.scalar_one_or_none()
        if not user:
            raise credentials_exception
        return user


# Minimal auth router to support OAuth2PasswordBearer if needed by tooling; not used by app routes
auth_router = APIRouter()


@auth_router.post("/token", response_model=Token, summary="OAuth2 Token (internal)")
async def token(email: EmailStr, password: str):
    """Issue a bearer token for valid credentials (internal helper)."""
    async with get_sessionmaker()() as session:
        result = await session.execute(select(User).where(User.email == str(email)))
        user: Optional[User] = result.scalar_one_or_none()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_access_token(str(user.id))
        return Token(access_token=token)
