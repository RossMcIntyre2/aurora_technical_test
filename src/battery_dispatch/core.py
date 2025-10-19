import pandas as pd

from battery_dispatch.values.battery import Battery, BatteryCommitment, BatteryState
from battery_dispatch.values.market import Market


def create_market_from_data(csv_path: str, interval_hours: float) -> Market:
    prices = pd.read_csv(csv_path, parse_dates=True)
    price_series = pd.Series(
        data=prices["price"].values,
        index=pd.to_datetime(prices["timestamp"].dt.strftime("%m/%d/%Y %H:%M")),
    )
    market = Market(
        name=f"Market_{interval_hours}h",
        prices=price_series,
        interval_hours=interval_hours,
    )
    return market


def run_battery_simulation() -> None:
    print("Running battery simulation... (this is a placeholder function)")
    market_1 = create_market_from_data(
        csv_path="data/half-hourly-data.csv", interval_hours=0.5
    )
    market_2 = create_market_from_data(
        csv_path="data/hourly-data.csv", interval_hours=1.0
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
    print("Running battery simulation for scenario... (this is a placeholder function)")
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

        print(
            f"At {timestamp}, battery state of charge: {battery.state_of_charge_mwh} MWh"
        )
        # Since we limit the battery to only be able to do one operation at once (charge or discharge)
        # we are basically choosing between charging or discharging based on the best price across all markets
        # so we can loop through all markets and find the best option to decide whether we charge or discharge

        best_commitments = []
        # Effective because the plan is to compare against the average -
        # using this method I can only really evaluate profit at the end of the interval
        # best_effective_profit = 0.0

        for battery_state in [BatteryState.CHARGING, BatteryState.DISCHARGING]:
            # Make sure we're not in the opposite state
            print("Are we in the right state?")

            for market in all_markets:
                if not market.is_interval_start(timestamp=timestamp):
                    # Battery must only commit its capacity for the entire market interval
                    continue

                price = market.prices.get(timestamp)
                if price is None:
                    continue

                if battery_state is BatteryState.CHARGING:
                    charge_profit, charge_commitments = (
                        get_potential_profit_from_charge()
                    )
                else:
                    assert battery_state is BatteryState.DISCHARGING
                    discharge_profit, discharge_commitments = (
                        get_potential_profit_from_discharge()
                    )

            if charge_profit > discharge_profit and charge_profit > 0:
                print("Decided to charge the battery.")
                best_commitments = charge_commitments
            elif discharge_profit > charge_profit and discharge_profit > 0:
                print("Decided to discharge the battery.")
                best_commitments = discharge_commitments
            else:
                print("Decided to remain idle.")
                best_commitments = []

            if len(best_commitments) > 0:
                for commitment in best_commitments:
                    battery.add_commitments(new_commitments=[commitment])

    battery_revenue = 10
    battery_cost = 5
    print(
        f"\n Total Revenue: {battery_revenue:.2f} GBP, Total Cost: {battery_cost:.2f} GBP, Total Profit: {battery_revenue - battery_cost:.2f} GBP, Final State of Charge: {battery.state_of_charge_mwh:.2f} MWh"
    )


def get_potential_profit_from_charge() -> tuple[float, list[BatteryCommitment]]:
    print(
        "Calculating potential profit from charge... (this is a placeholder function)"
    )
    return 0.0, []


def get_potential_profit_from_discharge() -> tuple[float, list[BatteryCommitment]]:
    print(
        "Calculating potential profit from discharge... (this is a placeholder function)"
    )
    return 0.0, []


if __name__ == "__main__":
    run_battery_simulation()
