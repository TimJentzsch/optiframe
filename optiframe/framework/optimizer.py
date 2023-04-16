"""The optimizer classes used to configure and execute the optimization process."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Self, Type, Any

from pulp import LpProblem, LpMinimize, LpMaximize

from optiframe.workflow_engine import Step, StepData
from optiframe.workflow_engine.workflow import Workflow, InitializedWorkflow

from .default_tasks import (
    CreateProblemTask,
    SolveTask,
    SolveSettings,
    ExtractSolutionObjValueTask,
    ProblemSettings,
)
from .metrics import StepTimes, ModelSize
from .tasks import BuildMipTask, ValidateTask, PreProcessingTask, ExtractSolutionTask


@dataclass
class OptimizationPackage:
    """A package bundling tasks for each step of the optimization process."""

    build_mip: Type[BuildMipTask[Any]]
    validate: Optional[Type[ValidateTask]] = None
    pre_processing: Optional[Type[PreProcessingTask[Any]]] = None
    extract_solution: Optional[Type[ExtractSolutionTask[Any]]] = None


class Optimizer:
    """An optimizer for an optimization problem.

    Can be configured by adding optimization packages,
    which implement the actual optimization process.
    """

    name: str
    sense: LpMinimize | LpMaximize
    packages: list[OptimizationPackage]

    def __init__(self, name: str, sense: LpMinimize | LpMaximize):
        """Create a new optimizer.

        :param name: The name of the optimization problem.
        :param sense: Whether to minimize or maximize the objective.
        Defaults to minimize.
        """
        self.name = name
        self.sense = sense
        self.packages = []

    def add_package(self, package: OptimizationPackage) -> Self:
        """Add an optimization package to the optimizer."""
        self.packages.append(package)
        return self

    def initialize(self, *data: Any) -> InitializedOptimizer:
        """Initialize the optimizer with the data defining the problem instance.

        Which data classes need to be added here depends on the packages
        that have been added to the optimizer.
        """
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
    """An optimizer that has been initialized with a concrete problem instance."""

    workflow: InitializedWorkflow

    def __init__(self, workflow: InitializedWorkflow):
        self.workflow = workflow

    def validate(self) -> ValidatedOptimizer:
        """Validate the data provided during the initialization."""
        start = datetime.now()
        self.workflow.execute_step(0)
        validate_time = datetime.now() - start

        return ValidatedOptimizer(self.workflow, validate_time)

    def solve(
        self,
        solver: Optional[Any] = None,
    ) -> StepData:
        """Execute all optimization steps to solve the problem.

        This is a shorthand for
        `.validate().pre_processing().build_mip().solve(solver)`.
        """
        return self.validate().pre_processing().build_mip().solve(solver)

    def print_mip_and_solve(
        self,
        solver: Optional[Any] = None,
    ) -> StepData:
        """Execute all optimization steps to solve the problem and print the created MIP.

        This is a shorthand for
        `.validate().pre_processing().build_mip().print_mip_and_solve(solver)`.
        """
        return self.validate().pre_processing().build_mip().print_mip_and_solve(solver)


class ValidatedOptimizer:
    """An optimizer that has been initialized and validated."""

    workflow: InitializedWorkflow

    validate_time: timedelta

    def __init__(self, workflow: InitializedWorkflow, validate_time: timedelta):
        self.workflow = workflow
        self.validate_time = validate_time

    def pre_processing(self) -> PreProcessedOptimizer:
        """Execute the pre-processing tasks.

        The pre-processing can reduce the size of the MIP which can in turn
        reduce the time needed to obtain the optimal solution.
        """
        start = datetime.now()
        self.workflow.execute_step(1)
        pre_processing_time = datetime.now() - start

        return PreProcessedOptimizer(self.workflow, self.validate_time, pre_processing_time)


class PreProcessedOptimizer:
    """An optimizer that has been initialized, validated and pre-processed."""

    workflow: InitializedWorkflow

    validate_time: timedelta
    pre_processing_time: timedelta

    def __init__(
        self,
        workflow: InitializedWorkflow,
        validate_time: timedelta,
        pre_processing_time: timedelta,
    ):
        self.workflow = workflow
        self.validate_time = validate_time
        self.pre_processing_time = pre_processing_time

    def build_mip(self) -> BuiltOptimizer:
        """Construct the mixed integer program for the problem instance."""
        start = datetime.now()
        self.workflow.execute_step(2)
        build_mip_time = datetime.now() - start

        return BuiltOptimizer(
            self.workflow, self.validate_time, self.pre_processing_time, build_mip_time
        )


class BuiltOptimizer:
    workflow: InitializedWorkflow

    validate_time: timedelta
    pre_processing_time: timedelta
    build_mip_time: timedelta

    def __init__(
        self,
        workflow: InitializedWorkflow,
        validate_time: timedelta,
        pre_processing_time: timedelta,
        build_mip_time: timedelta,
    ):
        self.workflow = workflow
        self.validate_time = validate_time
        self.pre_processing_time = pre_processing_time
        self.build_mip_time = build_mip_time

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

        start = datetime.now()
        # Solve the MIP
        self.workflow.execute_step(3)
        end_solve = datetime.now()
        # Extract the solution
        result = self.workflow.execute_step(4)
        end_extract_solution = datetime.now()

        solve_time = end_solve - start
        extract_solution_time = end_extract_solution - end_solve

        # Add metrics to result
        result[StepTimes] = StepTimes(
            validate=self.validate_time,
            pre_processing=self.pre_processing_time,
            build_mip=self.build_mip_time,
            solve=solve_time,
            extract_solution=extract_solution_time,
        )

        result[ModelSize] = ModelSize(
            variable_count=self.problem().numVariables(),
            constraint_count=self.problem().numConstraints(),
        )

        return result

    def print_mip_and_solve(self, solver: Optional[Any] = None) -> StepData:
        """Print the description of the MIP and solve it."""
        print(self.get_lp_string())
        return self.solve(solver)
