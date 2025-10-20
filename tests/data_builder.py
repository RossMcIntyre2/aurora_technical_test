from __future__ import annotations

from typing import Union

import pandas as pd

from battery_dispatch.values.battery import (
    Battery,
    BatteryCommitment,
    BatteryCommitmentType,
)
from battery_dispatch.values.market import Market
from utils import Undefined, undefined


class DataBuilder:
    def add_battery(
        self,
        capacity_mwh: Union[Undefined, float] = undefined,
        max_charge_mw: Union[Undefined, float] = undefined,
        max_discharge_mw: Union[Undefined, float] = undefined,
        charge_efficiency: Union[Undefined, float] = undefined,
        discharge_efficiency: Union[Undefined, float] = undefined,
        state_of_charge_mwh: Union[Undefined, float] = undefined,
        commitments: Union[Undefined, list[BatteryCommitment]] = undefined,
    ) -> Battery:
        if capacity_mwh is undefined:
            capacity_mwh = 100.0

        if max_charge_mw is undefined:
            max_charge_mw = 20.0

        if max_discharge_mw is undefined:
            max_discharge_mw = 20.0

        if charge_efficiency is undefined:
            charge_efficiency = 1

        if discharge_efficiency is undefined:
            discharge_efficiency = 1

        if state_of_charge_mwh is undefined:
            state_of_charge_mwh = 50.0

        if commitments is undefined:
            commitments = []

        return Battery(
            capacity_mwh=capacity_mwh,
            max_charge_mw=max_charge_mw,
            max_discharge_mw=max_discharge_mw,
            charge_efficiency=charge_efficiency,
            discharge_efficiency=discharge_efficiency,
            state_of_charge_mwh=state_of_charge_mwh,
            commitments=commitments,
        )

    def add_market(
        self,
        market_name: Union[Undefined, str] = undefined,
        prices: Union[Undefined, pd.Series[float]] = undefined,
        highest_price_across_next_n_hours: Union[
            Undefined, pd.Series[float]
        ] = undefined,
        lowest_price_across_next_n_hours: Union[
            Undefined, pd.Series[float]
        ] = undefined,
        interval_hours: Union[Undefined, float] = undefined,
    ) -> Market:
        if market_name is undefined:
            market_name = "Test Market"

        if prices is undefined:
            prices = pd.Series(
                data=[50.0, 45.0, 55.0, 60.0],
                index=pd.date_range(start="2025-01-01 00:00", periods=4, freq="1h"),
            )

        if highest_price_across_next_n_hours is undefined:
            highest_price_across_next_n_hours = pd.Series(
                data=[50.0, 60.0, 60.0, 60.0],
                index=pd.date_range(start="2025-01-01 00:00", periods=4, freq="1h"),
            )

        if lowest_price_across_next_n_hours is undefined:
            lowest_price_across_next_n_hours = pd.Series(
                data=[45.0, 45.0, 55.0, 60.0],
                index=pd.date_range(start="2025-01-01 00:00", periods=4, freq="1h"),
            )

        if interval_hours is undefined:
            interval_hours = 1.0

        return Market(
            name=market_name,
            prices=prices,
            highest_price_across_next_n_hours=highest_price_across_next_n_hours,
            lowest_price_across_next_n_hours=lowest_price_across_next_n_hours,
            interval_hours=interval_hours,
        )

    def add_battery_commitment(
        self,
        market: Union[Undefined, Market] = undefined,
        commitment_type: Union[Undefined, BatteryCommitmentType] = undefined,
        energy_mwh: Union[Undefined, float] = undefined,
        start_time: Union[Undefined, str] = undefined,
        end_time: Union[Undefined, str] = undefined,
    ) -> BatteryCommitment:
        if market is undefined:
            market = self.add_market()

        if commitment_type is undefined:
            commitment_type = BatteryCommitmentType.CHARGE

        if energy_mwh is undefined:
            energy_mwh = 10.0

        if start_time is undefined:
            start_time = pd.date_range(
                start="2025-01-01 00:00:00", periods=1, freq="1h"
            )

        if end_time is undefined:
            end_time = start_time + pd.Timedelta(hours=market.interval_hours)

        return BatteryCommitment(
            market=market,
            commitment_type=commitment_type,
            energy_mwh=energy_mwh,
            start_time=start_time,
            end_time=end_time,
        )
