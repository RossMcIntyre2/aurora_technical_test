import copy
import dataclasses
from enum import Enum

import pandas as pd

from battery_dispatch.values.market import Market


class CannotDispatchBatteryError(Exception):
    pass


class CannotAddCommitmentError(Exception):
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
    revenue: float = 0.0
    cost: float = 0.0

    def commit_expired_commitments(
        self, *, current_timestamp: pd.DatetimeIndex
    ) -> None:
        commitments_to_commit = [
            commitment
            for commitment in self.commitments
            if commitment.end_time <= current_timestamp
        ]
        for commitment in commitments_to_commit:
            # Remove commitment first to avoid its commitment being incorporated
            # into available capacity/state_of_charge calculations
            self.commitments.remove(commitment)
            self.commit(commitment=commitment)
            self._update_financial_state(
                commitment_type=commitment.commitment_type,
                value=commitment.energy_mwh
                * commitment.market.prices[commitment.start_time],
            )

    def _update_financial_state(
        self, *, commitment_type: BatteryCommitmentType, value: float
    ) -> None:
        if commitment_type is BatteryCommitmentType.CHARGE:
            self.cost += value
        elif commitment_type is BatteryCommitmentType.DISCHARGE:
            self.revenue += value

    def current_mode(self, *, current_timestamp: pd.DatetimeIndex) -> BatteryState:
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

    def available_state_of_charge(
        self, *, current_timestamp: pd.DatetimeIndex
    ) -> float:
        discharge_commitment = sum(
            commitment.energy_mwh
            for commitment in self.commitments
            if commitment.commitment_type is BatteryCommitmentType.DISCHARGE
            and commitment.start_time <= current_timestamp < commitment.end_time
        )
        return self.state_of_charge_mwh - discharge_commitment

    def available_capacity(self, *, current_timestamp: pd.DatetimeIndex) -> float:
        charge_commitment = sum(
            commitment.energy_mwh
            for commitment in self.commitments
            if commitment.commitment_type is BatteryCommitmentType.CHARGE
            and commitment.start_time <= current_timestamp < commitment.end_time
        )
        return self.capacity_mwh - self.state_of_charge_mwh - charge_commitment

    def can_commit(
        self,
        *,
        energy_mwh: float,
        commitment_type: BatteryCommitmentType,
        current_timestamp: pd.DatetimeIndex,
    ) -> bool:
        # Check we aren't trying to discharge when we are charging (or vice versa)
        current_mode = self.current_mode(current_timestamp=current_timestamp)
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
            return self.available_capacity(current_timestamp=current_timestamp) >= 0
        elif commitment_type is BatteryCommitmentType.DISCHARGE:
            return (
                self.available_state_of_charge(current_timestamp=current_timestamp)
                >= energy_mwh
            )

    def add_commitments(self, *, new_commitments: list[BatteryCommitment]) -> None:
        if len(self.commitments) != 0 or len(new_commitments) != 1:
            # Assume any current commitments are using the maximum power available,
            # and we have committed to them already so we cannot take on more than one commitment
            raise CannotAddCommitmentError(
                "Cannot add new commitments to battery with existing commitments."
            )
        self.commitments += new_commitments

    def commit(
        self,
        *,
        commitment: BatteryCommitment,
        output: bool = True,
    ) -> BatteryCommitment:
        energy = commitment.energy_mwh

        if not self.can_commit(
            energy_mwh=energy,
            commitment_type=commitment.commitment_type,
            current_timestamp=commitment.start_time,
        ):
            raise CannotDispatchBatteryError(
                "Cannot commit to the requested battery operation."
            )

        actual_energy_committed = energy

        if commitment.commitment_type is BatteryCommitmentType.CHARGE:
            new_state_of_charge = self.state_of_charge_mwh + energy
            if new_state_of_charge > self.capacity_mwh:
                new_state_of_charge = self.capacity_mwh
                actual_energy_committed = new_state_of_charge - self.state_of_charge_mwh
            self.state_of_charge_mwh = new_state_of_charge

        else:
            assert commitment.commitment_type is BatteryCommitmentType.DISCHARGE
            self.state_of_charge_mwh -= energy
            if self.state_of_charge_mwh < 0:
                raise ValueError("State of charge cannot be negative after discharge.")

        if output:
            print(
                f"Committed to {commitment.commitment_type.name} "
                f"{actual_energy_committed} MWh from "
                f"{commitment.start_time} to {commitment.end_time}."
                f"on market {commitment.market.name}"
            )

        commitment_copy = copy.deepcopy(commitment)
        commitment_copy.energy_mwh = actual_energy_committed
        return commitment_copy
