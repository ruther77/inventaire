"""
NewCMS API Router
=================

Expose les nouveaux endpoints CMS:
- Finance Overview & Reconciliation
- Cockpit Morning Brief
- Operations
- Intelligence Overview & Recommendations
"""

from fastapi import APIRouter

from backend.api.newcms.finance import router as finance_router
from backend.api.newcms.cockpit import router as cockpit_router
from backend.api.newcms.operations import router as operations_router
from backend.api.newcms.intelligence import router as intelligence_router

# Router principal NewCMS
router = APIRouter(prefix="/api", tags=["newcms"])

# Inclure les sous-modules
router.include_router(finance_router)
router.include_router(cockpit_router)
router.include_router(operations_router)
router.include_router(intelligence_router)
