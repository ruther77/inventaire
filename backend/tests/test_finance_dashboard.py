"""Smoke test dashboard summary service."""

from backend.services.finance import dashboard as finance_dashboard


def test_dashboard_summary_smoke(monkeypatch):
    class DummyDF:
        def __init__(self):
            self.empty = False

        def __getitem__(self, key):
            return None

        def __getattr__(self, item):
            raise AttributeError

        def iloc(self, idx):
            return self

    # Skip DB calls by monkeypatching query_df to return empty
    monkeypatch.setattr(finance_dashboard, "query_df", lambda *args, **kwargs: DummyDF())
    summary = finance_dashboard.dashboard_summary()
    assert isinstance(summary, dict)
    assert "net" in summary
