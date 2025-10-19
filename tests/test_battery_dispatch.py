import pandas as pd
import pytest

from battery_dispatch.core import run_battery_simulation_for_scenario
from tests.data_builder import DataBuilder


class TestBatteryDispatchIntegration:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_battery_dispatch_simple_scenario_single_market(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=100.0,
            max_charge_mw=10.0,
            max_discharge_mw=20.0,
            state_of_charge_mwh=50.0,
        )
        prices = pd.Series(
            data=[30.0, 40.0, 50.0, 60.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=4, freq="1h"),
        )
        market = self._data_builder.add_market(prices=prices, interval_hours=1.0)

        run_battery_simulation_for_scenario(
            battery=battery,
            all_markets=[market],
        )

        # Market average is (30+40+50+60)/4 = 45, so we would expect the battery to charge when prices < 45
        # and discharge when prices > 45. With a final state of charge of 50 + 20 - 40 = 30.
        assert battery.state_of_charge_mwh == 30.0

    def test_battery_dispatch_multiple_markets(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=200.0,
            max_charge_mw=10.0,
            max_discharge_mw=20.0,
            state_of_charge_mwh=100.0,
        )

        prices_market_1 = pd.Series(
            data=[25.0, 35.0, 45.0, 55.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=4, freq="1h"),
        )
        market_1 = self._data_builder.add_market(
            prices=prices_market_1, interval_hours=1.0
        )

        prices_market_2 = pd.Series(
            data=[20.0, 30.0, 40.0, 50.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=4, freq="1h"),
        )
        market_2 = self._data_builder.add_market(
            prices=prices_market_2, interval_hours=1.0
        )

        run_battery_simulation_for_scenario(
            battery=battery,
            all_markets=[market_1, market_2],
        )

        # Average price across both markets is (25+35+45+55 + 20+30+40+50)/8 = 37.5
        # Expect charging at prices < 37.5 and discharging at prices > 37.5
        # Final state of charge should be 100 + 10 + 10 - 20 - 20 = 80
        assert battery.state_of_charge_mwh == 80.0


class TestBatteryDispatchFunctions:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_commit_charge(self): ...

    def test_commit_discharge(self): ...
