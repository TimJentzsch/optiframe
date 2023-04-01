from dataclasses import dataclass


@dataclass
class BaseData:
    """
    The base_data needed to describe an instance of the knapsack problem.
    """

    # The available items
    items: list[str]

    # The profit / value of each item
    # We want to achieve the maximum profit with the selected items
    profits: dict[str, float]

    # The weights of each item
    # The maximum weight of the knapsack has to be respected
    weights: dict[str, float]

    # The maximum weight of the knapsack
    max_weight: float
