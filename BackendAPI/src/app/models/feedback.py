from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.app.db.session import Base


class Feedback(Base):
    """Feedback model connecting users to recipe feedback."""
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    recipe_id: Mapped[int] = mapped_column(Integer, ForeignKey("recipes.id"), nullable=False, index=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)  # like/dislike/rating/etc
    comment: Mapped[str] = mapped_column(Text, nullable=True)
