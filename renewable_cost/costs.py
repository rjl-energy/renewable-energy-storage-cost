from dataclasses import dataclass

import pandas as pd


@dataclass
class LCOEParams:
    """Class for passing LCOE configuration parameters."""

    periods: int
    discount_rate: float
    capital_cost: int
    capacity_factor: float
    fixed_OM_cost: int


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


def lcoe(param: LCOEParams) -> float:
    """
    Compute the levelised cost of energy for the given parameters.

    Args:
        params: The parameters object

    Returns:
        Levelised cost of energy (£/MWh)
    """
    intermediate = pow(1.0 + param.discount_rate, param.periods)
    crf = param.discount_rate * intermediate / (intermediate - 1)

    return (
        1000
        * (param.capital_cost * crf + param.fixed_OM_cost)
        / (8760 * param.capacity_factor)
    )


def compute_costs(df: pd.DataFrame, lcoe_params: LCOEParams, capex: Capex) -> Costs:
    """
    Compute generation and storage costs.

    Args:
        df: Data to compute costs for
        params: Levelised cost of electricity parameters

    Returns:
        An object with the costs

    """

    cost = lcoe(lcoe_params)

    pass
