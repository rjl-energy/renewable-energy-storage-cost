"""
Plot a dataframe of demand and generation data as a 5 panel figure.
"""
import matplotlib
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec


def plot(df: pd.DataFrame) -> None:
    fig = plt.figure()
    width_inches = 10
    height_inches = width_inches * 700 / 1280
    fig.set_size_inches(width_inches, height_inches)
    fig.patch.set_facecolor("white")
    fig.suptitle(
        f"UK renewable energy generation and storage requirement to meet demand (2022)"
    )

    # Initialise a five panel figure.
    gs = GridSpec(4, 2, figure=fig)
    ax1 = fig.add_subplot(gs[:2, 0])
    ax2 = fig.add_subplot(gs[:2, 1])
    ax3 = fig.add_subplot(gs[2:4, 0])
    ax4 = fig.add_subplot(gs[2, 1])
    ax5 = fig.add_subplot(gs[3, 1])

    # number of periods to smooth data by
    periods = 30

    # Top left: Energy demand and supply.

    title = "[A] Energy demand and solar and wind supply (GW)"
    annotate_title(ax1, title)

    # wind
    df["wind_gw"] = df["wind_mw"] / 1000
    df["wind_gw_avg"] = df["wind_gw"].ewm(span=periods).mean()
    ax1.fill_between(
        df.index,
        df["wind_gw"],
        df["wind_gw_avg"],
        linewidth=0.5,
        color="tab:blue",
        alpha=0.25,
    )
    df["wind_gw_avg"].plot(ax=ax1, label="wind", color="tab:blue")

    # solar
    df["solar_gw"] = df["solar_mw"] / 1000
    df["solar_gw_avg"] = df["solar_gw"].ewm(span=periods).mean()
    ax1.fill_between(
        df.index,
        df["solar_gw"],
        df["solar_gw_avg"],
        linewidth=0.5,
        color="tab:orange",
        alpha=0.25,
    )
    df["solar_gw_avg"].plot(ax=ax1, label="solar", color="tab:orange")

    # demand
    df["demand_gw"] = df["demand_mw"] / 1000
    df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    ax1.fill_between(
        df.index,
        df["demand_gw"],
        df["demand_gw_avg"],
        linewidth=0.5,
        color="tab:green",
        alpha=0.25,
    )
    df["demand_gw_avg"].plot(ax=ax1, label="demand", color="tab:green")

    ax1.set(xlabel=None)
    ax1.set(xticklabels=[])
    ax1.legend()

    # Top right: Energy demand and supply.

    title = "[B] Energy demand and actual solar+wind supply (GW)"
    annotate_title(ax2, title)

    # supply
    df["supply_gw"] = df["supply_mw"] / 1000
    df["supply_gw_avg"] = df["supply_gw"].ewm(span=periods).mean()
    ax2.fill_between(
        df.index,
        df["supply_gw"],
        df["supply_gw_avg"],
        linewidth=0.5,
        color="tab:purple",
        alpha=0.25,
    )
    df["supply_gw_avg"].plot(ax=ax2, label="wind+solar", color="tab:purple")

    # demand
    df["demand_gw"] = df["demand_mw"] / 1000
    df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    ax2.fill_between(
        df.index,
        df["demand_gw"],
        df["demand_gw_avg"],
        linewidth=0.5,
        color="tab:green",
        alpha=0.25,
    )
    df["demand_gw_avg"].plot(ax=ax2, label="demand", color="tab:green")

    ax2.set(xlabel=None)
    ax2.set(xticklabels=[])
    ax2.legend(loc="center left")

    # Bottom left: Energy demand and supply.

    title = "[C] Energy demand and solar+wind as 100% of supply (GW)"
    annotate_title(ax3, title)

    # supply
    df["supply_mult_gw"] = df["supply_mult_mw"] / 1000
    df["supply_mult_gw_avg"] = df["supply_mult_gw"].ewm(span=periods).mean()
    ax3.fill_between(
        df.index,
        df["supply_mult_gw"],
        df["supply_mult_gw_avg"],
        linewidth=0.5,
        color="tab:purple",
        alpha=0.25,
    )
    df["supply_mult_gw_avg"].plot(ax=ax3, label="wind+solar", color="tab:purple")

    # demand
    df["demand_gw"] = df["demand_mw"] / 1000
    df["demand_gw_avg"] = df["demand_gw"].ewm(span=periods).mean()
    ax3.fill_between(
        df.index,
        df["demand_gw"],
        df["demand_gw_avg"],
        linewidth=0.5,
        color="tab:green",
        alpha=0.25,
    )
    df["demand_gw_avg"].plot(ax=ax3, label="demand", color="tab:green")

    ax3.set(xlabel=None)
    ax3.legend(loc="lower left")

    # Bottom right (top): Generation balance.

    title = "[E] Supply/demand balance (GW)"
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

    # storage balance
    df["storage_balance_TWh"] = df["storage_balance_GWh"] / 1000
    df["storage_balance_TWh"].plot(ax=ax5, label="storage balance", color="tab:red")
    ax5.fill_between(df.index, df["storage_balance_TWh"], color="tab:red", alpha=0.1)

    ax5.set(xlabel=None)

    annotate_copyright(ax3)
    plt.show()


def annotate_copyright(ax) -> None:
    ax.annotate(
        "© Lyon Energy Futures Ltd. (2022)",
        (0, 0),
        (720, 25),
        xycoords="figure points",
        textcoords="offset pixels",
        va="top",
        color="grey",
    )


def annotate_title(ax: matplotlib.axis, title: str, x=10, y=185, color="black") -> None:
    ax.annotate(
        title,
        (0, 0),
        (x, y),
        color=color,
        xycoords="axes points",
        textcoords="offset pixels",
        fontsize=8,
        fontweight=600,
    )
