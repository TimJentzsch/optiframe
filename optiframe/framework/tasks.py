from dataclasses import dataclass
from typing import Any, Optional

from pulp import LpProblem, LpMinimize, LpAffineExpression, LpStatus

from optiframe.framework.errors import SolveError, SolveErrorReason
from optiframe.workflow_engine import Task


class CreateProblemTask(Task[LpProblem]):
    def __init__(self):
        pass

    def execute(self) -> LpProblem:
        # TODO: Add way to change name and min/max target
        return LpProblem("optimization_problem", LpMinimize)


class CreateObjectiveTask(Task[LpAffineExpression]):
    def __init__(self):
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
            raise SolveError(SolveErrorReason.INFEASIBLE)


@dataclass
class SolutionCost:
    """The total cost of the solution."""

    cost: float


class ExtractSolutionCostTask(Task[SolutionCost]):
    problem: LpProblem

    def __init__(self, problem: LpProblem):
        self.problem = problem

    def execute(self) -> SolutionCost:
        cost = self.problem.objective.value()

        return SolutionCost(cost)
