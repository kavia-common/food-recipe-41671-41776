import json
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.app.core.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


settings = get_settings()
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    """Initialize database schema and seed minimal data."""
    # Import models so metadata has all tables
    from src.app.models import recipe as recipe_model  # noqa: F401
    from src.app.models import user as user_model  # noqa: F401
    from src.app.models import feedback as feedback_model  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed minimal recipes if empty
    async with async_session() as session:
        from sqlalchemy import select, func
        from src.app.models.recipe import Recipe as RecipeModel

        count = (await session.execute(select(func.count(RecipeModel.id)))).scalar_one()
        if count == 0:
            seed_recipes: List[RecipeModel] = [
                RecipeModel(
                    title="Spaghetti Aglio e Olio",
                    description="Classic Italian pasta with garlic and olive oil.",
                    ingredients=json.dumps(["spaghetti", "garlic", "olive oil", "chili flakes", "parsley", "salt"]),
                    steps=json.dumps(["Boil pasta", "Saute garlic", "Toss with oil and chili", "Garnish"]),
                    cuisine="Italian",
                    diet="vegetarian",
                    difficulty="easy",
                    prep_time=10,
                    cook_time=15,
                    nutrition=json.dumps({"calories": 420}),
                    rating=4.5,
                    image_url="https://example.com/images/aglio-olio.jpg",
                ),
                RecipeModel(
                    title="Chicken Tikka Masala",
                    description="Grilled chicken in creamy tomato sauce.",
                    ingredients=json.dumps(["chicken", "yogurt", "tomato", "cream", "garam masala", "garlic", "ginger"]),
                    steps=json.dumps(["Marinate", "Grill", "Simmer sauce", "Combine"]),
                    cuisine="Indian",
                    diet="non-vegetarian",
                    difficulty="medium",
                    prep_time=30,
                    cook_time=40,
                    nutrition=json.dumps({"calories": 550}),
                    rating=4.7,
                    image_url="https://example.com/images/tikka-masala.jpg",
                ),
            ]
            session.add_all(seed_recipes)
            await session.commit()
