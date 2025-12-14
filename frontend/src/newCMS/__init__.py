"""
NewCMS - Restaurant & Mobile API Module

Modern API endpoints for restaurant management and mobile inventory control.
Optimized for speed and mobile-first design.

Usage:
    from newCMS.backend.api import restaurant_router
    app.include_router(restaurant_router)

Endpoints:
    - GET  /newcms/restaurant/overview  - Restaurant dashboard
    - GET  /newcms/mobile/inventory     - Mobile inventory list
    - POST /newcms/mobile/scan          - Barcode scan
    - POST /newcms/mobile/adjust        - Stock adjustment

Documentation:
    - README.md                    - Quick start guide
    - RESTAURANT_MOBILE_API.md     - Complete API documentation
    - INTEGRATION_EXAMPLE.py       - Integration examples
    - test_endpoints.py            - Unit tests

Version: 1.0.0
Author: Restaurant Backend Expert
Date: 2025-12-11
"""

__version__ = "1.0.0"
__author__ = "Restaurant Backend Expert"

from newCMS.backend.api import restaurant_router

__all__ = ["restaurant_router"]
