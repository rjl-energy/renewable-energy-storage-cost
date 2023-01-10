from dataclasses import dataclass

import pandas as pd


@dataclass
class LCOEParams:
    """Class for passing LCOE configuration parameters."""

    periods_years: int  #
    discount_rate: float

    # total capital cost of the plant per installed kw of generating capacity
    capital_cost_kw: int

    # percent of time plant is producing power
    capacity_factor: float

    # fixed cost for operating and maintaining the plant
    fixed_OM_cost_kw_yr: int


def compute_lcoe(param: LCOEParams) -> float:
    """
    Compute the levelised cost per MWh of energy for the given parameters.

    LCOE represents the average revenue per unit of electricity generated that would be required to recover the costs
    of building and operating a generating plant during an assumed financial life and duty cycle.
    See: https://www.nrel.gov/analysis/tech-lcoe.html, https://en.wikipedia.org/wiki/Levelized_cost_of_electricity

    Args:
        params: The parameters object

    Returns:
        Levelised cost of energy (£/MWh)
    """
    intermediate = pow(1.0 + param.discount_rate, param.periods_years)
    crf = param.discount_rate * intermediate / (intermediate - 1)
    life_time_cost = param.capital_cost_kw * crf + param.fixed_OM_cost_kw_yr
    life_time_energy = 24 * 365 * param.capacity_factor

    return 1000 * life_time_cost / life_time_energy


@dataclass
class CostData:
    """Class for returning cost info."""

    # wind generation required to meet demand
    wind_mw: float = None

    # solar generation required to meet demand
    solar_mw: float = None

    # levelised cost of energy
    lcoe_wind_mwh: float = None
    lcoe_solar_mwh: float = None

    # cost of wind to meet demand
    wind_cost: float = None

    # cost of solar to meet demand
    solar_cost: float = None

    # cost of batteries to support demand
    storage_cost: float = None

    # maximum storage capacity
    max_storage_gwh: float = None


def compute_costs(
        df: pd.DataFrame,
        lcoe_params_wind: LCOEParams,
        lcoe_params_solar: LCOEParams,
        battery_cost_kwh: float,
) -> CostData:
    """
    Compute generation and storage costs for a given energy scenario.

    Args:
        df: Energy to compute costs for
        lcoe_params: Levelised cost of electricity parameters

    Returns:
        An object with generation and storage costs

    """

    print(df.columns)

    cost_data = CostData()

    # compute wind/solar fractions
    wind_frac = df.wind_mw.mean() / df.supply_mw.mean()
    solar_frac = df.solar_mw.mean() / df.supply_mw.mean()

    # compute generation capacity for each source
    wind_mw = df.demand_mw.mean() * wind_frac
    solar_mw = df.demand_mw.mean() * solar_frac

    # compute levelised cost for each source
    lcoe_wind_mwh = compute_lcoe(lcoe_params_wind)
    lcoe_solar_mwh = compute_lcoe(lcoe_params_solar)

    # compute wind and solar generation cost
    wind_cost = wind_mw * 1000 * lcoe_params_wind.capital_cost_kw
    solar_cost = solar_mw * 1000 * lcoe_params_solar.capital_cost_kw

    # compute storage cost
    max_storage_gwh = df.storage_balance_GWh.max()
    storage_cost = max_storage_gwh * 1000 * 1000 * battery_cost_kwh

    cost_data.wind_mw = wind_mw
    cost_data.solar_mw = solar_mw
    cost_data.lcoe_wind_mwh = round(lcoe_wind_mwh, 0)
    cost_data.lcoe_solar_mwh = round(lcoe_solar_mwh, 0)
    cost_data.wind_cost = wind_cost
    cost_data.solar_cost = solar_cost
    cost_data.storage_cost = storage_cost
    cost_data.max_storage_gwh = max_storage_gwh

    return cost_data
