"""The base modules for the knapsack problem.

Provides the data and functionality that is needed for all problem variations.
"""

from dataclasses import dataclass

from pulp import LpVariable, LpProblem, LpBinary, lpSum

from optiframe.framework import OptimizationModule
from optiframe.framework.tasks import BuildMipTask, ExtractSolutionTask, ValidateTask


@dataclass
class BaseData:
    """The data needed to describe an instance of the knapsack problem."""

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


class ValidateBaseData(ValidateTask):
    """A task to validate that the knapsack base_data is valid."""

    base_data: BaseData

    def __init__(self, base_data: BaseData):
        self.base_data = base_data

    def execute(self) -> None:
        """Validate the base data of the knapsack problem."""
        for item in self.base_data.items:
            assert item in self.base_data.profits.keys(), f"No profit defined for item {item}"
            assert self.base_data.profits[item] >= 0, f"The profit for item {item} must be positive"

            assert item in self.base_data.weights.keys(), f"No weight defined for item {item}"
            assert self.base_data.weights[item] >= 0, f"The weight for item {item} must be positive"

            assert self.base_data.max_weight >= 0, "The maximum weight must be positive"


@dataclass
class BaseMipData:
    """The variables added by the base modules of the knapsack problem."""

    # Pack the item into the knapsack?
    var_pack_item: dict[str, LpVariable]


class BuildBaseMip(BuildMipTask[BaseMipData]):
    """A task to add the variables and constraints of the base modules to the MIP."""

    base_data: BaseData
    problem: LpProblem

    def __init__(self, base_data: BaseData, problem: LpProblem):
        self.base_data = base_data
        self.problem = problem

    def execute(self) -> BaseMipData:
        """Add the variables and constraints of the base modules to the MIP."""
        # Pack the item into the knapsack?
        var_pack_item = {
            item: LpVariable(f"pack_item({item})", cat=LpBinary) for item in self.base_data.items
        }

        # Respect the knapsack capacity
        self.problem += (
            lpSum(
                self.base_data.weights[item] * var_pack_item[item] for item in self.base_data.items
            )
            <= self.base_data.max_weight,
            "respect_capacity",
        )

        # Maximize the profit
        self.problem.objective += lpSum(
            self.base_data.profits[item] * var_pack_item[item] for item in self.base_data.items
        )

        return BaseMipData(var_pack_item)


@dataclass
class SolutionData:
    """The solution to the knapsack problem."""

    packed_items: list[str]


class ExtractSolution(ExtractSolutionTask[SolutionData]):
    """A task to extract the solution of the knapsack problem from the variable values."""

    base_data: BaseData
    base_mip_data: BaseMipData
    problem: LpProblem

    def __init__(self, base_data: BaseData, base_mip_data: BaseMipData, problem: LpProblem):
        self.base_data = base_data
        self.problem = problem
        self.base_mip_data = base_mip_data

    def execute(self) -> SolutionData:
        """Extract the solution of the knapsack problem from the variable values."""
        packed_items = []

        # Determine which items should be included in the knapsack
        for item in self.base_data.items:
            var = self.base_mip_data.var_pack_item[item]

            if round(var.value()) == 1:
                packed_items.append(item)

        return SolutionData(packed_items)


base_module = OptimizationModule(
    validate=ValidateBaseData, build_mip=BuildBaseMip, extract_solution=ExtractSolution
)
