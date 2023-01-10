"""
This script fetches demand and solar and wind demand for a given period, generates an illustrative figure, and computes
the hypothetical cost of generation and storage capacity to match demand with wind and solar generation.
"""

from datetime import datetime
from pprint import pprint

import pandas as pd

from elexon import wind, demand
from renewable_cost.costdata import LCOEParams, compute_costs
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

    lcoe_params_wind = LCOEParams(
        periods_years=20,
        discount_rate=0.03,
        capital_cost_kw=1500,
        capacity_factor=0.25,
        fixed_OM_cost_kw_yr=25,
    )

    lcoe_params_solar = LCOEParams(
        periods_years=20,
        discount_rate=0.03,
        capital_cost_kw=1000,
        capacity_factor=0.25,
        fixed_OM_cost_kw_yr=25,
    )

    battery_cost_kwh = 200

    df = compute_profiles()
    cost_data = compute_costs(df, lcoe_params_wind, lcoe_params_solar, battery_cost_kwh)

    # Print analysis

    print(f"Average demand {df.demand_mw.mean() / 1000:.1f} GW")
    print(
        f"Average supply {df.supply_mw.mean() / 1000:.1f} GW (wind: {df.wind_mw.mean() / 1000:.1f} GW / solar: {df.solar_mw.mean() / 1000:.1f} GW)"
    )

    print("Additional cost:")
    print(
        f"- wind {cost_data.wind_mw / 1000:.1f} GW / £{round(cost_data.wind_cost / pow(10, 9), 1):.1f}bn @ {cost_data.lcoe_wind_mwh:.0f} £/MWh"
    )
    print(
        f"- solar {cost_data.solar_mw / 1000:.1f} GW / £{round(cost_data.solar_cost / pow(10, 9), 1):.1f}bn @ {cost_data.lcoe_solar_mwh:.0f} £/MWh"
    )
    print(
        f"- battery  {round(cost_data.max_storage_gwh) / 1000:.1f} TWh (peak) / £{round(cost_data.storage_cost) / pow(10, 12):.1f}tn"
    )

    plot(df)
