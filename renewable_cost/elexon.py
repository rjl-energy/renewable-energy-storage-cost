"""
Functions to get wind and demand data from Elexon.

Elexon returns generation for 30 minute time intervals for a range of fuel types.
https://developer.data.elexon.co.uk/api-details#api=prod-insol-insights-api&operation=get-generation-outturn-summary
"""
from datetime import datetime, timedelta
from typing import List
from urllib import parse

import pandas as pd
import requests
from pydantic import BaseModel, Field
from pprint import pprint
import pytz

from requests import Response


# Represents the API return schema
class Report(BaseModel):
    fuelType: str
    generation: int


class GenerationData(BaseModel):
    # settlementPeriod: int
    startTime: datetime
    data: List[Report]


class DemandData(BaseModel):
    publishTime: datetime
    INDO: float | None = Field(alias="initialDemandOutturn")
    ITSDO: float | None = Field(alias="initialTransmissionSystemDemandOutturn")


def get_response(
    endpoint: str, params: dict, start_time: datetime, end_time: datetime
) -> Response:
    """
    Get the response for the given endpoint and time period
    Args:
        endpint: The URL to get
        start_time: The start date of the period
        end_time: The end date of the period

    Returns:
        The Response object

    """
    url = f"https://data.elexon.co.uk/bmrs/api/v1/{endpoint}"
    headers = {"Cache-Control": "no-cache"}
    pprint(params)
    response = requests.get(url, headers=headers, params=parse.urlencode(params))

    if not response.ok:
        error = f"Failed to get url: {response.json()}"
        pprint(response.json())
        raise error

    return response


def all_fuels(start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Get generation for all fuels for the given time period.
    Args:
        start_time: The start date of the period
        end_time: The end date of the period

    Returns:
        A dataframe ot total daily generation  for each fuel type.
    """

    # get the raw data (generation is in MW)

    params = {
        "startTime": start_time.isoformat(),
        "endTime": end_time.isoformat(),
        "format": "json",
    }
    response = get_response("generation/outturn/summary", params, start_time, end_time)

    # build the raw dataframe

    response_data = [GenerationData(**item) for item in response.json()]
    df = pd.DataFrame(columns=["date", "type", "generation_mw"])
    rows = []
    for period in response_data:
        for data in period.data:
            rows.append(
                {
                    "date": period.startTime,
                    "type": data.fuelType,
                    "generation_mw": data.generation,
                }
            )
    df = df.append(rows)
    df = df.set_index("date")

    # pivot by fuel type

    df = df.pivot(columns="type", values="generation_mw")

    # downsample to daily

    df = df.resample("1D").mean()

    # normalise the time index

    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)

    return df


def wind(start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Get total UK (Scotland, England, and Wales wind generation for the given time period.
    Args:
        start_time: The start date of the period
        end_time: The end date of the period

    Returns:
        A dataframe ot total daily generation.
    """
    fuels_df = all_fuels(start_time, end_time)
    df = fuels_df["WIND"]

    df.columns = ["total"]

    return df


def demand(start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Get Demand Outturn for the given time period

    Provides Initial Demand Outturn (INDO) and Initial Transmission System Demand Outturn (ITSDO)

    https://developer.data.elexon.co.uk/api-details#api=prod-insol-insights-api&operation=get-demand
    Args:
        start_time: The start date of the period
        end_time: The end date of the period

    Returns:
        A dataframe of daily average demand data in MW

    """
    # get the raw data (demand is in MW)

    # page through in 28 day intervals

    df = pd.DataFrame(columns=["date", "INDO_mw", "ITSDO_mw"])
    rows = []

    current_end_time = start_time - timedelta(days=1)

    while current_end_time < end_time:
        current_start_time = current_end_time + timedelta(days=1)
        current_end_time = current_start_time + timedelta(days=27)

        params = {
            "settlementDateFrom": current_start_time.isoformat(),
            "settlementDateTo": current_end_time.isoformat(),
            "format": "json",
        }

        response = get_response("demand", params, start_time, end_time)
        response_data = [DemandData(**item) for item in response.json()["data"]]

        for period in response_data:
            rows.append(
                {
                    "date": period.publishTime,
                    "INDO_mw": period.INDO,
                    "ITSDO_mw": period.ITSDO,
                }
            )

    df = df.append(rows)
    df = df.set_index("date")
    df.index = df.index.tz_localize(None)

    # downsample to daily

    df = df.resample("1D").mean()
    df.to_pickle("data/elexon_demand.pkl")

    return df
