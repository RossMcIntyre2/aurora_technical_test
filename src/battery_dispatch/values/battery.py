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

    def current_mode(self, current_timestamp: pd.DatetimeIndex) -> BatteryState:
        for commitment in self.commitments:
            # We should only have one type of commitment at a time if we call can_commit()
            # properly, so can safely take the first one here
            if commitment.start_time <= current_timestamp < commitment.end_time:
                return (
                    BatteryState.CHARGING
                    if commitment.commitment_type is BatteryCommitmentType.CHARGE
                    else BatteryState.DISCHARGING
                )
        return BatteryState.IDLE

    def available_state_of_charge(self, current_timestamp: pd.DatetimeIndex) -> float:
        discharge_commitment = sum(
            commitment.energy_mwh
            for commitment in self.commitments
            if commitment.commitment_type is BatteryCommitmentType.DISCHARGE
            and commitment.start_time <= current_timestamp < commitment.end_time
        )
        return self.state_of_charge_mwh - discharge_commitment

    def available_capacity(self, current_timestamp: pd.DatetimeIndex) -> float:
        charge_commitment = sum(
            commitment.energy_mwh
            for commitment in self.commitments
            if commitment.commitment_type is BatteryCommitmentType.CHARGE
            and commitment.start_time <= current_timestamp < commitment.end_time
        )
        return self.capacity_mwh - self.state_of_charge_mwh - charge_commitment

    def can_commit(
        self,
        energy_mwh: float,
        commitment_type: BatteryCommitmentType,
        current_timestamp: pd.DatetimeIndex,
    ) -> bool:
        # Check we aren't trying to discharge when we are charging (or vice versa)
        current_mode = self.current_mode(current_timestamp)
        if (
            current_mode is BatteryState.CHARGING
            and commitment_type is BatteryCommitmentType.DISCHARGE
        ) or (
            current_mode is BatteryState.DISCHARGING
            and commitment_type is BatteryCommitmentType.CHARGE
        ):
            return False

        # Check we have enough capacity / state of charge
        if commitment_type is BatteryCommitmentType.CHARGE:
            # Allow zero for now as future commitments may still be involved in this calculation
            # TODO: Refine this logic
            return self.available_capacity(current_timestamp) >= 0
        elif commitment_type is BatteryCommitmentType.DISCHARGE:
            return self.available_state_of_charge(current_timestamp) >= energy_mwh

    def add_commitments(self, new_commitments: list[BatteryCommitment]) -> None:
        self.commitments += new_commitments

    def commit(
        self,
        commitment: BatteryCommitment,
        test_mode: bool = False,
    ) -> BatteryCommitment:
        # Note: this will have to return a potentially modified commitment in case
        # of partial commitments, rather than just the original commitment as I was intending.
        # This may well be needed for efficiency reasons anyway.
        ...
