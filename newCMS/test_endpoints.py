"""
Quick test script for newCMS restaurant and mobile endpoints.

Run with: python -m pytest newCMS/test_endpoints.py -v
Or standalone: python newCMS/test_endpoints.py
"""

import sys
from typing import Dict, Any

# Mock dependencies for testing
class MockTenant:
    """Mock tenant for testing."""
    def __init__(self, tenant_id: int = 1):
        self.id = tenant_id


def test_restaurant_overview_response_schema():
    """Test that restaurant overview response matches schema."""
    from newCMS.backend.schemas.restaurant import (
        RestaurantOverviewResponse,
        RestaurantOverviewMetrics,
        RestaurantPlatCost,
        RestaurantStockLocation,
        RestaurantIngredientAlert,
        RestaurantTopPlat,
    )

    # Create sample response
    response = RestaurantOverviewResponse(
        metrics=RestaurantOverviewMetrics(
            total_plats=10,
            avg_food_cost_pct=32.5,
            alerts_count=3,
            top_plats=[
                RestaurantTopPlat(
                    plat_id=1,
                    nom="Burger",
                    marge_pct=68.5,
                    prix_vente_ttc=12.50,
                    cout_matiere=3.94,
                )
            ],
        ),
        plat_costs=[
            RestaurantPlatCost(
                plat_id=1,
                nom="Burger",
                food_cost_pct=31.5,
                marge_pct=68.5,
                prix_vente_ttc=12.50,
                cout_matiere=3.94,
            )
        ],
        stock_locations=[
            RestaurantStockLocation(location="cuisine", count=10, valeur=500.0)
        ],
        ingredient_alerts=[
            RestaurantIngredientAlert(
                ingredient_id=1,
                nom="Tomate",
                stock_actuel=2.0,
                seuil_alerte=5.0,
                status="alerte",
            )
        ],
    )

    assert response.metrics.total_plats == 10
    assert response.metrics.avg_food_cost_pct == 32.5
    assert len(response.plat_costs) == 1
    assert response.plat_costs[0].nom == "Burger"
    print("✓ Restaurant overview schema valid")


def test_mobile_inventory_response_schema():
    """Test that mobile inventory response matches schema."""
    from newCMS.backend.schemas.restaurant import (
        MobileInventoryListResponse,
        MobileInventoryItem,
    )

    response = MobileInventoryListResponse(
        items=[
            MobileInventoryItem(
                id=1,
                nom="Tomate",
                code_barre="3245678901234",
                stock_actuel=15.5,
                seuil_alerte=10.0,
                categorie="ingredient",
            )
        ],
        total=1,
        page=1,
        page_size=50,
    )

    assert len(response.items) == 1
    assert response.items[0].nom == "Tomate"
    assert response.items[0].code_barre == "3245678901234"
    assert response.total == 1
    print("✓ Mobile inventory schema valid")


def test_mobile_scan_response_schema():
    """Test that mobile scan response matches schema."""
    from newCMS.backend.schemas.restaurant import (
        MobileScanResponse,
        MobileInventoryItem,
    )

    # Test found case
    response_found = MobileScanResponse(
        found=True,
        product=MobileInventoryItem(
            id=1,
            nom="Tomate",
            code_barre="3245678901234",
            stock_actuel=15.5,
            seuil_alerte=10.0,
            categorie="ingredient",
        ),
        message=None,
    )

    assert response_found.found is True
    assert response_found.product is not None
    assert response_found.product.nom == "Tomate"

    # Test not found case
    response_not_found = MobileScanResponse(
        found=False,
        product=None,
        message="Product not found",
    )

    assert response_not_found.found is False
    assert response_not_found.product is None
    assert response_not_found.message == "Product not found"
    print("✓ Mobile scan schema valid")


def test_mobile_adjust_request_validation():
    """Test mobile adjust request validation."""
    from newCMS.backend.schemas.restaurant import MobileAdjustRequest
    from pydantic import ValidationError

    # Valid request
    valid_request = MobileAdjustRequest(
        product_id=1,
        adjustment=-1.0,
        adjustment_type="delta",
        reason="breakage",
        notes="Test",
    )

    assert valid_request.product_id == 1
    assert valid_request.adjustment == -1.0
    assert valid_request.reason == "breakage"

    # Invalid product_id (must be > 0)
    try:
        invalid_request = MobileAdjustRequest(
            product_id=0,
            adjustment=-1.0,
            adjustment_type="delta",
            reason="breakage",
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    print("✓ Mobile adjust validation works")


def test_adjustment_types():
    """Test different adjustment types."""
    from newCMS.backend.schemas.restaurant import MobileAdjustRequest

    # Delta adjustment
    delta_request = MobileAdjustRequest(
        product_id=1,
        adjustment=-1.0,
        adjustment_type="delta",
        reason="theft",
    )
    assert delta_request.adjustment_type == "delta"

    # Absolute adjustment
    absolute_request = MobileAdjustRequest(
        product_id=1,
        adjustment=10.0,
        adjustment_type="absolute",
        reason="error",
    )
    assert absolute_request.adjustment_type == "absolute"

    print("✓ Adjustment types valid")


def test_adjustment_reasons():
    """Test all valid adjustment reasons."""
    from newCMS.backend.schemas.restaurant import MobileAdjustRequest

    valid_reasons = ["breakage", "theft", "error", "expiry", "other"]

    for reason in valid_reasons:
        request = MobileAdjustRequest(
            product_id=1,
            adjustment=-1.0,
            adjustment_type="delta",
            reason=reason,
        )
        assert request.reason == reason

    print("✓ All adjustment reasons valid")


def test_response_serialization():
    """Test that responses can be serialized to JSON."""
    import json
    from datetime import datetime
    from newCMS.backend.schemas.restaurant import MobileAdjustResponse

    response = MobileAdjustResponse(
        product_id=1,
        product_name="Tomate",
        old_stock=15.5,
        new_stock=14.5,
        adjustment=-1.0,
        reason="breakage",
        timestamp=datetime.utcnow(),
    )

    # Test JSON serialization
    json_str = response.model_dump_json()
    assert json_str is not None
    assert "product_id" in json_str
    assert "Tomate" in json_str

    # Test dict conversion
    response_dict = response.model_dump()
    assert response_dict["product_id"] == 1
    assert response_dict["product_name"] == "Tomate"
    assert response_dict["adjustment"] == -1.0

    print("✓ Response serialization works")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_restaurant_overview_response_schema,
        test_mobile_inventory_response_schema,
        test_mobile_scan_response_schema,
        test_mobile_adjust_request_validation,
        test_adjustment_types,
        test_adjustment_reasons,
        test_response_serialization,
    ]

    print("\n" + "=" * 60)
    print("Running newCMS endpoint tests")
    print("=" * 60 + "\n")

    failed = 0
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {e}")
            failed += 1

    print("\n" + "=" * 60)
    if failed == 0:
        print(f"✓ All {len(tests)} tests passed!")
    else:
        print(f"✗ {failed}/{len(tests)} tests failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
