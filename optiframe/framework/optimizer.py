"""The optimizer classes used to configure and execute the optimization process."""
from __future__ import annotations

import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional, Self, Type

from pulp import LpMaximize, LpMinimize, LpProblem

from optiframe.workflow_engine import Step, StepData
from optiframe.workflow_engine.workflow import InitializedWorkflow, Workflow

from .default_tasks import (
    CreateProblemTask,
    ProblemSettings,
    SolutionObjValueExtractionTask,
    SolveSettings,
    SolveTask,
)
from .metrics import ModelSize, StepTimes
from .tasks import MipConstructionTask, PreProcessingTask, SolutionExtractionTask, ValidationTask


@dataclass
class OptimizationModule:
    """A modules bundling tasks for each steps of the optimization process."""

    validation: Optional[Type[ValidationTask]] = None
    pre_processing: Optional[Type[PreProcessingTask[Any]]] = None
    mip_construction: Optional[Type[MipConstructionTask[Any]]] = None
    solution_extraction: Optional[Type[SolutionExtractionTask[Any]]] = None


class Optimizer:
    """An optimizer for an optimization problem.

    Can be configured by adding optimization modules,
    which implement the actual optimization process.
    """

    name: str
    sense: LpMinimize | LpMaximize
    modules: list[OptimizationModule]

    def __init__(self, name: str, sense: LpMinimize | LpMaximize):
        """Create a new optimizer.

        :param name: The name of the optimization problem.
        :param sense: Whether to minimize or maximize the objective.
        Defaults to minimize.
        """
        self.name = name
        self.sense = sense
        self.modules = []

    def add_modules(self, *modules: OptimizationModule) -> Self:
        """Add optimization modules to the optimizer.

        The modules implement the entire functionality,
        without any modules, the optimizer doesn't do anything useful.
        """
        for module in modules:
            self.modules.append(module)

        return self

    def initialize(self, *data: Any) -> InitializedOptimizer:
        """Initialize the optimizer with the data defining the problem instance.

        Which data classes need to be added here depends on the modules
        that have been added to the optimizer.
        """
        validation_step = Step("validation")
        pre_processing_step = Step("pre_processing")
        mip_construction_step = Step("mip_construction").add_tasks(CreateProblemTask)
        solving_step = Step("solving").add_tasks(SolveTask)
        solution_extraction_step = Step("solution_extraction").add_tasks(
            SolutionObjValueExtractionTask
        )

        for module in self.modules:
            if module.validation is not None:
                validation_step.add_tasks(module.validation)

            if module.pre_processing is not None:
                pre_processing_step.add_tasks(module.pre_processing)

            if module.mip_construction is not None:
                mip_construction_step.add_tasks(module.mip_construction)

            if module.solution_extraction is not None:
                solution_extraction_step.add_tasks(module.solution_extraction)

        workflow = (
            Workflow()
            .add_steps(
                validation_step,
                pre_processing_step,
                mip_construction_step,
                solving_step,
                solution_extraction_step,
            )
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
    """An optimizer where the MIP has been built."""

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
        """Return the `LpProblem` instance defining the MIP."""
        return self.workflow.step_data[LpProblem]

    def get_lp_string(self, line_limit: int = 100) -> str:
        """Get a string representing the LP defined by the MIP.

        :param line_limit: The maximum number of lines to include of the LP.
        """
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", suffix=".lp") as file:
            self.problem().writeLP(filename=file.name)
            return "".join(file.readlines()[:line_limit])

    def solve(
        self,
        solver: Optional[Any] = None,
    ) -> StepData:
        """Solve the optimization problem with the given solver.

        :param solver: A PuLP solver class to use to solve the optimization problem.
        Defaults to the coinOR solver, bundled with PuLP.
        """
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
