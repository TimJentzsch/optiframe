"""
An example showcasing the implementation of the knapsack problem with optiframe.

For the knapsack problem, the task is to fill a knapsack with a given set of items.
Each item may be included in the knapsack or not.
The goal is to maximize the profits of the packed items, while respecting the maximum
capacity of the knapsack.
"""
from pulp import LpMaximize

from .base_package import BaseData, SolutionData, base_package
from optiframe import Optimizer, SolutionObjValue, InfeasibleError
from .conflict_package import conflict_package, ConflictData


def demo() -> None:
    """
    Solve a small instance of the knapsack problem.

    Can be executed via `poetry run knapsack`.
    """
    item_count = 20

    # Generate a problem instance with 20 items
    base_data = BaseData(
        items=[f"item_{i}" for i in range(item_count)],
        weights={f"item_{i}": i * 20 % 43 for i in range(item_count)},
        profits={f"item_{i}": i + 1 for i in range(item_count)},
        max_weight=49,
    )

    # Disallow some items from being packed together
    conflict_data = ConflictData(
        conflicts=[(f"item_{i}", f"item_{i + item_count // 2}") for i in range(item_count // 2)]
    )

    # Create an optimizer object with both packages
    knapsack_optimizer = (
        Optimizer("knapsack", sense=LpMaximize)
        .add_package(base_package)
        .add_package(conflict_package)
    )

    # Try to solve the problem
    try:
        solution = knapsack_optimizer.initialize(base_data, conflict_data).solve()
    except InfeasibleError:
        print("Failed to find a solution!")
        exit(1)
        return

    total_profit = solution[SolutionObjValue].objective_value
    packed_items = solution[SolutionData].packed_items

    print("Found a solution!")
    print(f"Pack the following items: {packed_items}")
    print(f"Total profit: {total_profit}")
