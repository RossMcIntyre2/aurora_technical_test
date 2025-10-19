import dataclasses
from enum import Enum

import pandas as pd

from battery_dispatch.values.market import Market


class CannotDispatchBatteryError(Exception):
    pass


class BatteryCommitmentType(Enum):
    CHARGE = "charge"
    DISCHARGE = "discharge"


@dataclasses.dataclass
class BatteryCommitment:
    market: Market
    commitment_type: BatteryCommitmentType
    energy_mwh: float
    start_time: pd.DatetimeIndex
    end_time: pd.DatetimeIndex


class BatteryState(Enum):
    IDLE = "idle"
    CHARGING = "charging"
    DISCHARGING = "discharging"


@dataclasses.dataclass
class Battery:
    capacity_mwh: float
    max_charge_mw: float
    max_discharge_mw: float
    charge_efficiency: float
    discharge_efficiency: float
    state_of_charge_mwh: float
    commitments: list[BatteryCommitment] = dataclasses.field(default_factory=list)

    def commit_expired_commitments(
        self, current_timestamp: pd.DatetimeIndex
    ) -> None: ...

    def current_mode(self, current_timestamp: pd.DatetimeIndex) -> BatteryState: ...

    def available_state_of_charge(
        self, current_timestamp: pd.DatetimeIndex
    ) -> float: ...

    def available_capacity(self, current_timestamp: pd.DatetimeIndex) -> float: ...

    def can_commit(
        self,
        energy_mwh: float,
        commitment_type: BatteryCommitmentType,
        current_timestamp: pd.DatetimeIndex,
    ) -> bool: ...

    def add_commitments(self, new_commitments: list[BatteryCommitment]) -> None: ...

    def commit(
        self,
        commitment: BatteryCommitment,
        test_mode: bool = False,
    ) -> BatteryCommitment: ...
