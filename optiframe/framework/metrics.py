"""Automatically added metrics for the optimization process."""
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class ModelSize:
    """The size of the MIP, determined by the number of variables and constraints."""

    variable_count: int
    constraint_count: int

    @property
    def total(self) -> int:
        """The total size of the model, i.e. the variable count times the constraint count."""
        return self.variable_count * self.constraint_count


@dataclass
class StepTimes:
    """The time needed to execute each steps of the optimization."""

    validate: timedelta
    pre_processing: timedelta
    build_mip: timedelta
    solve: timedelta
    extract_solution: timedelta

    @property
    def total(self) -> timedelta:
        """The total time needed to solve the problem.

        This is the sum of all steps times.
        """
        return sum(
            [self.validate, self.pre_processing, self.build_mip, self.solve, self.extract_solution],
            timedelta(),
        )
