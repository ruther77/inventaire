import pandas as pd

from backend.services import stock


def test_fetch_movement_timeseries(monkeypatch):
    sample = pd.DataFrame(
        [
            {'jour': '2024-01-01', 'type': 'ENTREE', 'quantite': 5},
            {'jour': '2024-01-01', 'type': 'SORTIE', 'quantite': 2},
        ]
    )
    monkeypatch.setattr(stock, "query_df", lambda *args, **kwargs: sample)

    df = stock.fetch_movement_timeseries(window_days=7, product_id=1)
    assert len(df) == 2
    assert df.iloc[0]['jour'].year == 2024


def test_adjust_stock_level(monkeypatch):
    class DummyConn:
        def __init__(self):
            self.data = {'stock': 5}

        def execute(self, query, params=None):
            text = str(query)
            if "FOR UPDATE" in text:
                return DummyResult(DummyRow({'nom': 'Produit A', 'stock_actuel': self.data['stock']}))
            if "INSERT INTO mouvements_stock" in text:
                self.data['stock'] += params['quantite'] if params['type'] == 'ENTREE' else -params['quantite']
                return DummyResult(None)
            if "SELECT COALESCE" in text:
                return DummyResult(DummyRow([self.data['stock']]))
            return DummyResult(None)

    class DummyResult:
        def __init__(self, row):
            self._row = row

        def fetchone(self):
            return self._row

    class DummyRow:
        def __init__(self, data):
            self.data = data

        def __getattr__(self, item):
            if isinstance(self.data, dict):
                return self.data[item]
            raise AttributeError(item)

        def __getitem__(self, key):
            if isinstance(key, int):
                if isinstance(self.data, dict):
                    return list(self.data.values())[key]
                if isinstance(self.data, (list, tuple)):
                    return self.data[key]
            return self.data[key]

    class DummyEngine:
        def begin(self):
            return DummyContext(self)

        def connect(self):
            return DummyContext(self)

    class DummyContext:
        def __init__(self, engine):
            self.conn = DummyConn()

        def __enter__(self):
            return self.conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

    monkeypatch.setattr(stock, "get_engine", lambda: DummyEngine())

    result = stock.adjust_stock_level(1, 8, username="bot")
    assert result["movement_created"] is True
    assert result["movement_type"] == "ENTREE"
    assert result["movement_quantity"] == 3
