import pandas as pd
import pytest

from battery_dispatch.values.battery import (
    BatteryCommitmentType,
    BatteryState,
    CannotDispatchBatteryError,
)
from tests.data_builder import DataBuilder


class TestBattery:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self._data_builder = DataBuilder()

    def test_current_mode(self):
        charge_commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.CHARGE,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 01:00:00",
        )
        discharge_commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.DISCHARGE,
            start_time="2025-01-01 02:00:00",
            end_time="2025-01-01 03:00:00",
        )
        battery = self._data_builder.add_battery(
            commitments=[charge_commitment, discharge_commitment]
        )

        # During charging period
        current_mode = battery.current_mode(current_timestamp="2025-01-01 00:30:00")
        assert current_mode is BatteryState.CHARGING

        # Between commitments
        current_mode = battery.current_mode(current_timestamp="2025-01-01 01:30:00")
        assert current_mode is BatteryState.IDLE

        # During discharging period
        current_mode = battery.current_mode(current_timestamp="2025-01-01 02:30:00")
        assert current_mode is BatteryState.DISCHARGING

    def test_available_state_of_charge(self):
        charge_commitment = 20
        discharge_commitment = 30
        current_state_of_charge = 50
        commitments = [
            self._data_builder.add_battery_commitment(
                commitment_type=BatteryCommitmentType.CHARGE,
                energy_mwh=charge_commitment,
                start_time="2025-01-01 00:00:00",
                end_time="2025-01-01 02:30:00",
            ),
            self._data_builder.add_battery_commitment(
                commitment_type=BatteryCommitmentType.DISCHARGE,
                energy_mwh=discharge_commitment,
                start_time="2025-01-01 00:00:00",
                end_time="2025-01-01 02:30:00",
            ),
        ]
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=current_state_of_charge,
            commitments=commitments,
        )
        available_state_of_charge = battery.available_state_of_charge(
            current_timestamp="2025-01-01 00:00:00"
        )
        # Charge commitments shouldn't be taken into account
        assert (
            available_state_of_charge == current_state_of_charge - discharge_commitment
        )

    def test_available_capacity(self):
        max_capacity = 100
        charge_commitment = 20
        discharge_commitment = 30
        current_state_of_charge = 50
        commitments = [
            self._data_builder.add_battery_commitment(
                commitment_type=BatteryCommitmentType.CHARGE,
                energy_mwh=charge_commitment,
                end_time="2025-01-01 02:30:00",
            ),
            self._data_builder.add_battery_commitment(
                commitment_type=BatteryCommitmentType.DISCHARGE,
                energy_mwh=discharge_commitment,
                end_time="2025-01-01 02:30:00",
            ),
        ]
        battery = self._data_builder.add_battery(
            capacity_mwh=max_capacity,
            state_of_charge_mwh=current_state_of_charge,
            commitments=commitments,
        )
        available_capacity = battery.available_capacity(
            current_timestamp="2025-01-01 00:00:00"
        )
        # Discharge commitments shouldn't be taken into account
        assert (
            available_capacity
            == max_capacity - current_state_of_charge - charge_commitment
        )

    def test_cannot_commit_to_discharge_if_charging(self):
        commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.CHARGE,
            energy_mwh=5,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 01:00:00",
        )
        # Battery with plenty of space to ensure the fail reason is because of mismatching dispatch type
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=50,
            commitments=[commitment],
        )
        assert (
            battery.can_commit(
                energy_mwh=5,
                commitment_type=BatteryCommitmentType.DISCHARGE,
                current_timestamp="2025-01-01 00:30:00",
            )
            is False
        )

    def test_cannot_commit_to_charge_if_discharging(self):
        commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.DISCHARGE,
            energy_mwh=5,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 01:00:00",
        )
        # Battery with plenty of space to ensure the fail reason is because of mismatching dispatch type
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=50,
            commitments=[commitment],
        )
        assert (
            battery.can_commit(
                energy_mwh=5,
                commitment_type=BatteryCommitmentType.CHARGE,
                current_timestamp="2025-01-01 00:30:00",
            )
            is False
        )

    def test_cannot_commit_to_discharge_if_state_of_charge_too_low(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=10,
        )
        assert (
            battery.can_commit(
                energy_mwh=20,
                commitment_type=BatteryCommitmentType.DISCHARGE,
                current_timestamp="2025-01-01 00:00:00",
            )
            is False
        )

    def cannot_commit_to_charge_if_capacity_too_low(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=95,
        )
        # Do we actually want this? A battery should be able to commit to charge even
        # if it can't take the full amount?
        # TODO: Revisit later to decide on desired behavior, maybe this makes the algorithm
        #  more complex if we consider partial commitments
        assert (
            battery.can_commit(
                energy_mwh=10,
                commitment_type=BatteryCommitmentType.CHARGE,
                current_timestamp="2025-01-01 00:00:00",
            )
            is False
        )

    def test_commit(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=50,
        )
        commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.CHARGE,
            energy_mwh=20,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 01:00:00",
        )
        battery.commit(commitment=commitment)
        assert battery.state_of_charge_mwh == 70

        commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.DISCHARGE,
            energy_mwh=30,
            start_time="2025-01-01 02:00:00",
            end_time="2025-01-01 03:00:00",
        )
        battery.commit(commitment=commitment)
        assert battery.state_of_charge_mwh == 40

    def test_commit_raises_error_if_cannot_commit(self):
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=10,
        )
        commitment = self._data_builder.add_battery_commitment(
            commitment_type=BatteryCommitmentType.DISCHARGE,
            energy_mwh=20,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 01:00:00",
        )
        # Do we actually want to raise this in reality? Maybe we want to catch and handle it differently?
        with pytest.raises(CannotDispatchBatteryError):
            battery.commit(commitment=commitment)

    def test_commit_expired_commitments_only_commits_expired(self):
        market = self._data_builder.add_market(
            prices=pd.Series(
                data=[50.0, 60.0, 70.0],
                index=pd.date_range(
                    start="2025-01-01 00:00:00", periods=3, freq="30min"
                ),
            ),
            interval_hours=0.5,
        )
        commitment_1 = self._data_builder.add_battery_commitment(
            market=market,
            commitment_type=BatteryCommitmentType.CHARGE,
            energy_mwh=20,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 01:00:00",
        )
        commitment_2 = self._data_builder.add_battery_commitment(
            market=market,
            commitment_type=BatteryCommitmentType.CHARGE,
            energy_mwh=15,
            start_time="2025-01-01 00:00:00",
            end_time="2025-01-01 00:30:00",
        )
        battery = self._data_builder.add_battery(
            capacity_mwh=100,
            state_of_charge_mwh=50,
            commitments=[commitment_1, commitment_2],
        )
        battery.commit_expired_commitments(current_timestamp="2025-01-01 00:30:00")
        assert battery.state_of_charge_mwh == 65
        assert len(battery.commitments) == 1
