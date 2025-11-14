import asyncio
import json
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.app.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""
    pass


# Lazily initialized globals
_engine: Optional[AsyncEngine] = None
_async_session: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """
    Return a singleton AsyncEngine, creating it on first use.

    Avoids connecting to the database at import time so the application can start
    and serve basic routes (e.g., health) even if the DB is unavailable.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """
    Return a singleton async_sessionmaker bound to the engine.

    Created lazily to prevent import-time DB initialization.
    """
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _async_session


# PUBLIC_INTERFACE
async def init_db(timeout_seconds: int = 5) -> None:
    """
    Initialize database schema and seed minimal data in a safe, non-blocking way.

    This function will:
    - Import models so metadata is populated
    - Create tables if they do not exist
    - Seed a few default recipes if the table is empty

    If the database is unreachable or the initialization exceeds the timeout,
    the exception is propagated to the caller so it can be handled (logged) and
    the app can continue to start for liveness checks.
    """
    # Import models so metadata has all tables
    from src.app.models import recipe as recipe_model  # noqa: F401
    from src.app.models import user as user_model  # noqa: F401
    from src.app.models import feedback as feedback_model  # noqa: F401

    engine = get_engine()
    sessionmaker = get_sessionmaker()

    async def _perform_init():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Seed minimal recipes if empty
        async with sessionmaker() as session:
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

    try:
        await asyncio.wait_for(_perform_init(), timeout=timeout_seconds)
    except Exception as e:
        # Log; let caller decide whether to crash or continue.
        logger.warning("Database initialization failed or timed out: %s", e)
        raise


# Backwards-compatible names for importers
async_session = get_sessionmaker
