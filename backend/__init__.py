"""Backend package exposing the FastAPI application for the SPA."""

import os

if os.getenv("SKIP_BACKEND_APP"):
    app = None
else:
    try:
        # Re-export the FastAPI application when the dependency is available.
        from .main import app  # type: ignore[import]
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency for tests
        if exc.name != "fastapi":
            raise
        app = None

__all__ = ["app"]
