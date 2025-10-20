import pandas as pd
import pytest

from battery_dispatch.core import (
    NUMBER_OF_HOURS_TO_LOOK_AHEAD,
    _get_highest_price_across_next_n_hours_series,
    _get_lowest_price_across_next_n_hours_series,
    run_battery_simulation_for_scenario,
)
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
        market_interval_hours = 1.0
        prices = pd.Series(
            data=[30.0, 40.0, 50.0, 60.0, 50.0, 40.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=6, freq="1h"),
        )
        highest_price_across_next_n_hours = (
            _get_highest_price_across_next_n_hours_series(
                price_series=prices,
                number_of_intervals_to_look_ahead=int(
                    NUMBER_OF_HOURS_TO_LOOK_AHEAD / market_interval_hours
                ),
            )
        )
        lowest_price_across_next_n_hours = _get_lowest_price_across_next_n_hours_series(
            price_series=prices,
            number_of_intervals_to_look_ahead=int(
                NUMBER_OF_HOURS_TO_LOOK_AHEAD / market_interval_hours
            ),
        )
        market = self._data_builder.add_market(
            prices=prices,
            highest_price_across_next_n_hours=highest_price_across_next_n_hours,
            lowest_price_across_next_n_hours=lowest_price_across_next_n_hours,
            interval_hours=market_interval_hours,
        )

        run_battery_simulation_for_scenario(
            battery=battery,
            all_markets=[market],
        )

        # Would expect charging at 30 and 40, discharging at 60 and 50
        # State of charge changes: 50 + 10 + 10 - 20 - 20 = 30
        assert battery.state_of_charge_mwh == 30.0
        # Revenue from discharging: (60*20*1 + 50*20*1) = 2200
        assert battery.revenue == 2200.0
        # Cost from charging: (30*10*1 + 40*10*1) = 700
        assert battery.cost == 700.0

    def test_battery_dispatch_multiple_markets(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=200.0,
            max_charge_mw=10.0,
            max_discharge_mw=20.0,
            state_of_charge_mwh=100.0,
        )

        market_1_interval_hours = 1.0
        prices_market_1 = pd.Series(
            data=[25.0, 35.0, 45.0, 35.0, 25.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=5, freq="1h"),
        )
        market_1_highest_price_across_next_n_hours = (
            _get_highest_price_across_next_n_hours_series(
                price_series=prices_market_1,
                number_of_intervals_to_look_ahead=int(
                    NUMBER_OF_HOURS_TO_LOOK_AHEAD / market_1_interval_hours
                ),
            )
        )
        market_1_lowest_price_across_next_n_hours = (
            _get_lowest_price_across_next_n_hours_series(
                price_series=prices_market_1,
                number_of_intervals_to_look_ahead=int(
                    NUMBER_OF_HOURS_TO_LOOK_AHEAD / market_1_interval_hours
                ),
            )
        )
        market_1 = self._data_builder.add_market(
            prices=prices_market_1,
            highest_price_across_next_n_hours=market_1_highest_price_across_next_n_hours,
            lowest_price_across_next_n_hours=market_1_lowest_price_across_next_n_hours,
            interval_hours=1.0,
        )

        market_2_interval_hours = 1.0
        prices_market_2 = pd.Series(
            data=[20.0, 30.0, 40.0, 30.0, 20.0],
            index=pd.date_range(start="2025-01-01 00:00:00", periods=5, freq="1h"),
        )
        market_2_highest_price_across_next_n_hours = (
            _get_highest_price_across_next_n_hours_series(
                price_series=prices_market_2,
                number_of_intervals_to_look_ahead=int(
                    NUMBER_OF_HOURS_TO_LOOK_AHEAD / market_2_interval_hours
                ),
            )
        )
        market_2_lowest_price_across_next_n_hours = (
            _get_lowest_price_across_next_n_hours_series(
                price_series=prices_market_2,
                number_of_intervals_to_look_ahead=int(
                    NUMBER_OF_HOURS_TO_LOOK_AHEAD / market_2_interval_hours
                ),
            )
        )
        market_2 = self._data_builder.add_market(
            prices=prices_market_2,
            highest_price_across_next_n_hours=market_2_highest_price_across_next_n_hours,
            lowest_price_across_next_n_hours=market_2_lowest_price_across_next_n_hours,
            interval_hours=1.0,
        )

        run_battery_simulation_for_scenario(
            battery=battery,
            all_markets=[market_1, market_2],
        )

        # Would expect charging at 20 (not 25 because they occur at the same time and 20 is cheaper),
        # discharging at 45 and 35
        # State of charge changes: 100 + 10 - 20 - 20 = 70
        assert battery.state_of_charge_mwh == 70.0
        # Revenue from discharging: (45*20*1 + 35*20*1) = 1600
        assert battery.revenue == 1600.0
        # Cost from charging: (20*10*1) = 200
        assert battery.cost == 200.0


class TestBatteryDispatchFunctions:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_commit_charge(self): ...

    def test_commit_discharge(self): ...


class TestCreateMarketFromData:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_create_market_from_data(self): ...
