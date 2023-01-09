#
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib

from elexon import wind, demand
from sheffield import solar

WIND_CAPEX_KW = 1500
SOLAR_CAPEX_KW = 1000
BATTERY_CAPEX_KWH = 200


def get_data():
    """
    Get daily demand and wind, solar generation.

    Returns:
        Dataframe of daily data.

    """
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)

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


def compute() -> pd.DataFrame:
    # get the raw data
    df = get_data()

    # compute total wind and solar generation
    df["supply_mw"] = df["wind_mw"] + df["solar_mw"]

    # factor up wind and solar to match total annual demand
    mean_demand = df.demand_mw.mean()
    mean_supply = df.supply_mw.mean()
    multiplier = mean_demand / mean_supply

    print(f"Average demand {df.demand_mw.mean():.0f}")
    print(f"Average supply {df.supply_mw.mean():.0f}")
    print(f"Multiplier: {multiplier:.1f}")

    df["supply_mult_mw"] = df["supply_mw"] * multiplier

    # sanity check
    assert abs(df.demand_mw.mean() - df.supply_mult_mw.mean()) < 1

    # compute generation surplus and deficit
    df["delta_mw"] = df["supply_mult_mw"] - df["demand_mw"]

    df["surplus_mw"] = df["delta_mw"][df["delta_mw"] >= 0]
    df["deficit_mw"] = df["delta_mw"][df["delta_mw"] < 0]

    # compute storage balance
    df["storage_balance_GWh"] = df["delta_mw"].cumsum() * 24 / 1000
    df["storage_balance_GWh"] = df["storage_balance_GWh"] - df["storage_balance_GWh"].min()

    return df


def annotate_title(ax: matplotlib.axis, title: str, x=10, y=185, color="black") -> None:
    """Return a"""
    ax.annotate(
        title,
        (0, 0),
        (x, y),
        color=color,
        xycoords="axes points",
        textcoords="offset pixels",
        fontsize=8,
        fontweight=600
    )


