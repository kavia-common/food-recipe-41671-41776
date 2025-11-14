"""
ASGI entrypoint for uvicorn/gunicorn to locate the FastAPI application.

This module attempts to import and expose "app" from the internal module at:
    src/api/main.py

It ensures the ./src directory is on sys.path so that imports work whether uvicorn
is started from the BackendAPI folder or from the repo root.

Typical usage:
    uvicorn main:app --host 0.0.0.0 --port 3001
"""

import os
import sys
from typing import Optional

# Ensure the BackendAPI/src folder is importable regardless of CWD.
# This avoids the need to set PYTHONPATH externally.
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_current_dir, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

_internal_app: Optional[object] = None

try:
    # Import the real FastAPI app from internal module
    from src.api.main import app as _real_app  # type: ignore
    _internal_app = _real_app
except Exception as import_err:
    # If the import failed, attempt one more time after adding the BackendAPI
    # directory itself to sys.path. This handles cases where relative pathing differs.
    backend_root = _current_dir
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)
    try:
        from src.api.main import app as _real_app  # type: ignore
        _internal_app = _real_app
    except Exception as second_err:
        # Fallback: provide a minimal FastAPI app so uvicorn can still boot,
        # exposing a health endpoint that surfaces the import error.
        try:
            from fastapi import FastAPI
        except Exception:
            # If FastAPI itself is missing, re-raise the original error to fail fast.
            raise second_err

        fallback = FastAPI(
            title="BackendAPI (Fallback)",
            description="Fallback app exposed because internal app import failed.",
            version="0.0.0",
            openapi_tags=[{"name": "health", "description": "Health check and import status"}],
        )

        _import_error_text = f"first={import_err!r}; second={second_err!r}"

        # PUBLIC_INTERFACE
        @fallback.get("/", summary="Health Check", tags=["health"])
        def health():
            """Health endpoint indicating fallback mode and the reason."""
            return {
                "message": "BackendAPI fallback app running",
                "detail": "Failed to import src.api.main:app",
                "error": _import_error_text,
            }

        _internal_app = fallback


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
