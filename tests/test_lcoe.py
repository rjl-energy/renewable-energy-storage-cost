from renewable_cost.costs import LCOEParams, lcoe
from pytest import approx


def test_lcoe():
    params = LCOEParams(
        periods=20,
        discount_rate=0.03,
        capital_cost=1250,
        capacity_factor=0.25,
        fixed_OM_cost=25
    )

    cost = lcoe(params)
    assert cost == approx(49.7, abs=0.1)
