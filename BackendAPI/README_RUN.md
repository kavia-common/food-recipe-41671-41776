# BackendAPI Run Guide

## ASGI Entry Point
The ASGI application is exposed at the top-level module:
    main:app

This file lives at:
    BackendAPI/main.py
and imports the real app from:
    BackendAPI/src/api/main.py

## Start with uvicorn
Ensure the working directory is BackendAPI/ (so that the `src` package is importable) or make sure PYTHONPATH includes BackendAPI.

Examples:
- From BackendAPI directory:
    uvicorn main:app --host 0.0.0.0 --port 8000

- From repository root, set PYTHONPATH if needed:
    PYTHONPATH=food-recipe-41671-41776/BackendAPI uvicorn main:app --host 0.0.0.0 --port 8000

## Notes
- The app factory and routers are defined in src/api/main.py and src/app/api/routers/.
- Database URL is read from POSTGRES_URL env var with a sensible default for local development.
