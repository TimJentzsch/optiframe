"""The default tasks of the optimization framework.

These tasks are added to the steps automatically when constructing the optimizer.
"""
from dataclasses import dataclass
from typing import Any, Optional

from pulp import LpProblem, LpMinimize, LpAffineExpression, LpStatus, LpMaximize

from optiframe.framework.errors import InfeasibleError
from optiframe.framework.tasks import BuildMipTask, ExtractSolutionTask
from optiframe.workflow_engine import Task


@dataclass
class ProblemSettings:
    """The settings to configure the MIP."""

    name: str
    sense: LpMinimize | LpMaximize


class CreateProblemTask(BuildMipTask[LpProblem]):
    """A task to initialize the MIP object."""

    problem_settings: ProblemSettings

    def __init__(self, problem_settings: ProblemSettings):
        self.problem_settings = problem_settings

    def execute(self) -> LpProblem:
        """Create the `LpProblem` instance to make it available to other tasks."""
        problem = LpProblem(self.problem_settings.name, self.problem_settings.sense)
        # Initialize the objective to an empty expression
        problem.setObjective(LpAffineExpression())
        return problem


@dataclass
class SolveSettings:
    """The settings to configure the solver."""

    # The PuLP solver object to use for the optimization
    solver: Optional[Any]


class SolveTask(Task[None]):
    """The task to execute the solver on the constructed MIP."""

    problem: LpProblem
    objective: LpAffineExpression
    solve_settings: SolveSettings

    def __init__(
        self,
        problem: LpProblem,
        solve_settings: SolveSettings,
    ):
        self.problem = problem
        self.solve_settings = solve_settings

    def execute(self) -> None:
        """Execute the solver on the constructed MIP."""
        # Solve the problem
        status_code = self.problem.solve(solver=self.solve_settings.solver)
        status = LpStatus[status_code]

        if status != "Optimal":
            raise InfeasibleError()


@dataclass
class SolutionObjValue:
    """The objective value of the solution."""

    objective_value: float


class ExtractSolutionObjValueTask(ExtractSolutionTask[SolutionObjValue]):
    """A task to extract the objective value from the solved MIP."""

    problem: LpProblem

    def __init__(self, problem: LpProblem):
        self.problem = problem

    def execute(self) -> SolutionObjValue:
        """Extract the objective value from the solved MIP."""
        cost = self.problem.objective.value()

        return SolutionObjValue(cost)
