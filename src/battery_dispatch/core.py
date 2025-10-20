import copy
import dataclasses

import pandas as pd

from battery_dispatch.values.battery import (
    Battery,
    BatteryCommitment,
    BatteryCommitmentType,
    BatteryState,
    CannotAddCommitmentError,
    CannotDispatchBatteryError,
)
from battery_dispatch.values.market import Market


@dataclasses.dataclass
class CommitmentEvaluation:
    commitment: BatteryCommitment
    revenue: float


def create_market_from_data(csv_path: str, interval_hours: float) -> Market:
    prices = pd.read_csv(csv_path, parse_dates=True)
    price_series = pd.Series(
        data=prices["price [£/MWh]"].values,
        index=pd.to_datetime(prices["timestamp"], format="%m/%d/%y %H:%M"),
    )
    market = Market(
        name=f"Market_{interval_hours}h",
        prices=price_series,
        interval_hours=interval_hours,
    )
    return market


def run_battery_simulation() -> None:
    market_1 = create_market_from_data(
        csv_path="src/data/half-hourly-data.csv", interval_hours=0.5
    )
    market_2 = create_market_from_data(
        csv_path="src/data/hourly-data.csv", interval_hours=1.0
    )
    battery = Battery(
        capacity_mwh=4.0,
        max_charge_mw=2.0,
        max_discharge_mw=2.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        state_of_charge_mwh=0,
    )
    run_battery_simulation_for_scenario(
        battery=battery,
        all_markets=[market_1, market_2],
    )


def run_battery_simulation_for_scenario(
    battery: Battery,
    all_markets: list[Market],
) -> None:
    # This is for a first pass, maybe could do some weighting
    # in future, but we should replace this anyway with a smarter approach
    average_market_price = sum([market.average_price for market in all_markets]) / len(
        all_markets
    )

    min_interval = min([market.interval_hours for market in all_markets])
    max_interval = max([market.interval_hours for market in all_markets])

    open_time = min([min(market.prices.index) for market in all_markets])
    close_time = max([max(market.prices.index) for market in all_markets])

    # Generate timestamps from open_time to close_time with min_interval
    # frequency so we can consider at every interval
    timestamps = pd.date_range(
        start=open_time,
        end=close_time + pd.Timedelta(hours=max_interval),
        freq=f"{min_interval}h",
    )
    for timestamp in timestamps:
        # Commit commitments now, as this represents the end of the previous interval
        battery.commit_expired_commitments(current_timestamp=timestamp)

        best_commitments: list[CommitmentEvaluation] = []
        # Effective profit because the plan is to compare against the average -
        # using this method I can only really evaluate profit at the end of the interval
        best_effective_profit = 0.0

        # Since we limit the battery to only be able to do one operation at once (charge or discharge)
        # we are basically choosing between charging or discharging based on the best price across all markets
        # so we can loop through all markets and find the best option to decide whether we charge or discharge

        evaluations_by_battery_state: dict[BatteryState, list[CommitmentEvaluation]] = {
            BatteryState.CHARGING: [],
            BatteryState.DISCHARGING: [],
        }

        for battery_state in evaluations_by_battery_state.keys():
            if (
                battery_state is not battery.current_mode(current_timestamp=timestamp)
                and battery.current_mode(current_timestamp=timestamp)
                is not BatteryState.IDLE
            ):
                # Can't cancel commitments mid-way through, so we can't switch states
                continue

            for market in all_markets:
                if not market.is_interval_start(timestamp=timestamp):
                    # Battery must only commit its capacity for the entire market interval
                    continue

                price = market.prices.get(timestamp)
                if price is None:
                    continue

                duration = market.interval_timedelta()

                if battery_state is BatteryState.CHARGING:
                    dispatch_fn = attempt_charge
                else:
                    assert battery_state is BatteryState.DISCHARGING
                    dispatch_fn = attempt_discharge

                dispatch_fn(
                    battery_state=battery_state,
                    battery=battery,
                    duration=duration,
                    market=market,
                    price=price,
                    timestamp=timestamp,
                    average_market_price=average_market_price,
                    evaluations_by_battery_state=evaluations_by_battery_state,
                )

        # Select the best commitments
        for (
            battery_state,
            potential_evaluations,
        ) in evaluations_by_battery_state.items():
            # Sort by highest effective profit (this is not actual revenue)
            potential_evaluations.sort(key=lambda ev: ev.revenue, reverse=True)
            evaluations, profit = _get_possible_evaluations(
                potential_evaluations=potential_evaluations,
                battery=battery,
            )

            if profit > best_effective_profit:
                best_effective_profit = profit
                best_commitments = evaluations

        if len(best_commitments) > 0:
            assert len(best_commitments) == 1
            for evaluation in best_commitments:
                commitment = evaluation.commitment
                try:
                    battery.add_commitments(new_commitments=[commitment])
                except CannotAddCommitmentError:
                    continue

    print(
        f"\n Total Revenue: {battery.revenue:.2f} GBP, Total Cost: {battery.cost:.2f} GBP, Total Profit: {battery.revenue - battery.cost:.2f} GBP, Final State of Charge: {battery.state_of_charge_mwh:.2f} MWh"
    )


