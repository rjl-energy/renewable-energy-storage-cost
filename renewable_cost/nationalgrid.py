"""
Functions to get wind data from the National Grid ESO service.

NOTE: This doesn't appear to have any data prior to 1 April 2022

"""

import datetime
from urllib import parse

import pandas as pd
import requests
from pydantic import BaseModel, Field


# Represents the API return schema
class Record(BaseModel):
    england_wales: float = Field(alias="England/Wales Wind Output")
    scotland: float = Field(alias="Scottish Wind Output")
    total: float = Field(alias="Total")
    date: datetime.date = Field(alias="Sett_Date")
    period: int = Field(alias="Sett_Period")


def wind(start_time: datetime, end_time: datetime) -> pd.DataFrame:
    """
    Get wind generation for the given time period.
    Args:
        start_time: The start date of the period
        end_time: The end date of the period

    Returns:
        A dataframe ot total daily generation.
    """

    # get the raw data

    end_time_str = end_time.isoformat() + ".000Z"
    start_time_str = start_time.isoformat() + ".000Z"

    url = "https://api.nationalgrideso.com/api/3/action/datastore_search_sql"
    sql_query = f'SELECT COUNT(*) OVER () AS _count, * FROM "f732e9bb-b573-46a7-8767-3affbbb29b45" WHERE "Sett_Date" >=\'{start_time_str}\' AND "Sett_Date" < \'{end_time_str}\' ORDER BY "_id" ASC'
    params = {"sql": sql_query}
    response = requests.get(url, params=parse.urlencode(params))
    records = response.json()["result"]["records"]

    # build the raw dataframe

    record_data = [Record(**record) for record in records]
    rows = []
    for record in record_data:
        rows.append(
            {
                "date": record.date,
                "england_wales": record.england_wales,
                "scotland": record.scotland,
                "total": record.total,
                "period": record.period,
            }
        )

    df = pd.DataFrame(columns=["date", "period", "england_wales", "scotland", "total"])
    df = df.append(rows)

    # sum

    df = df.groupby(["date"]).mean().astype(int)

    # normalise the time index

    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)

    return df
