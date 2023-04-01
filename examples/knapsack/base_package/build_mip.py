from dataclasses import dataclass

from pulp import LpVariable, lpSum, LpProblem, LpAffineExpression, LpBinary

from examples.knapsack.base_package.data import KnapsackData
from optiframe import Task


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