from dataclasses import dataclass

from pytest import approx
from pulp import LpProblem, LpAffineExpression, LpVariable, LpBinary, lpSum, LpMaximize

from optiframe import Task, Optimizer, SolutionObjValue
from optiframe.framework import OptimizationPackage


@dataclass
class KnapsackData:
    """
    The data needed to describe an instance of the knapsack problem.
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


class ValidateData(Task[None]):
    data: KnapsackData

    def __init__(self, data: KnapsackData):
        self.data = data

    def execute(self) -> None:
        for item in self.data.items:
            assert item in self.data.profits.keys(), f"No profit defined for item {item}"
            assert self.data.profits[item] >= 0, f"The profit for item {item} must be positive"

            assert item in self.data.weights.keys(), f"No weight defined for item {item}"
            assert self.data.weights[item] >= 0, f"The weight for item {item} must be positive"

            assert self.data.max_weight >= 0, "The maximum weight must be positive"


@dataclass
class MipData:
    # Pack the item into the knapsack?
    var_pack_item: dict[str, LpVariable]


class BuildMip(Task[MipData]):
    data: KnapsackData
    problem: LpProblem
    objective: LpAffineExpression

    def __init__(self, data: KnapsackData, problem: LpProblem, objective: LpAffineExpression):
        self.data = data
        self.problem = problem
        self.objective = objective

    def execute(self) -> MipData:
        # Pack the item into the knapsack?
        var_pack_item = {
            item: LpVariable(f"pack_item({item})", cat=LpBinary) for item in self.data.items
        }

        # Respect the knapsack capacity
        self.problem += (
            lpSum(self.data.weights[item] * var_pack_item[item] for item in self.data.items)
            <= self.data.max_weight,
            "respect_capacity",
        )

        # Maximize the profit
        self.objective += lpSum(
            self.data.profits[item] * var_pack_item[item] for item in self.data.items
        )

        return MipData(var_pack_item)


@dataclass
class SolutionData:
    packed_items: list[str]


class ExtractSolution(Task[SolutionData]):
    data: KnapsackData
    mip_data: MipData
    problem: LpProblem

    def __init__(self, data: KnapsackData, mip_data: MipData, problem: LpProblem):
        self.data = data
        self.problem = problem
        self.mip_data = mip_data

    def execute(self) -> SolutionData:
        packed_items = []

        # Determine which items should be included in the knapsack
        for item in self.data.items:
            var = self.mip_data.var_pack_item[item]

            if round(var.value()) == 1:
                packed_items.append(item)

        return SolutionData(packed_items)


OPTIMIZER = Optimizer("test_knapsack", sense=LpMaximize).add_package(
    OptimizationPackage(validate=ValidateData, build_mip=BuildMip, extract_solution=ExtractSolution)
)


def test_one_fitting_item():
    """There is only one item, which fits into the knapsack."""
    solution = (
        OPTIMIZER.initialize(
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


def test_two_items_one_fits():
    """There is only one item, which fits into the knapsack."""
    solution = (
        OPTIMIZER.initialize(
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
