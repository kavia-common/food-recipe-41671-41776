import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select

from src.app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from src.app.db.session import get_sessionmaker
from src.app.models.user import User
from src.app.schemas.user import (
    UserLoginIn,
    UserOut,
    UserProfileUpdateIn,
    UserRegisterIn,
)

router = APIRouter()


def _user_to_out(u: User) -> UserOut:
    bookmarks = []
    if u.bookmarks:
        try:
            bookmarks = json.loads(u.bookmarks)
        except Exception:
            bookmarks = []
    prefs = None
    if u.preferences:
        try:
            prefs = json.loads(u.preferences)
        except Exception:
            prefs = None
    return UserOut(id=u.id, email=u.email, preferences=prefs, bookmarks=bookmarks)


# PUBLIC_INTERFACE
@router.post("/register", status_code=201, summary="Register a new user")
async def register(payload: UserRegisterIn):
    async with get_sessionmaker()() as session:  # type: AsyncSession
        exists = await session.execute(select(User).where(User.email == str(payload.email)))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")
        u = User(email=str(payload.email), password_hash=get_password_hash(payload.password))
        session.add(u)
        await session.commit()
        return {"status": "created"}


# PUBLIC_INTERFACE
@router.post("/login", summary="User login")
async def login(payload: UserLoginIn):
    async with get_sessionmaker()() as session:
        result = await session.execute(select(User).where(User.email == str(payload.email)))
        u = result.scalar_one_or_none()
        if not u or not verify_password(payload.password, u.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        token = create_access_token(str(u.id))
        return {"accessToken": token, "tokenType": "bearer"}


# PUBLIC_INTERFACE
@router.get("/{id}/profile", response_model=UserOut, summary="Get user profile")
async def get_profile(id: int = Path(..., description="User ID")):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == id))
        u = result.scalar_one_or_none()
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        return _user_to_out(u)


# PUBLIC_INTERFACE
@router.patch("/{id}/profile", summary="Update user profile")
async def patch_profile(id: int, payload: UserProfileUpdateIn, user=Depends(get_current_user)):
    if user.id != id:
        raise HTTPException(status_code=403, detail="Forbidden")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == id))
        u = result.scalar_one_or_none()
        if not u:
            raise HTTPException(status_code=404, detail="User not found")

        if payload.preferences is not None:
            u.preferences = json.dumps(payload.preferences)
        if payload.bookmarks is not None:
            u.bookmarks = json.dumps(payload.bookmarks)
        await session.commit()
        return {"status": "updated"}


# PUBLIC_INTERFACE
@router.post("/preferences", summary="Update user preferences")
async def update_preferences(payload: Dict[str, Any], user=Depends(get_current_user)):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user.id))
        u = result.scalar_one_or_none()
        if not u:
            raise HTTPException(status_code=404, detail="User not found")
        u.preferences = json.dumps(payload)
        await session.commit()
        return {"status": "updated"}
