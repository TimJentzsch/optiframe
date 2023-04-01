"""
An example showcasing the implementation of the knapsack problem with optiframe.

For the knapsack problem, the task is to fill a knapsack with a given set of items.
Each item may be included in the knapsack or not.
The goal is to maximize the profits of the packed items, while respecting the maximum
capacity of the knapsack.
"""
from pulp import LpMaximize

from .base_package import base_package, KnapsackData
from optiframe import Optimizer, SolutionObjValue, InfeasibleError

# An optimizer object to solve the knapsack problem
from .base_package.extract_solution import SolutionData

knapsack_optimizer = Optimizer("knapsack", sense=LpMaximize).add_package(base_package)


def demo() -> None:
    """Solve a small instance of the knapsack problem."""
    item_count = 20

    # Generate a problem instance with 20 items
    data = KnapsackData(
        items=[f"item_{i}" for i in range(item_count)],
        weights={f"item_{i}": i * 20 % 43 for i in range(item_count)},
        profits={f"item_{i}": i + 1 for i in range(item_count)},
        max_weight=49,
    )

    # Try to solve the problem
    try:
        solution = knapsack_optimizer.initialize(data).validate().build_mip().solve()
    except InfeasibleError:
        print("Failed to find a solution!")
        exit(1)
        return

    total_profit = solution[SolutionObjValue].objective_value
    packed_items = solution[SolutionData].packed_items

    print("Found a solution!")
    print(f"Pack the following items: {packed_items}")
    print(f"Total profit: {total_profit}")
