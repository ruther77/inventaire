"""
Tests pour l'API Forecasting.
Coverage des endpoints critiques de prévision.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from backend.api.forecasting import (
    forecast_sales,
    forecast_stock_depletion,
    forecast_cash_flow,
    forecast_price_trend,
    get_forecasting_summary,
    SalesForecastRequest,
)
from core.finance.forecasting import (
    ForecastingEngine,
    ForecastResult,
    ForecastType,
    ForecastMethod,
    CashFlowForecast,
)


@pytest.fixture
def mock_tenant():
    """Mock tenant pour les tests."""
    tenant = MagicMock()
    tenant.id = 1
    return tenant


@pytest.fixture
def mock_forecasting_engine():
    """Mock ForecastingEngine avec des données de test."""
    with patch('backend.api.forecasting.ForecastingEngine') as mock:
        engine = MagicMock()

        # Mock forecast_sales
        sales_forecast = MagicMock()
        sales_forecast.method = ForecastMethod.HOLT_WINTERS
        sales_forecast.predictions = [100.0, 110.0, 120.0]
        sales_forecast.lower_bounds = [90.0, 100.0, 110.0]
        sales_forecast.upper_bounds = [110.0, 120.0, 130.0]
        sales_forecast.confidence = 0.85
        sales_forecast.trend = "increasing"
        sales_forecast.seasonality_detected = True
        sales_forecast.metrics = {"mae": 5.2, "rmse": 7.1}
        engine.forecast_sales.return_value = sales_forecast

        # Mock forecast_cashflow
        cashflow_forecast = MagicMock()
        cashflow_forecast.daily_forecasts = [
            {"date": "2025-12-16", "inflow": 1000, "outflow": 800, "net": 200, "balance": 5200},
            {"date": "2025-12-17", "inflow": 1200, "outflow": 900, "net": 300, "balance": 5500},
        ]
        engine.forecast_cashflow.return_value = cashflow_forecast

        # Mock forecast_price_trend
        price_forecast = MagicMock()
        price_forecast.predictions = [10.5, 10.8, 11.0]
        price_forecast.lower_bounds = [10.0, 10.3, 10.5]
        price_forecast.upper_bounds = [11.0, 11.3, 11.5]
        engine.forecast_price_trend.return_value = price_forecast

        mock.return_value = engine
        yield mock


@pytest.fixture
def mock_sales_history():
    """Mock query_df pour historique de ventes."""
    with patch('backend.api.forecasting._get_sales_history') as mock:
        mock.return_value = [
            {"date": date.today() - timedelta(days=i), "amount": Decimal(str(100 + i * 5))}
            for i in range(30)
        ]
        yield mock


@pytest.fixture
def mock_query_df():
    """Mock query_df pour les requêtes SQL."""
    with patch('backend.api.forecasting.query_df') as mock:
        yield mock


class TestForecastSalesEndpoint:
    """Tests pour l'endpoint POST /forecasting/sales"""

    def test_forecast_sales_success(self, mock_tenant, mock_forecasting_engine, mock_sales_history):
        """Test prévision de ventes avec succès."""
        request = SalesForecastRequest(horizon_days=3, method="HOLT_WINTERS")

        result = forecast_sales(request, mock_tenant)

        assert result.method == "holt_winters"
        assert result.horizon_days == 3
        assert len(result.predictions) == 3
        assert result.predictions[0].value == 100.0
        assert result.predictions[0].lower_bound == 90.0
        assert result.predictions[0].upper_bound == 110.0
        assert result.confidence == 0.85
        assert result.trend == "increasing"
        assert result.seasonality_detected is True

    def test_forecast_sales_not_enough_data(self, mock_tenant):
        """Test échec si pas assez de données historiques."""
        with patch('backend.api.forecasting._get_sales_history') as mock:
            mock.return_value = [{"date": date.today(), "amount": Decimal("100")}]  # Seulement 1 jour

            request = SalesForecastRequest(horizon_days=30)

            with pytest.raises(HTTPException) as exc_info:
                forecast_sales(request, mock_tenant)

            assert exc_info.value.status_code == 400
            assert "Pas assez de données" in exc_info.value.detail

    def test_forecast_sales_auto_method_selection(self, mock_tenant, mock_forecasting_engine, mock_sales_history):
        """Test sélection automatique de la méthode."""
        request = SalesForecastRequest(horizon_days=7, method=None)

        result = forecast_sales(request, mock_tenant)

        assert result is not None
        # Vérifie que l'engine a été appelé avec method=None
        mock_forecasting_engine.return_value.forecast_sales.assert_called_once()


