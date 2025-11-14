from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from src.app.core.security import get_current_user
from src.app.db.session import get_sessionmaker
from src.app.models.feedback import Feedback
from src.app.models.recipe import Recipe
from src.app.schemas.feedback import FeedbackIn

router = APIRouter()


# PUBLIC_INTERFACE
@router.post(
    "/feedback",
    status_code=201,
    summary="Submit feedback on a recipe",
    description="Requires authentication. Submit feedback for a recipe.",
)
async def submit_feedback(payload: FeedbackIn, user=Depends(get_current_user)):
    async with get_sessionmaker()() as session:  # type: AsyncSession
        # ensure recipe exists
        recipe_exists = await session.execute(select(Recipe.id).where(Recipe.id == payload.recipeId))
        if recipe_exists.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

        fb = Feedback(
            user_id=user.id,
            recipe_id=payload.recipeId,
            feedback_type=payload.feedbackType,
            comment=payload.comment,
        )
        session.add(fb)
        await session.commit()
        return {"status": "created"}
