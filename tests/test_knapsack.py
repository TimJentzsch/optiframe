from pulp import LpMaximize
from pytest import approx

from examples.knapsack.conflict_package import conflict_package, ConflictData
from examples.knapsack.base_package import BaseData, base_package
from examples.knapsack.base_package import SolutionData
from optiframe import SolutionObjValue, Optimizer
from optiframe.framework import ModelSize

base_optimizer = Optimizer("knapsack_base", sense=LpMaximize).add_package(base_package)
conflict_optimizer = (
    Optimizer("knapsack_conflict", sense=LpMaximize)
    .add_package(base_package)
    .add_package(conflict_package)
)


def test_one_fitting_item() -> None:
    """There is only one item, which fits into the knapsack."""
    solution = (
        base_optimizer.initialize(
            BaseData(
                items=["apple"], profits={"apple": 1.0}, weights={"apple": 1.0}, max_weight=1.0
            )
        )
        .validate()
        .pre_processing()
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
        .pre_processing()
        .build_mip()
        .print_mip_and_solve()
    )

    assert solution[SolutionObjValue].objective_value == approx(2.0)
    assert solution[SolutionData].packed_items == ["banana"]


def test_conflict() -> None:
    """
    There are three items.
    The first two fit in the knapsack together and would yield the most profit.
    The third item fills the whole knapsack and is worth less than one and two,
    but more than only one of them.
    The first two items are conflicting, so the solution is to pack the third item.
    """
    solution = (
        conflict_optimizer.initialize(
            BaseData(
                items=["apple", "banana", "kiwi"],
                profits={"apple": 2.0, "banana": 2.0, "kiwi": 3.0},
                weights={"apple": 1.0, "banana": 1.0, "kiwi": 2.0},
                max_weight=2.0,
            ),
            ConflictData(
                conflicts=[("apple", "banana")],
            ),
        )
        .validate()
        .pre_processing()
        .build_mip()
        .print_mip_and_solve()
    )

    assert solution[SolutionObjValue].objective_value == approx(3.0)
    assert solution[SolutionData].packed_items == ["kiwi"]


def test_model_size_base():
    """
    Test that the model size of the base model is correct.

    We expect:
    - Variable count to be equal to the number of items
    - Constraint count to be 1
    """
    solution = (
        base_optimizer.initialize(
            BaseData(
                items=["apple", "banana"],
                profits={"apple": 1.0, "banana": 2.0},
                weights={"apple": 1.0, "banana": 1.5},
                max_weight=2.0,
            )
        )
        .validate()
        .pre_processing()
        .build_mip()
        .print_mip_and_solve()
    )

    assert solution[ModelSize] == ModelSize(variable_count=2, constraint_count=1)


def test_model_size_conflict():
    """
    Test that the model size of the conflict model is correct.

    We expect:
    - Variable count to be equal to the number of items
    - Constraint count to be 1 + number of conflict pairs
    """
    solution = (
        conflict_optimizer.initialize(
            BaseData(
                items=["apple", "banana", "kiwi"],
                profits={"apple": 2.0, "banana": 2.0, "kiwi": 3.0},
                weights={"apple": 1.0, "banana": 1.0, "kiwi": 2.0},
                max_weight=2.0,
            ),
            ConflictData(
                conflicts=[("apple", "banana")],
            ),
        )
        .validate()
        .pre_processing()
        .build_mip()
        .print_mip_and_solve()
    )

    assert solution[ModelSize] == ModelSize(variable_count=3, constraint_count=2)
