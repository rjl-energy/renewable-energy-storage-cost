"""
Functions to get solar data from Sheffield University PV API.

see: https://api0.solar.sheffield.ac.uk/pvlive/docs
"""

from datetime import datetime
from typing import List, Dict

import pandas as pd
import requests
from pydantic import BaseModel


# Represents the API return schema
class GenerationData(BaseModel):
    gsp_id: int
    datetime_gmt: datetime
    generation_mw: float | None
    capacity_mwp: float
    installedcapacity_mwp: float


def dict_from_list(data: List) -> Dict:
    """
    Map a list of data values to a dictionary using defined keys.
    NOTE: The list of keys must match the field names in the API return schema `GenerationData`

    Args:
        data: A list of data values in known order

    Returns:
        A dictionary of data values with specified keys.

    """
    if not len(data) == 5:
        raise f"Wrong number of parameters in response. Expected 5, got {len(data)}"

    res = dict()
    keys = [
        "gsp_id",
        "datetime_gmt",
        "generation_mw",
        "capacity_mwp",
        "installedcapacity_mwp",
    ]

    for key, value in zip(keys, data):
        res[key] = value
    return res


def solar(start_time: datetime, end_time: datetime, from_disk=True) -> pd.DataFrame:
    """
    Get solar generation for the given time period.

    Args:
        start_time: The start date of the period
        end_time: The end date of the period
        from_disk: Read from pickle file

    Returns:
        A dataframe of total solar daily generation.
    """
    if from_disk:
        df = pd.read_pickle("data/sheffield_solar_half_hourly.pkl")
        return df

    # Get the raw data

    url = "https://api0.solar.sheffield.ac.uk//pvlive/api/v4/gsp/0"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }
    extra_fields = ["capacity_mwp", "installedcapacity_mwp"]
    params = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "extra_fields": ",".join(extra_fields),
    }
    response = requests.get(url, headers=headers, params=params)

    if not response.ok:
        raise f"Failed to get url: {url}"

    # build the raw dataframe

    raw_data = response.json()["data"]
    response_data = [GenerationData(**dict_from_list(item)) for item in raw_data]

    df = pd.DataFrame(columns=["gsp_id", "datetime_gmt", "generation_mw"])
    rows = []
    for period in response_data:
        rows.append(
            {
                "gsp_id": period.gsp_id,
                "datetime_gmt": period.datetime_gmt,
                "generation_mw": period.generation_mw,
                "capacity_mwp": period.capacity_mwp,
                "installedcapacity_mwp": period.installedcapacity_mwp,
            }
        )
    df = df.append(rows)
    df = df.set_index("datetime_gmt")

    # normalise the time index

    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)

    df.to_pickle("data/sheffield_solar_half_hourly.pkl")

    return df
