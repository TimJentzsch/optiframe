from pulp import LpMaximize
from pytest import approx

from examples.knapsack.base_package import BaseData, base_package
from examples.knapsack.base_package import SolutionData
from optiframe import SolutionObjValue, Optimizer


base_optimizer = Optimizer("knapsack_base", sense=LpMaximize).add_package(base_package)


def test_one_fitting_item() -> None:
    """There is only one item, which fits into the knapsack."""
    solution = (
        base_optimizer.initialize(
            BaseData(
                items=["apple"], profits={"apple": 1.0}, weights={"apple": 1.0}, max_weight=1.0
            )
        )
        .validate()
        .build_mip()
        .print_mip_and_solve()
    )

    assert solution[SolutionObjValue].objective_value == approx(1.0)
    assert solution[SolutionData].packed_items == ["apple"]


def test_two_items_one_fits() -> None:
    """There is only one item, which fits into the knapsack."""
    solution = (
        base_optimizer.initialize(
            BaseData(
                items=["apple", "banana"],
                profits={"apple": 1.0, "banana": 2.0},
                weights={"apple": 1.0, "banana": 1.0},
                max_weight=1.0,
            )
        )
        .validate()
        .build_mip()
        .print_mip_and_solve()
    )

    assert solution[SolutionObjValue].objective_value == approx(2.0)
    assert solution[SolutionData].packed_items == ["banana"]
