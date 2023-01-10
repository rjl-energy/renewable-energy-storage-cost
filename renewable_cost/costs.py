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
    life_time_energy = 8760 * param.capacity_factor

    return 1000 * life_time_cost / life_time_energy


@dataclass
class Capex:
    """Class for passing capex assumptions."""

    wind_kw: int
    solar_kw: int
    battery_kwh: int


@dataclass
class Costs:
    """Class for returning cost info."""

    generation: float
    storage: float


def compute_costs(df: pd.DataFrame, lcoe_params: LCOEParams, capex: Capex) -> Costs:
    """
    Compute generation and storage costs for a given energy scenario.

    Args:
        df: Energy to compute costs for
        lcoe_params: Levelised cost of electricity parameters

    Returns:
        An object with generation and storage costs

    """

    costs = compute_lcoe(lcoe_params)

    pass
