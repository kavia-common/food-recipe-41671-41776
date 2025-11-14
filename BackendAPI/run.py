"""
Helper script to run the FastAPI app using uvicorn.

Usage:
    python run.py
or
    python -m BackendAPI.run

Environment:
    Ensure PYTHONPATH includes this BackendAPI directory or project root so that `src` is importable.
"""

import os
import sys

if __name__ == "__main__":
    # Ensure current directory is on sys.path to resolve 'src' package
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    import uvicorn

    # Use the top-level ASGI entrypoint "main:app"
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
