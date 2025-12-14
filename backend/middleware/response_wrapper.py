"""
Response Wrapper Middleware - Format de réponse unifié avancé.

Transforme automatiquement toutes les réponses en format standardisé:
{
    "success": true/false,
    "data": {...},
    "error": null | { "code": "...", "message": "...", "details": {...} },
    "meta": { "request_id": "...", "duration_ms": ..., "pagination": {...} }
}
"""

from __future__ import annotations

import json
import time
import logging
from typing import Any, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from .request_context import get_request_id, get_elapsed_ms

logger = logging.getLogger(__name__)


# Codes d'erreur standardisés
class ErrorCodes:
    """Codes d'erreur avec messages et suggestions."""

    VALIDATION_ERROR = ("VALIDATION_ERROR", "Données invalides", "Vérifiez les champs du formulaire")
    NOT_FOUND = ("NOT_FOUND", "Ressource introuvable", "L'élément demandé n'existe pas ou a été supprimé")
    UNAUTHORIZED = ("UNAUTHORIZED", "Authentification requise", "Connectez-vous pour accéder à cette ressource")
    FORBIDDEN = ("FORBIDDEN", "Accès refusé", "Vous n'avez pas les droits nécessaires")
    CONFLICT = ("CONFLICT", "Conflit de données", "Un élément avec ces données existe déjà")
    RATE_LIMITED = ("RATE_LIMITED", "Trop de requêtes", "Attendez quelques instants avant de réessayer")
    SERVER_ERROR = ("SERVER_ERROR", "Erreur serveur", "Réessayez dans quelques instants")
    SERVICE_UNAVAILABLE = ("SERVICE_UNAVAILABLE", "Service indisponible", "Le service est temporairement indisponible")

    @classmethod
    def from_status(cls, status_code: int) -> tuple[str, str, str]:
        """Mappe un code HTTP vers un code d'erreur."""
        mapping = {
            400: cls.VALIDATION_ERROR,
            401: cls.UNAUTHORIZED,
            403: cls.FORBIDDEN,
            404: cls.NOT_FOUND,
            409: cls.CONFLICT,
            422: cls.VALIDATION_ERROR,
            429: cls.RATE_LIMITED,
            500: cls.SERVER_ERROR,
            502: cls.SERVICE_UNAVAILABLE,
            503: cls.SERVICE_UNAVAILABLE,
        }
        return mapping.get(status_code, cls.SERVER_ERROR)


def build_success_response(
    data: Any,
    *,
    meta: Optional[dict] = None,
    status_code: int = 200,
) -> dict[str, Any]:
    """Construit une réponse de succès standardisée."""
    response = {
        "success": True,
        "data": data,
        "error": None,
        "meta": {
            "request_id": get_request_id(),
            "duration_ms": round(get_elapsed_ms(), 2),
            **(meta or {}),
        },
    }
    return response


def build_error_response(
    code: str,
    message: str,
    *,
    suggestion: Optional[str] = None,
    details: Optional[dict] = None,
    field_errors: Optional[dict[str, list[str]]] = None,
) -> dict[str, Any]:
    """Construit une réponse d'erreur standardisée."""
    error_obj = {
        "code": code,
        "message": message,
    }

    if suggestion:
        error_obj["suggestion"] = suggestion

    if details:
        error_obj["details"] = details

    if field_errors:
        error_obj["field_errors"] = field_errors

    return {
        "success": False,
        "data": None,
        "error": error_obj,
        "meta": {
            "request_id": get_request_id(),
            "duration_ms": round(get_elapsed_ms(), 2),
        },
    }


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """
    Middleware de standardisation des réponses.

    - Wrappe toutes les réponses JSON dans le format unifié
    - Enrichit les erreurs avec codes et suggestions
    - Ajoute les métadonnées (request_id, timing)
    - Gère la pagination automatiquement
    """

    def __init__(
        self,
        app,
        *,
        exclude_paths: Optional[list[str]] = None,
        wrap_errors_only: bool = False,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.wrap_errors_only = wrap_errors_only

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclure certains paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        response = await call_next(request)

        # Ne traiter que les réponses JSON
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Lire le body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            original_data = json.loads(body)
        except json.JSONDecodeError:
            return response

        # Déterminer si c'est déjà wrappé
        if self._is_already_wrapped(original_data):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        # Wrapper la réponse
        if response.status_code >= 400:
            wrapped = self._wrap_error(original_data, response.status_code)
        elif not self.wrap_errors_only:
            wrapped = self._wrap_success(original_data, response.status_code)
        else:
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        return JSONResponse(
            content=wrapped,
            status_code=response.status_code,
            headers={k: v for k, v in response.headers.items() if k.lower() != "content-length"},
        )

    def _is_already_wrapped(self, data: Any) -> bool:
        """Vérifie si la réponse est déjà au format standardisé."""
        if not isinstance(data, dict):
            return False
        return "success" in data and ("data" in data or "error" in data)

    def _wrap_success(self, data: Any, status_code: int) -> dict[str, Any]:
        """Wrappe une réponse de succès."""
        meta = {
            "request_id": get_request_id(),
            "duration_ms": round(get_elapsed_ms(), 2),
        }

        # Détecter la pagination
        if isinstance(data, dict):
            if "items" in data:
                meta["total_count"] = data.get("total", len(data["items"]))
                if "page" in data:
                    meta["pagination"] = {
                        "page": data.get("page", 1),
                        "per_page": data.get("per_page", data.get("size", 50)),
                        "total_pages": data.get("total_pages", data.get("pages", 1)),
                    }

        return {
            "success": True,
            "data": data,
            "error": None,
            "meta": meta,
        }

    def _wrap_error(self, data: Any, status_code: int) -> dict[str, Any]:
        """Wrappe une réponse d'erreur."""
        code, default_message, suggestion = ErrorCodes.from_status(status_code)

        # Extraire le message d'erreur
        message = default_message
        details = None
        field_errors = None

        if isinstance(data, dict):
            if "detail" in data:
                detail = data["detail"]
                if isinstance(detail, str):
                    message = detail
                elif isinstance(detail, list):
                    # Erreurs de validation Pydantic
                    field_errors = {}
                    for err in detail:
                        loc = err.get("loc", [])
                        field = ".".join(str(l) for l in loc[1:]) if len(loc) > 1 else "general"
                        msg = err.get("msg", "Erreur de validation")
                        if field not in field_errors:
                            field_errors[field] = []
                        field_errors[field].append(msg)
                    message = "Erreurs de validation sur les champs"
                elif isinstance(detail, dict):
                    message = detail.get("message", default_message)
                    details = detail
            elif "message" in data:
                message = data["message"]

        error_obj = {
            "code": code,
            "message": message,
            "suggestion": suggestion,
        }

        if details:
            error_obj["details"] = details

        if field_errors:
            error_obj["field_errors"] = field_errors

        return {
            "success": False,
            "data": None,
            "error": error_obj,
            "meta": {
                "request_id": get_request_id(),
                "duration_ms": round(get_elapsed_ms(), 2),
            },
        }
