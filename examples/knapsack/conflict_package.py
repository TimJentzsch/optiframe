from dataclasses import dataclass

from pulp import LpProblem

from examples.knapsack.base_package import BaseMipData
from optiframe import Task
from optiframe.framework import OptimizationPackage
from examples.knapsack.base_package import BaseData


@dataclass
class ConflictData:
    # A list of item pairs which must not be packed together
    conflicts: list[tuple[str, str]]


class ValidateConflictData(Task[None]):
    """A task to validate that the knapsack base_data is valid."""

    base_data: BaseData
    conflict_data: ConflictData

    def __init__(self, base_data: BaseData, conflict_data: ConflictData):
        self.base_data = base_data
        self.conflict_data = conflict_data

    def execute(self) -> None:
        for item_1, item_2 in self.conflict_data.conflicts:
            assert (
                item_1 in self.base_data.items
            ), f"Item {item_1} is not defined in the base base_data"
            assert (
                item_2 in self.base_data.items
            ), f"Item {item_2} is not defined in the base base_data"
            assert item_1 != item_2, f"Item {item_1} is conflicting with itself"


class BuildConflictMip(Task[None]):
    base_data: BaseData
    base_mip_data: BaseMipData

    conflict_data: ConflictData

    problem: LpProblem

    def __init__(
        self,
        base_data: BaseData,
        base_mip_data: BaseMipData,
        conflict_data: ConflictData,
        problem: LpProblem,
    ):
        self.base_data = base_data
        self.base_mip_data = base_mip_data
        self.conflict_data = conflict_data
        self.problem = problem

    def execute(self) -> None:
        var_pack_item = self.base_mip_data.var_pack_item

        # Prevent the conflicting items from being packed together
        for item_1, item_2 in self.conflict_data.conflicts:
            self.problem += var_pack_item[item_1] + var_pack_item[item_2] <= 1


conflict_package = OptimizationPackage(validate=ValidateConflictData, build_mip=BuildConflictMip)
