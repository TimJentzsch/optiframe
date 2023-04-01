from pytest import approx

from examples.knapsack import knapsack_optimizer
from examples.knapsack.base_package import KnapsackData
from examples.knapsack.base_package.extract_solution import SolutionData
from optiframe import SolutionObjValue


def test_one_fitting_item() -> None:
    """There is only one item, which fits into the knapsack."""
    solution = (
        knapsack_optimizer.initialize(
            KnapsackData(
                items=["apple"], profits={"apple": 1.0}, weights={"apple": 1.0}, max_weight=1.0
            )
        )
        .validate()
        .build_mip()
        .solve()
    )

    assert solution[SolutionObjValue].objective_value == approx(1.0)
    assert solution[SolutionData].packed_items == ["apple"]


def test_two_items_one_fits() -> None:
    """There is only one item, which fits into the knapsack."""
    solution = (
        knapsack_optimizer.initialize(
            KnapsackData(
                items=["apple", "banana"],
                profits={"apple": 1.0, "banana": 2.0},
                weights={"apple": 1.0, "banana": 1.0},
                max_weight=1.0,
            )
        )
        .validate()
        .build_mip()
        .solve()
    )

    assert solution[SolutionObjValue].objective_value == approx(2.0)
    assert solution[SolutionData].packed_items == ["banana"]
