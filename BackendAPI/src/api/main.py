import logging
import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.app.core.config import get_settings
from src.app.core.security import auth_router
from src.app.db.session import init_db
from src.app.api.routers.recipes import router as recipes_router
from src.app.api.routers.feedback import router as feedback_router
from src.app.api.routers.recommendations import router as recommendations_router
from src.app.api.routers.users import router as users_router


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application with CORS, routes, and error handlers.
    """
    settings = get_settings()

    # Configure logging level
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("backend")

    app = FastAPI(
        title="Food Recipe Application REST API",
        description="RESTful API for recipe browsing, user management, preferences, recommendations, and feedback.",
        version="1.0.0",
        openapi_tags=[
            {"name": "health", "description": "Health check and service metadata"},
            {"name": "auth", "description": "Authentication and authorization (JWT)"},
            {"name": "recipes", "description": "Browse and search recipes"},
            {"name": "feedback", "description": "Submit feedback for recipes"},
            {"name": "recommendations", "description": "Get personalized recommendations"},
            {"name": "users", "description": "User management and profile"},
        ],
    )

    # CORS configuration
    allow_origins: List[str] = []
    if settings.CORS_ORIGINS:
        allow_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    else:
        # Fallback to frontend URL envs if provided
        for key in ("REACT_APP_FRONTEND_URL", "REACT_APP_API_BASE", "REACT_APP_BACKEND_URL"):
            val = os.getenv(key)
            if val:
                allow_origins.append(val)
        if not allow_origins:
            allow_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def on_startup():
        logger.info("Initializing database...")
        try:
            await init_db()
            logger.info("Database initialized.")
        except Exception as e:
            # Do not block app startup; log and proceed so healthcheck passes.
            logger.warning("Continuing startup without DB (degraded). Error: %s", e)

    # Register routers
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(recipes_router, tags=["recipes"])
    app.include_router(feedback_router, tags=["feedback"])
    app.include_router(recommendations_router, tags=["recommendations"])
    app.include_router(users_router, prefix="/users", tags=["users"])

    # PUBLIC_INTERFACE
    @app.get("/", summary="Health Check", tags=["health"])
    def health_check():
        """Health endpoint to verify service liveness."""
        return {"message": "Healthy"}

    # PUBLIC_INTERFACE
    @app.get("/healthz", summary="Liveness probe", tags=["health"])
    def healthz():
        """
        Liveness endpoint used by deployment probes.
        This endpoint has no external dependencies (e.g., database) and should always return 200 when the app is running.
        """
        return {"status": "ok"}

    # Example docs route for WebSocket usage (none used now) to satisfy doc guidance
    # PUBLIC_INTERFACE
    @app.get("/docs/websocket-usage", summary="WebSocket Usage", tags=["health"])
    def websocket_usage():
        """No WebSocket endpoints in this project currently."""
        return {"websocket": "No WebSocket endpoints available in this API."}

    # Global error handler to match Error schema
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=ErrorDetail(code=str(exc.status_code), message=exc.detail)).model_json_dict(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error=ErrorDetail(code="500", message="Internal Server Error", details={"path": str(request.url)})
            ).model_json_dict(),
        )

    return app


# PUBLIC_INTERFACE
app = create_app()
