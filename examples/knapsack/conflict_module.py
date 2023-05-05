"""A modules that allows you to add conflicting items which must not be packed together."""

from dataclasses import dataclass

from pulp import LpProblem

from examples.knapsack.base_module import BaseData, BaseMipData
from optiframe.framework import OptimizationModule
from optiframe.framework.tasks import MipConstructionTask, ValidationTask


@dataclass
class ConflictData:
    """The data required for the conflict modules."""

    # A list of item pairs which must not be packed together
    conflicts: list[tuple[str, str]]


class ValidationConflictData(ValidationTask):
    """A task to validation that the data of the conflict modules is valid."""

    base_data: BaseData
    conflict_data: ConflictData

    def __init__(self, base_data: BaseData, conflict_data: ConflictData):
        self.base_data = base_data
        self.conflict_data = conflict_data

    def execute(self) -> None:
        """Validate the data of the conflict modules."""
        for item_1, item_2 in self.conflict_data.conflicts:
            assert (
                item_1 in self.base_data.items
            ), f"Item {item_1} is not defined in the base base_data"
            assert (
                item_2 in self.base_data.items
            ), f"Item {item_2} is not defined in the base base_data"
            assert item_1 != item_2, f"Item {item_1} is conflicting with itself"


class ConflictMipConstruction(MipConstructionTask[None]):
    """A task to add the variables and constraints of the conflict modules to the MIP."""

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
        """Add the variables and constraints of the conflict modules to the MIP."""
        var_pack_item = self.base_mip_data.var_pack_item

        # Prevent the conflicting items from being packed together
        for item_1, item_2 in self.conflict_data.conflicts:
            self.problem += var_pack_item[item_1] + var_pack_item[item_2] <= 1


conflict_module = OptimizationModule(validation=ValidationConflictData, mip_construction=ConflictMipConstruction)