class TestStockDepletionEndpoint:
    """Tests pour l'endpoint GET /forecasting/stock-depletion"""

    def test_stock_depletion_forecast(self, mock_tenant, mock_query_df):
        """Test prévision d'épuisement du stock."""
        import pandas as pd

        # Mock les données de stock
        mock_query_df.return_value = pd.DataFrame([
            {"product_id": 1, "product_name": "Tomates", "current_stock": 100, "avg_daily": 10},
            {"product_id": 2, "product_name": "Pommes", "current_stock": 50, "avg_daily": 5},
        ])

        result = forecast_stock_depletion(days_horizon=60, tenant=mock_tenant)

        assert len(result) == 2
        assert result[0].product_id == 1
        assert result[0].days_until_depletion == 10.0  # 100/10
        assert result[0].recommended_reorder_date is not None
        # Vérifie que les produits sont triés par jours restants
        assert result[0].days_until_depletion <= result[1].days_until_depletion

    def test_stock_depletion_no_consumption(self, mock_tenant, mock_query_df):
        """Test avec produits sans consommation."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {"product_id": 1, "product_name": "Produit", "current_stock": 100, "avg_daily": 0},
        ])

        result = forecast_stock_depletion(tenant=mock_tenant)

        assert len(result) == 1
        assert result[0].days_until_depletion is None
        assert result[0].predicted_depletion_date is None


class TestCashFlowEndpoint:
    """Tests pour l'endpoint GET /forecasting/cash-flow"""

    def test_cash_flow_forecast_success(self, mock_tenant, mock_forecasting_engine):
        """Test prévision de trésorerie avec succès."""
        result = forecast_cash_flow(
            horizon_days=2,
            starting_balance=5000.0,
            tenant=mock_tenant
        )

        assert result.period_start == date.today() + timedelta(days=1)
        assert result.period_end == date.today() + timedelta(days=2)
        assert len(result.predictions) == 2
        assert result.total_inflows == 2200.0  # 1000 + 1200
        assert result.total_outflows == 1700.0  # 800 + 900
        assert result.net_cash_flow == 500.0
        assert result.ending_balance == 5500.0

    def test_cash_flow_forecast_negative_balance_alert(self, mock_tenant):
        """Test alertes de solde négatif."""
        with patch('backend.api.forecasting.ForecastingEngine') as mock:
            engine = MagicMock()
            cashflow = MagicMock()
            cashflow.daily_forecasts = [
                {"date": "2025-12-16", "inflow": 100, "outflow": 500, "net": -400, "balance": -400},
            ]
            engine.forecast_cashflow.return_value = cashflow
            mock.return_value = engine

            result = forecast_cash_flow(horizon_days=1, tenant=mock_tenant)

            assert len(result.alerts) > 0
            assert "Solde négatif" in result.alerts[0]

    def test_cash_flow_forecast_error_handling(self, mock_tenant):
        """Test gestion d'erreur lors de la prévision."""
        with patch('backend.api.forecasting.ForecastingEngine') as mock:
            mock.return_value.forecast_cashflow.side_effect = Exception("DB error")

            result = forecast_cash_flow(horizon_days=30, starting_balance=1000, tenant=mock_tenant)

            # Doit retourner une prévision vide sans crash
            assert result.predictions == []
            assert "Pas assez de données" in result.alerts[0]


