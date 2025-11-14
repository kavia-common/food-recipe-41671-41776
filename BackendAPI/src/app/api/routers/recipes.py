import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, or_

from src.app.db.session import get_sessionmaker
from src.app.models.recipe import Recipe
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
    "/recipes",
    response_model=List[RecipeOut],
    summary="Search and filter recipes",
    description="Search/filter by query, cuisine, diet, difficulty. Supports pagination via page and size.",
)
async def list_recipes(
    search: Optional[str] = Query(default=None),
    cuisine: Optional[str] = Query(default=None),
    diet: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    sort: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    offset = (page - 1) * size
    async with get_sessionmaker()() as session:  # type: AsyncSession
        query = select(Recipe)
        # filters
        if cuisine:
            query = query.where(Recipe.cuisine.ilike(f"%{cuisine}%"))
        if diet:
            query = query.where(Recipe.diet.ilike(f"%{diet}%"))
        if difficulty:
            query = query.where(Recipe.difficulty.ilike(f"%{difficulty}%"))
        if search:
            like = f"%{search}%"
            query = query.where(or_(Recipe.title.ilike(like), Recipe.description.ilike(like)))

        # simple sort support
        if sort == "rating_desc":
            from sqlalchemy import desc
            query = query.order_by(desc(Recipe.rating))
        elif sort == "rating_asc":
            from sqlalchemy import asc
            query = query.order_by(asc(Recipe.rating))

        query = query.offset(offset).limit(size)
        result = await session.execute(query)
        recipes = result.scalars().all()
        return [_model_to_schema(r) for r in recipes]


# PUBLIC_INTERFACE
@router.get(
    "/recipes/{id}",
    response_model=RecipeOut,
    summary="Get recipe details",
    description="Return a single recipe by ID.",
)
async def get_recipe(id: int):
    async with get_sessionmaker()() as session:
        result = await session.execute(select(Recipe).where(Recipe.id == id))
        r: Optional[Recipe] = result.scalar_one_or_none()
        if not r:
            raise HTTPException(status_code=404, detail="Recipe not found")
        return _model_to_schema(r)
