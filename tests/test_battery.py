import pytest

from tests.data_builder import DataBuilder


class TestBattery:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_available_state_of_charge(self):
        pass
