#
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from elexon import wind, demand
from sheffield import solar


def compute():
    pd.set_option('display.max_rows', 500)

    start_time = datetime(2022, 1, 1)
    end_time = datetime(2022, 12, 31)

    wind_df = wind(start_time, end_time, from_disk=True)
    wind_df = wind_df.resample("1D").mean()

    solar_df = solar(start_time, end_time, from_disk=True)
    solar_df = solar_df.resample("1D").mean()

    demand_df = demand(start_time, end_time, from_disk=True)
    demand_df = demand_df.resample("1D").mean()

    df = pd.DataFrame(columns=["wind", "solar", "demand"])

    df["wind"] = wind_df
    df["solar"] = solar_df["generation_mw"]
    df["demand"] = demand_df

    df.plot()
    plt.show()


if __name__ == "__main__":
    compute()
