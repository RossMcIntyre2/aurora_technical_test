import pytest

from tests.data_builder import DataBuilder


class TestMarket:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_market_is_interval_start(self):
        pass
