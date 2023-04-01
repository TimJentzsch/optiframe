from examples.knapsack.base_package.data import BaseData
from optiframe import Task


class ValidateBaseData(Task[None]):
    """A task to validate that the knapsack base_data is valid."""

    data: BaseData

    def __init__(self, data: BaseData):
        self.data = data

    def execute(self) -> None:
        for item in self.data.items:
            assert item in self.data.profits.keys(), f"No profit defined for item {item}"
            assert self.data.profits[item] >= 0, f"The profit for item {item} must be positive"

            assert item in self.data.weights.keys(), f"No weight defined for item {item}"
            assert self.data.weights[item] >= 0, f"The weight for item {item} must be positive"

            assert self.data.max_weight >= 0, "The maximum weight must be positive"
