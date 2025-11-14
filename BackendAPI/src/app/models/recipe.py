from sqlalchemy import Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.session import Base


class Recipe(Base):
    """Recipe model storing core recipe data."""
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    ingredients: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as text
    steps: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as text
    cuisine: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    diet: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    prep_time: Mapped[int] = mapped_column(Integer, nullable=True)
    cook_time: Mapped[int] = mapped_column(Integer, nullable=True)
    nutrition: Mapped[str] = mapped_column(Text, nullable=True)  # JSON object as text
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
