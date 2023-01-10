"""
This script fetches demand and solar and wind demand for a given period, generates an illustrative figure, and computes
the hypothetical cost of generation and storage capacity to match demand with wind and solar generation.
"""

from datetime import datetime
from pprint import pprint

import pandas as pd

from elexon import wind, demand
from renewable_cost.costs import LCOEParams, Capex, compute_costs
from renewable_cost.plot import plot
from sheffield import solar

pd.set_option("display.max_rows", 500)
pd.set_option("display.max_columns", 500)


def get_data():
    """
    Get daily demand and wind and solar generation.

    Returns:
        Dataframe with time series of daily demand, wind and solar generation in MW.

    """

    start_time = datetime(2022, 1, 1)
    end_time = datetime(2022, 12, 31)

    wind_df = wind(start_time, end_time, from_disk=True)
    wind_df = wind_df.resample("1D").mean()

    solar_df = solar(start_time, end_time, from_disk=True)
    solar_df = solar_df.resample("1D").mean()

    demand_df = demand(start_time, end_time, from_disk=True)
    demand_df = demand_df.resample("1D").mean()

    df = pd.DataFrame(columns=["demand_mw", "wind_mw", "solar_mw"])

    df["wind_mw"] = wind_df
    df["solar_mw"] = solar_df["generation_mw"]
    df["demand_mw"] = demand_df

    return df


def compute_profiles() -> pd.DataFrame:
    """Compute profiles to support plotting and cost analysis."""

    # get the raw data
    df = get_data()

    # compute total wind and solar generation
    df["supply_mw"] = df["wind_mw"] + df["solar_mw"]

    # factor up wind and solar to match total annual demand
    mean_demand = df.demand_mw.mean()
    mean_supply = df.supply_mw.mean()
    factor = mean_demand / mean_supply

    df["supply_mult_mw"] = df["supply_mw"] * factor

    # sanity check
    assert abs(df.demand_mw.mean() - df.supply_mult_mw.mean()) < 1

    # compute generation surplus and deficit
    df["delta_mw"] = df["supply_mult_mw"] - df["demand_mw"]
    df["surplus_mw"] = df["delta_mw"][df["delta_mw"] >= 0]
    df["deficit_mw"] = df["delta_mw"][df["delta_mw"] < 0]

    # compute storage balance
    df["storage_balance_GWh"] = df["delta_mw"].cumsum() * 24 / 1000
    df["storage_balance_GWh"] = (
            df["storage_balance_GWh"] - df["storage_balance_GWh"].min()
    )

    return df


if __name__ == "__main__":
    # assumptions

    capex = Capex(wind_kw=1500, solar_kw=1000, battery_kwh=200)
    lcoe_params = LCOEParams(
        periods=20,
        discount_rate=0.03,
        capital_cost=1250,
        capacity_factor=0.25,
        fixed_OM_cost=25,
    )

    df = compute_profiles()
    costs = compute_costs(df, lcoe_params, capex)

    # Print analysis

    multiplier = df.demand_mw.mean() / df.supply_mw.mean()

    print(f"Average demand {df.demand_mw.mean():.0f}")
    print(f"Average supply {df.supply_mw.mean():.0f}")
    print(f"Multiplier: {multiplier:.1f}")

    pprint(costs)

    plot(df)