def plot(df: pd.DataFrame):
    # Initialise a four panel figure.

    fig = plt.figure()
    width_inches = 10
    height_inches = width_inches * 700 / 1280
    fig.set_size_inches(width_inches, height_inches)
    fig.patch.set_facecolor("white")
    fig.suptitle(
        f"UK renewable energy generation and storage requirement to meet demand (2022)"
    )
    # gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.2)
    # (ax1, ax2), (ax3, ax4) = gs.subplots()
    # axes = [ax1, ax2, ax3, ax4]

    gs = GridSpec(4, 2, figure=fig)
    ax1 = fig.add_subplot(gs[:2, 0])
    ax2 = fig.add_subplot(gs[:2, 1])
    ax3 = fig.add_subplot(gs[2:4, 0])
    ax4 = fig.add_subplot(gs[2, 1])
    ax5 = fig.add_subplot(gs[3, 1])

    # Top left: Energy demand and supply.

    title = "[A] Energy demand and solar and wind supply (GW)"
    annotate_title(ax1, title)

    periods = 30

    # wind
    df["wind_gw"] = df["wind_mw"] / 1000
    df["wind_gw_avg"] = df["wind_gw"].ewm(span=periods).mean()
    ax1.fill_between(df.index, df["wind_gw"], df["wind_gw_avg"], linewidth=0.5, color="tab:blue", alpha=0.25)
    df["wind_gw_avg"].plot(ax=ax1, label="wind", color="tab:blue")

    # solar
    df["solar_gw"] = df["solar_mw"] / 1000
    df["solar_gw_avg"] = df["solar_gw"].ewm(span=periods).mean()
    ax1.fill_between(df.index, df["solar_gw"], df["solar_gw_avg"], linewidth=0.5, color="tab:orange", alpha=0.25)
    df["solar_gw_avg"].plot(ax=ax1, label="solar", color="tab:orange")

    # demand
    df["demand_gw"] = df["demand_mw"] / 1000
    df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    ax1.fill_between(df.index, df["demand_gw"], df["demand_gw_avg"], linewidth=0.5, color="tab:green", alpha=0.25)
    df["demand_gw_avg"].plot(ax=ax1, label="demand", color="tab:green")

    ax1.set(xlabel=None)
    ax1.set(xticklabels=[])
    ax1.legend()

    # Top right: Energy demand and supply.

    title = "[B] Energy demand and actual solar+wind supply (GW)"
    annotate_title(ax2, title)

    periods = 30

    # supply
    df["supply_gw"] = df["supply_mw"] / 1000
    df["supply_gw_avg"] = df["supply_gw"].ewm(span=periods).mean()
    ax2.fill_between(df.index, df["supply_gw"], df["supply_gw_avg"], linewidth=0.5, color="tab:purple", alpha=0.25)
    df["supply_gw_avg"].plot(ax=ax2, label="wind+solar", color="tab:purple")

    # demand
    df["demand_gw"] = df["demand_mw"] / 1000
    df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    ax2.fill_between(df.index, df["demand_gw"], df["demand_gw_avg"], linewidth=0.5, color="tab:green", alpha=0.25)
    df["demand_gw_avg"].plot(ax=ax2, label="demand", color="tab:green")

    ax2.set(xlabel=None)
    ax2.set(xticklabels=[])
    ax2.legend()

    # Bottom left: Energy demand and supply.

    title = "[C] Energy demand and solar+wind as 100% of supply (GW)"
    annotate_title(ax3, title)

    periods = 30

    # supply
    df["supply_mult_gw"] = df["supply_mult_mw"] / 1000
    df["supply_mult_gw_avg"] = df["supply_mult_gw"].ewm(span=periods).mean()
    ax3.fill_between(df.index, df["supply_mult_gw"], df["supply_mult_gw_avg"], linewidth=0.5, color="tab:purple",
                     alpha=0.25)
    df["supply_mult_gw_avg"].plot(ax=ax3, label="wind+solar", color="tab:purple")

    # demand
    df["demand_gw"] = df["demand_mw"] / 1000
    df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    ax3.fill_between(df.index, df["demand_gw"], df["demand_gw_avg"], linewidth=0.5, color="tab:green", alpha=0.25)
    df["demand_gw_avg"].plot(ax=ax3, label="demand", color="tab:green")

    ax3.set(xlabel=None)
    ax3.legend(loc="lower right")

    # Bottom right (top): Generation balance.

    title = "[E] Generation balance (GW)"
    annotate_title(ax4, title, y=5)

    df["surplus_gw"] = df["surplus_mw"].fillna(0) / 1000
    df["deficit_gw"] = df["deficit_mw"].fillna(0) / 1000
    df["surplus_gw"].plot(ax=ax4, label="surplus", linewidth=1, color="tab:green")
    ax4.fill_between(df.index, df["surplus_gw"], color="tab:green", alpha=0.1)
    df["deficit_gw"].plot(ax=ax4, label="deficit", linewidth=1, color="tab:red")
    ax4.fill_between(df.index, df["deficit_gw"], color="tab:red", alpha=0.1)

    ax4.set(xticklabels=[])
    ax4.set(xlabel=None)

    # Bottom right (bottom): Storage requirement.

    title = "[F] Storage requirement (TWh)"
    annotate_title(ax5, title, y=5)

    periods = 30

    # storage balance
    df["storage_balance_TWh"] = df["storage_balance_GWh"] / 1000
    df["storage_balance_TWh"].plot(ax=ax5, label="storage balance", color="tab:red")
    ax5.fill_between(df.index, df["storage_balance_TWh"], color="tab:red", alpha=0.1)

    # demand
    # df["demand_gw"] = df["demand_mw"] / 1000
    # df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    # ax3.fill_between(df.index, df["demand_gw"], df["demand_gw_avg"], linewidth=0.5, color="tab:green", alpha=0.25)
    # df["demand_gw_avg"].plot(ax=ax3, label="demand", color="tab:green")

    ax5.set(xlabel=None)

    # ax4.legend()

    print(df.columns)

    # df.plot(y=["supply_mult_mwy_mult_mw", "demand_mw"])
    # df.plot(y=["storage_balance_GWh"])

    plt.show()


if __name__ == "__main__":
    df = compute()
    plot(df)
