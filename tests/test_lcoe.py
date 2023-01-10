import pytest

from renewable_cost.costdata import LCOEParams, compute_lcoe
from pytest import approx

params1 = LCOEParams(
    periods_years=20,
    discount_rate=0.03,
    capital_cost_kw=1250,
    capacity_factor=0.25,
    fixed_OM_cost_kw_yr=25,
)

params2 = LCOEParams(
    periods_years=20,
    discount_rate=0.03,
    capital_cost_kw=2000,
    capacity_factor=0.5,
    fixed_OM_cost_kw_yr=25,
)

params3 = LCOEParams(
    periods_years=10,
    discount_rate=0.05,
    capital_cost_kw=2000,
    capacity_factor=0.25,
    fixed_OM_cost_kw_yr=25,
)


@pytest.mark.parametrize(
    "params, expected", [(params1, 50), (params2, 36), (params3, 130)]
)
def test_compute_lcoe(params, expected):
    cost = compute_lcoe(params)
    assert cost == approx(expected, abs=1)