class TestPriceTrendEndpoint:
    """Tests pour l'endpoint GET /forecasting/price-trend/{product_id}"""

    def test_price_trend_forecast_success(self, mock_tenant, mock_query_df, mock_forecasting_engine):
        """Test prévision de tendance de prix."""
        import pandas as pd

        # Mock produit
        mock_query_df.return_value = pd.DataFrame([
            {"id": 1, "nom": "Tomates", "prix_achat": 2.5}
        ])

        with patch('backend.api.forecasting._get_price_history') as mock_history:
            mock_history.return_value = [
                {"date": date.today() - timedelta(days=i), "price": Decimal(str(2.0 + i * 0.1))}
                for i in range(10)
            ]

            result = forecast_price_trend(
                product_id=1,
                horizon_days=3,
                tenant=mock_tenant
            )

            assert result.product_id == 1
            assert result.product_name == "Tomates"
            assert len(result.predicted_prices) == 3
            assert result.trend_direction in ["increasing", "decreasing", "stable"]
            assert 0 <= result.trend_strength <= 1.0

    def test_price_trend_product_not_found(self, mock_tenant, mock_query_df):
        """Test produit non trouvé."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame()  # Vide

        with pytest.raises(HTTPException) as exc_info:
            forecast_price_trend(product_id=999, tenant=mock_tenant)

        assert exc_info.value.status_code == 404

    def test_price_trend_insufficient_history(self, mock_tenant, mock_query_df):
        """Test avec historique insuffisant de prix."""
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {"id": 1, "nom": "Produit", "prix_achat": 10.0}
        ])

        with patch('backend.api.forecasting._get_price_history') as mock_history:
            mock_history.return_value = [{"date": date.today(), "price": Decimal("10")}]  # Seulement 1 jour

            result = forecast_price_trend(product_id=1, horizon_days=7, tenant=mock_tenant)

            # Doit retourner une prévision stable
            assert result.trend_direction == "stable"
            assert result.trend_strength == 0.0


class TestForecastingSummaryEndpoint:
    """Tests pour l'endpoint GET /forecasting/summary"""

    def test_forecasting_summary(self, mock_tenant, mock_query_df):
        """Test résumé des prévisions."""
        import pandas as pd

        # Mock ventes
        mock_query_df.side_effect = [
            # Sales query
            pd.DataFrame([{"recent": 1000, "previous": 900}]),
            # Depletion query
            pd.DataFrame([{"count": 5}]),
            # Cash query
            pd.DataFrame([{"inflows": 5000, "outflows": 4000}]),
        ]

        result = get_forecasting_summary(tenant=mock_tenant)

        assert "sales" in result
        assert result["sales"]["recent_7_days"] == 1000
        assert result["sales"]["previous_7_days"] == 900
        assert result["sales"]["trend_pct"] > 0

        assert "stock" in result
        assert result["stock"]["products_depleting_7_days"] == 5

        assert "cash_flow" in result
        assert result["cash_flow"]["recent_inflows"] == 5000
        assert result["cash_flow"]["net_flow_7_days"] == 1000


class TestTenantMapping:
    """Tests pour la conversion tenant_id -> effective_tenant"""

    def test_intelligence_tenant_mapping_sales(self, mock_query_df):
        """Test que tenant intelligence (4) accède au tenant restaurant (2) pour sales."""
        from backend.api.forecasting import _get_sales_history
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame([
            {"date": date.today(), "amount": 100}
        ])

        _get_sales_history(tenant_id=4, days=30)

        # Vérifie que la requête utilise tenant_id=2 (restaurant)
        call_params = mock_query_df.call_args[1]['params']
        assert call_params['tenant_id'] == 2

    def test_normal_tenant_no_mapping(self, mock_query_df):
        """Test que les autres tenants ne sont pas mappés."""
        from backend.api.forecasting import _get_sales_history
        import pandas as pd

        mock_query_df.return_value = pd.DataFrame()

        _get_sales_history(tenant_id=1, days=30)

        call_params = mock_query_df.call_args[1]['params']
        assert call_params['tenant_id'] == 1


class TestMethodEnumConversion:
    """Tests pour la conversion string -> ForecastMethod enum"""

    def test_valid_method_strings(self):
        """Test conversion des méthodes valides."""
        from backend.api.forecasting import _get_method_enum

        assert _get_method_enum("HOLT_WINTERS") == ForecastMethod.HOLT_WINTERS
        assert _get_method_enum("LINEAR_REGRESSION") == ForecastMethod.LINEAR_REGRESSION
        assert _get_method_enum("holt_winters") == ForecastMethod.HOLT_WINTERS  # Case insensitive

    def test_invalid_method_string(self):
        """Test méthode invalide retourne None."""
        from backend.api.forecasting import _get_method_enum

        assert _get_method_enum("INVALID_METHOD") is None
        assert _get_method_enum(None) is None
