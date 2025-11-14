from typing import Optional
from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    recipeId: int = Field(..., description="Recipe ID")
    feedbackType: str = Field(..., description="Type of feedback (like/dislike/rating)")
    comment: Optional[str] = Field(None, description="Optional comment")
