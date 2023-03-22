from dataclasses import dataclass
from typing import Any, Optional

from pulp import LpProblem, LpMinimize, LpAffineExpression, LpStatus, LpMaximize

from optiframe.framework.errors import InfeasibleError
from optiframe.workflow_engine import Task


@dataclass
class ProblemSettings:
    name: str
    sense: LpMinimize | LpMaximize


class CreateProblemTask(Task[LpProblem]):
    problem_settings: ProblemSettings

    def __init__(self, problem_settings: ProblemSettings):
        self.problem_settings = problem_settings

    def execute(self) -> LpProblem:
        return LpProblem(self.problem_settings.name, self.problem_settings.sense)


class CreateObjectiveTask(Task[LpAffineExpression]):
    def __init__(self) -> None:
        pass

    def execute(self) -> LpAffineExpression:
        return LpAffineExpression()


@dataclass
class SolveSettings:
    # The PuLP solver object to use for the optimization
    solver: Optional[Any]


class SolveTask(Task[None]):
    problem: LpProblem
    objective: LpAffineExpression
    solve_settings: SolveSettings

    def __init__(
        self,
        problem: LpProblem,
        objective: LpAffineExpression,
        solve_settings: SolveSettings,
    ):
        self.problem = problem
        self.objective = objective
        self.solve_settings = solve_settings

    def execute(self) -> None:
        # Add objective to MIP
        self.problem.setObjective(self.objective)

        # Solve the problem
        status_code = self.problem.solve(solver=self.solve_settings.solver)
        status = LpStatus[status_code]

        if status != "Optimal":
            raise InfeasibleError()


@dataclass
class SolutionObjValue:
    """The objective value of the solution."""

    objective_value: float


class ExtractSolutionObjValueTask(Task[SolutionObjValue]):
    problem: LpProblem

    def __init__(self, problem: LpProblem):
        self.problem = problem

    def execute(self) -> SolutionObjValue:
        cost = self.problem.objective.value()

        return SolutionObjValue(cost)
