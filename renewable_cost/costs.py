#
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from elexon import wind, demand
from sheffield import solar


def compute():
    start_time = datetime(2022, 1, 1)
    end_time = datetime(2022, 6, 30)

    # wind_df = wind(start_time, end_time)
    # solar_df = solar(start_time, end_time)
    demand_df = demand(start_time, end_time)

    df = pd.DataFrame(columns=["wind", "solar", "demand"])

    # df["wind"] = wind_df
    # df["solar"] = solar_df["generation_mw"]
    df["demand"] = demand_df["INDO_mw"]
    #
    # print(df.head())

    df.plot()
    plt.show()


if __name__ == "__main__":
    compute()
