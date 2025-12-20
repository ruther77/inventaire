"""Package backend exposant l'application FastAPI pour la SPA."""

import os

if os.getenv("SKIP_BACKEND_APP"):
    app = None
else:
    try:
        # Réexporter l'application FastAPI quand la dépendance est disponible.
        from .main import app  # type: ignore[import]
    except ModuleNotFoundError as exc:  # pragma: no cover - dépendance optionnelle pour les tests
        if exc.name != "fastapi":
            raise
        app = None

__all__ = ["app"]
