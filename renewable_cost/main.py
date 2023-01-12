"""
This script fetches demand and solar and wind demand for a given period, generates an illustrative figure, and computes
the hypothetical cost of generation and storage capacity to match demand with wind and solar generation.
"""

from datetime import datetime
from pprint import pprint

import pandas as pd

from elexon import wind, demand
from renewable_cost.costdata import LCOEParams, compute_costs, compute_lcoe
from renewable_cost.plot import plot
from sheffield import solar

# pretty print dataframes
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
pd.set_option("display.colheader_justify", "center")
pd.set_option("display.precision", 3)


def get_data(year: int, from_disk=True):
    """
    Get daily demand and wind and solar generation.

    Returns:
        Dataframe with time series of daily demand, wind and solar generation in MW.

    """

    start_time = datetime(year, 1, 1)
    end_time = datetime(year, 12, 31)

    wind_df = wind(start_time, end_time, from_disk=from_disk)
    wind_df = wind_df.resample("1D").mean()

    solar_df = solar(start_time, end_time, from_disk=from_disk)
    solar_df = solar_df.resample("1D").mean()

    demand_df = demand(start_time, end_time, from_disk=from_disk)
    demand_df = demand_df.resample("1D").mean()

    df = pd.DataFrame(columns=["demand_mw", "wind_mw", "solar_mw"])

    df["wind_mw"] = wind_df
    df["solar_mw"] = solar_df["generation_mw"]
    df["demand_mw"] = demand_df

    return df


def compute_profiles(
        year: int = 2022,
        demand_multiplier: float = 1.0,
        battery_loss: float = 0.0,
        from_disk: bool = True,
) -> pd.DataFrame:
    """
    Compute profiles to support plotting and cost analysis.

    Args:
        year: The year to get data for
        demand_multiplier: Amount to increase demand by to account for electrification
        battery_loss: Battery loss over a charge/discharge cycle
        from_disk: Get the data from disk (assumes its been run previously for the specified year)

    Returns:
        Dataframe with a day averaged timeseries of profiles.
    """

    # get the raw data
    df = get_data(year=year, from_disk=from_disk)

    # compute total wind and solar generation
    df["supply_mw"] = df["wind_mw"] + df["solar_mw"]

    # factor up wind and solar to match total annual demand
    equivalent_demand_mw = df.demand_mw * demand_multiplier
    mean_equivalent_demand_mw = equivalent_demand_mw.mean()
    mean_supply_mw = df.supply_mw.mean()
    factor = mean_equivalent_demand_mw / mean_supply_mw

    df["equivalent_demand_mw"] = equivalent_demand_mw
    df["supply_mult_mw"] = df["supply_mw"] * factor

    # sanity check
    assert abs(df.demand_mw.mean() * demand_multiplier - df.supply_mult_mw.mean()) < 1

    # compute generation surplus and deficit
    df["delta_mw"] = df["supply_mult_mw"] - df["equivalent_demand_mw"]
    df["surplus_mw"] = df["delta_mw"][df["delta_mw"] >= 0]
    df["deficit_mw"] = df["delta_mw"][df["delta_mw"] < 0]

    # compute storage balance

    # temp_df = pd.DataFrame(columns=["delta_mw", "surplus_mw", "deficit_mw"])
    # temp_df["delta_mw"] = df["delta_mw"]
    # temp_df["surplus_mw"] = df["surplus_mw"]
    # temp_df["deficit_mw"] = df["deficit_mw"]
    # temp_df["adjusted_mw"] = df["surplus_mw"].fillna(0) + df["deficit_mw"].fillna(0) * (1 + battery_loss)
    # temp_df["check"] = temp_df["delta_mw"] - temp_df["adjusted_mw"]
    #
    # print(temp_df.head(100))

    adjusted_storage_balance_mw = df["surplus_mw"].fillna(0) + df["deficit_mw"].fillna(
        0
    ) * (1 + battery_loss)
    df["storage_balance_GWh"] = adjusted_storage_balance_mw.cumsum() * 24 / 1000

    df["storage_balance_GWh"] = (
            df["storage_balance_GWh"] - df["storage_balance_GWh"].min()
    )

    return df


if __name__ == "__main__":
    # assumptions

    # ‘Electricity Generation Costs 2020’. 2020. UK Government. Table 2.3
    lcoe_params_wind = LCOEParams(
        periods_years=30,
        discount_rate=0.03,
        capital_cost_kw=1300,
        capacity_factor=0.25,
        fixed_OM_cost_kw_yr=28,
    )

    # ‘Electricity Generation Costs 2020’. 2020. UK Government. Table 2.1
    lcoe_params_solar = LCOEParams(
        periods_years=35,
        discount_rate=0.03,
        capital_cost_kw=400,
        capacity_factor=0.25,
        fixed_OM_cost_kw_yr=6.7,
    )

    battery_cost_kwh = 200

    # the factor by which electricity demand increases after substituting for hydrocarbon
    demand_multiplier = 1.5

    # battery loss over a charge/discharge cycle
    battery_loss = 0.1

    df = compute_profiles(
        year=2022,
        demand_multiplier=demand_multiplier,
        battery_loss=battery_loss,
    )
    cost_data = compute_costs(df, lcoe_params_wind, lcoe_params_solar, battery_cost_kwh)

    # Print analysis ######################################################################

    print(f"Average demand {df.demand_mw.mean() / 1000:.1f} GW")
    print(
        f"Average supply {df.supply_mw.mean() / 1000:.1f} GW (wind: {df.wind_mw.mean() / 1000:.1f} GW / solar: {df.solar_mw.mean() / 1000:.1f} GW)"
    )

    print("Additional cost:")

    wind_cost_bn = cost_data.wind_cost / pow(10, 9)
    solar_cost_bn = cost_data.solar_cost / pow(10, 9)
    print(
        f"- wind {cost_data.wind_mw / 1000:.1f} GW / £{wind_cost_bn:.1f}bn @ {cost_data.lcoe_wind_mwh:.0f} £/MWh"
    )
    print(
        f"- solar {cost_data.solar_mw / 1000:.1f} GW / £{solar_cost_bn:.1f}bn @ {cost_data.lcoe_solar_mwh:.0f} £/MWh"
    )
    print(f"- total S+W £{(wind_cost_bn + solar_cost_bn):.1f} bn")
    print(
        f"- battery  {round(cost_data.max_storage_gwh) / 1000:.1f} TWh (peak) / £{round(cost_data.storage_cost) / pow(10, 12):.1f}tn"
    )

    # compute storage lcoe
    storage_capacity_gw = cost_data.max_storage_gwh / (365 * 24)
    storage_cost = cost_data.storage_cost
    storage_capex_kw = storage_cost / (storage_capacity_gw * 1000 * 1000)

    lcoe_params_solar = LCOEParams(
        periods_years=35,
        discount_rate=0.03,
        capital_cost_kw=storage_capex_kw,
        capacity_factor=1,
        fixed_OM_cost_kw_yr=0,
    )
    lcoe_storage_mwh = compute_lcoe(lcoe_params_solar)
    print(f"Solar LCOE: {lcoe_storage_mwh:.0f} £/MWh")

    plot(df, demand_multiplier, battery_loss)
