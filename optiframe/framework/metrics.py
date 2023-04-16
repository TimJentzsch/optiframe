from dataclasses import dataclass
from datetime import timedelta


@dataclass
class ModelSize:
    """
    The size of the mixed integer program, determined by the number of variables and constraints.
    """

    variable_count: int
    constraint_count: int


@dataclass
class StepTimes:
    """
    The time needed to execute each step of the optimization.
    """

    validate: timedelta
    pre_processing: timedelta
    build_mip: timedelta
    solve: timedelta
    extract_solution: timedelta
