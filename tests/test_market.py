import pandas as pd
import pytest

from tests.data_builder import DataBuilder


class TestMarket:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_market_is_interval_start(self):
        market_half_hour = self._data_builder.add_market(interval_hours=0.5)
        assert market_half_hour.is_interval_start(pd.Timestamp("2025-01-01 00:00:00"))
        assert market_half_hour.is_interval_start(pd.Timestamp("2025-01-01 00:30:00"))
        assert not market_half_hour.is_interval_start(
            pd.Timestamp("2025-01-01 00:15:00")
        )

        market_one_hour = self._data_builder.add_market(interval_hours=1.0)
        assert market_one_hour.is_interval_start(pd.Timestamp("2025-01-01 00:00:00"))
        assert not market_one_hour.is_interval_start(
            pd.Timestamp("2025-01-01 00:30:00")
        )

    def test_market_average_price(self) -> None:
        prices = pd.Series(
            data=[50.0, 60.0, 70.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=3, freq="1h"),
        )
        market = self._data_builder.add_market(prices=prices)
        assert market.average_price == 60.0
