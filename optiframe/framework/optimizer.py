from __future__ import annotations

import tempfile
from dataclasses import dataclass
from typing import Optional, Self, Type, Any

from pulp import LpProblem, LpMinimize, LpMaximize

from optiframe.workflow_engine import Step, StepData
from optiframe.workflow_engine.task import Task
from optiframe.workflow_engine.workflow import Workflow, InitializedWorkflow

from .tasks import (
    CreateProblemTask,
    SolveTask,
    SolveSettings,
    ExtractSolutionObjValueTask,
    ProblemSettings,
)


@dataclass
class OptimizationPackage:
    build_mip: Type[Task[Any]]
    validate: Optional[Type[Task[None]]] = None
    pre_processing: Optional[Type[Task[Any]]] = None
    extract_solution: Optional[Type[Task[Any]]] = None


class Optimizer:
    name: str
    sense: LpMinimize | LpMaximize
    packages: list[OptimizationPackage]

    def __init__(self, name: str, sense: LpMinimize | LpMaximize):
        """
        Create a new optimizer.

        :param name: The name of the optimization problem.
        :param sense: Whether to minimize or maximize the objective.
        Defaults to minimize.
        """
        self.name = name
        self.sense = sense
        self.packages = []

    def add_package(self, package: OptimizationPackage) -> Self:
        self.packages.append(package)
        return self

    def initialize(self, *data: Any) -> InitializedOptimizer:
        validate_step = Step("validate")
        pre_processing_step = Step("pre_processing")
        build_mip_step = Step("build_mip").add_task(CreateProblemTask)
        solve_step = Step("solve").add_task(SolveTask)
        extract_solution_step = Step("extract_solution").add_task(ExtractSolutionObjValueTask)

        for package in self.packages:
            if package.validate is not None:
                validate_step.add_task(package.validate)

            if package.pre_processing is not None:
                pre_processing_step.add_task(package.pre_processing)

            build_mip_step.add_task(package.build_mip)

            if package.extract_solution is not None:
                extract_solution_step.add_task(package.extract_solution)

        workflow = (
            Workflow()
            .add_step(validate_step)
            .add_step(pre_processing_step)
            .add_step(build_mip_step)
            .add_step(solve_step)
            .add_step(extract_solution_step)
            .initialize(*data)
            .add_data(ProblemSettings(name=self.name, sense=self.sense))
        )
        return InitializedOptimizer(workflow)


class InitializedOptimizer:
    workflow: InitializedWorkflow

    def __init__(self, workflow: InitializedWorkflow):
        self.workflow = workflow

    def validate(self) -> ValidatedOptimizer:
        self.workflow.execute_step(0)
        return ValidatedOptimizer(self.workflow)


class ValidatedOptimizer:
    workflow: InitializedWorkflow

    def __init__(self, workflow: InitializedWorkflow):
        self.workflow = workflow

    def pre_processing(self) -> PreProcessedOptimizer:
        self.workflow.execute_step(1)
        return PreProcessedOptimizer(self.workflow)


class PreProcessedOptimizer:
    workflow: InitializedWorkflow

    def __init__(self, workflow: InitializedWorkflow):
        self.workflow = workflow

    def build_mip(self) -> BuiltOptimizer:
        self.workflow.execute_step(2)
        return BuiltOptimizer(self.workflow)


class BuiltOptimizer:
    workflow: InitializedWorkflow

    def __init__(self, workflow: InitializedWorkflow):
        self.workflow = workflow

    def problem(self) -> LpProblem:
        return self.workflow.step_data[LpProblem]

    def get_lp_string(self, line_limit: int = 100) -> str:
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".lp") as file:
            self.problem().writeLP(filename=file.name)
            return "".join(file.readlines()[:line_limit])

    def solve(
        self,
        solver: Optional[Any] = None,
    ) -> StepData:
        self.workflow.add_data(SolveSettings(solver))
        self.workflow.execute_step(3)
        return self.workflow.execute_step(4)

    def print_mip_and_solve(self, solver: Optional[Any] = None) -> StepData:
        """Print the description of the MIP and solve it."""
        print(self.get_lp_string())
        return self.solve(solver)
