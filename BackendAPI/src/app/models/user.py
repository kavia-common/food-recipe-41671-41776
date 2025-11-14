from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.session import Base


class User(Base):
    """User model for authentication and profile."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    preferences: Mapped[str] = mapped_column(Text, nullable=True)  # JSON object as text
    bookmarks: Mapped[str] = mapped_column(Text, nullable=True)  # JSON array of recipe IDs as text
