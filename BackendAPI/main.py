"""
Entrypoint module for uvicorn/gunicorn to locate the FastAPI ASGI app.

This module exposes "app" by importing it from the project's actual application factory module.
It allows commands like:
    uvicorn main:app --host 0.0.0.0 --port 8000

Notes:
- The actual app is defined in src/api/main.py as `app = create_app()`.
- Ensure PYTHONPATH includes this repository root or BackendAPI/ so that the `src` package is discoverable.
"""

from src.api.main import app as _internal_app  # re-exported below without causing F401/F811


# PUBLIC_INTERFACE
def get_app():
    """
    Return the FastAPI ASGI application instance from the internal module.

    This function is provided as a stable, documented public interface that other
    tools or scripts can import (e.g., from main import get_app).
    """
    return _internal_app


# Expose the ASGI app at module level for uvicorn (main:app)
app = _internal_app
