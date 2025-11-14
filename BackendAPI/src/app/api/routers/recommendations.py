import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_

from src.app.core.security import get_current_user_optional
from src.app.db.session import async_session
from src.app.models.recipe import Recipe
from src.app.models.user import User
from src.app.schemas.recipe import RecipeOut

router = APIRouter()


def _model_to_schema(r: Recipe) -> RecipeOut:
    return RecipeOut(
        id=r.id,
        title=r.title,
        description=r.description,
        ingredients=json.loads(r.ingredients) if r.ingredients else [],
        steps=json.loads(r.steps) if r.steps else [],
        cuisine=r.cuisine,
        diet=r.diet,
        difficulty=r.difficulty,
        prepTime=r.prep_time,
        cookTime=r.cook_time,
        nutrition=json.loads(r.nutrition) if r.nutrition else None,
        rating=r.rating,
        imageUrl=r.image_url,
    )


# PUBLIC_INTERFACE
@router.get(
    "/recommendations",
    response_model=List[RecipeOut],
    summary="Get personalized recipe recommendations",
    description="Simple content-based recommendations using user's saved preferences. If user not provided, return top-rated.",
)
async def get_recommendations(
    userId: Optional[int] = Query(default=None, description="User ID for personalization"),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    async with async_session() as session:  # type: AsyncSession
        # Determine which user to use (token user takes precedence)
        uid = None
        if current_user:
            uid = current_user.id
        elif userId:
            uid = userId

        query = select(Recipe)
        if uid:
            # fetch user preferences
            from sqlalchemy import select as sel
            from src.app.models.user import User as UserModel
            result = await session.execute(sel(UserModel).where(UserModel.id == uid))
            u = result.scalar_one_or_none()
            prefs = {}
            if u and u.preferences:
                try:
                    prefs = json.loads(u.preferences)
                except Exception:
                    prefs = {}
            cuisine = prefs.get("cuisine")
            diet = prefs.get("diet")
            difficulty = prefs.get("difficulty")
            has_any = False
            if cuisine:
                query = query.where(Recipe.cuisine.ilike(f"%{cuisine}%"))
                has_any = True
            if diet:
                query = query.where(Recipe.diet.ilike(f"%{diet}%"))
                has_any = True
            if difficulty:
                query = query.where(Recipe.difficulty.ilike(f"%{difficulty}%"))
                has_any = True
            if not has_any:
                # fallback to title keywords in preferences if any
                kw = prefs.get("keywords")
                if kw:
                    like = f"%{kw}%"
                    query = query.where(or_(Recipe.title.ilike(like), Recipe.description.ilike(like)))
        else:
            # no user context: return top-rated
            from sqlalchemy import desc
            query = query.order_by(desc(Recipe.rating))

        query = query.limit(20)
        result = await session.execute(query)
        recipes = result.scalars().all()
        return [_model_to_schema(r) for r in recipes]
