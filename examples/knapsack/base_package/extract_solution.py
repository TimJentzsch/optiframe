from dataclasses import dataclass

from pulp import LpProblem

from examples.knapsack.base_package import BaseData
from examples.knapsack.base_package.build_mip import BaseMipData
from optiframe import Task


@dataclass
class SolutionData:
    packed_items: list[str]


class ExtractSolution(Task[SolutionData]):
    data: BaseData
    mip_data: BaseMipData
    problem: LpProblem

    def __init__(self, data: BaseData, mip_data: BaseMipData, problem: LpProblem):
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
