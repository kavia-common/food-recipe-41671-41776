from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    preferences: Optional[Dict[str, Any]] = None
    bookmarks: Optional[List[int]] = None

    class Config:
        from_attributes = True


class UserRegisterIn(BaseModel):
    email: EmailStr
    password: str


class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdateIn(BaseModel):
    preferences: Optional[Dict[str, Any]] = None
    bookmarks: Optional[List[int]] = None