# TODO: Abstract common logic between attempt_charge and attempt_discharge
def attempt_charge(
    battery_state: BatteryState,
    battery: Battery,
    duration: pd.Timedelta,
    market: Market,
    price: float,
    timestamp: pd.DatetimeIndex,
    average_market_price: float,
    evaluations_by_battery_state: dict[BatteryState, list[CommitmentEvaluation]],
) -> None:
    energy = battery.max_charge_mw * duration.total_seconds() / 3600
    if battery.available_capacity(current_timestamp=timestamp) < energy:
        energy = battery.available_capacity(current_timestamp=timestamp)

    cost = price * energy
    average_cost_for_energy = average_market_price * energy
    cost_improvement_from_average = average_cost_for_energy - cost
    print(cost_improvement_from_average)
    if cost_improvement_from_average > 0:
        charge_commitment = BatteryCommitment(
            market=market,
            commitment_type=BatteryCommitmentType.CHARGE,
            energy_mwh=energy,
            start_time=timestamp,
            end_time=timestamp + duration,
        )
        evaluations_by_battery_state[battery_state].append(
            CommitmentEvaluation(
                revenue=cost_improvement_from_average,
                commitment=charge_commitment,
            )
        )


def attempt_discharge(
    battery_state: BatteryState,
    battery: Battery,
    duration: pd.Timedelta,
    market: Market,
    price: float,
    timestamp: pd.DatetimeIndex,
    average_market_price: float,
    evaluations_by_battery_state: dict[BatteryState, list[CommitmentEvaluation]],
) -> None:
    energy = battery.max_discharge_mw * duration.total_seconds() / 3600
    if battery.state_of_charge_mwh < energy:
        energy = battery.state_of_charge_mwh

    revenue = price * energy
    average_revenue_for_energy = average_market_price * energy
    revenue_improvement_from_average = revenue - average_revenue_for_energy
    if revenue_improvement_from_average > 0:
        discharge_commitment = BatteryCommitment(
            market=market,
            commitment_type=BatteryCommitmentType.DISCHARGE,
            energy_mwh=energy,
            start_time=timestamp,
            end_time=timestamp + duration,
        )
        evaluations_by_battery_state[battery_state].append(
            CommitmentEvaluation(
                revenue=revenue_improvement_from_average,
                commitment=discharge_commitment,
            )
        )


def _get_possible_evaluations(
    *,
    potential_evaluations: list[CommitmentEvaluation],
    battery: Battery,
) -> tuple[list[CommitmentEvaluation], float]:
    # Make a copy of the battery to simulate commitments
    # We could maybe use dataclasses.replace here but deepcopy is safer because of nested structures
    battery_copy = copy.deepcopy(battery)

    profit = 0.0
    evaluations: list[CommitmentEvaluation] = []

    for evaluation in potential_evaluations:
        commitment = evaluation.commitment
        try:
            final_commitment = battery_copy.commit(commitment=commitment, output=False)
            # Update the final commitment to make sure we have the correct energy dispatched,
            # as we could accidentally overestimate the profit if we're not able to dispatch the full amount
            profit += evaluation.revenue * (
                final_commitment.energy_mwh / commitment.energy_mwh
            )
            evaluation.commitment = final_commitment
            evaluations.append(evaluation)

            # Take the first successful commitment only as it only makes sense to dispatch to the best option
            break

        except CannotDispatchBatteryError:
            continue

    return evaluations, profit


if __name__ == "__main__":
    run_battery_simulation()
