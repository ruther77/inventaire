"""
API Router pour newCMS - Agrégateurs pour le nouveau CMS.

Module dédié au nouveau CMS avec endpoints optimisés pour:
- Cockpit (Morning Brief)
- Opérations (Stock, Factures, Catalogue)
- Finance (Rapprochement, Transactions)
- Restaurant (Plats, Mobile)
- Intelligence (IA, Recommandations)
"""

from fastapi import APIRouter

from .cockpit import router as cockpit_router
from .operations import router as operations_router
from .finance import router as finance_router
from .restaurant import router as restaurant_router, mobile_router
from .intelligence import router as intelligence_router

router = APIRouter(prefix="/newcms", tags=["newcms"])

# Include sub-routers
router.include_router(cockpit_router)
router.include_router(operations_router)
router.include_router(finance_router)
router.include_router(restaurant_router)
router.include_router(mobile_router)
router.include_router(intelligence_router)

__all__ = ["router"]
