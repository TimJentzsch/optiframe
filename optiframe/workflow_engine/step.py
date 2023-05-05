"""The steps of a workflow.

Steps are executed sequentially in the optimization process.
Each steps can contain multiple tasks, which are ordered based on their dependencies.
"""

from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self, Type, TypeVar

from .errors import InjectionError, ScheduleError
from .task import Task

logger = logging.getLogger(__name__)


@dataclass
class TaskDependency:
    """A dependency required by a task, as defined in the `.__init__` method."""

    param: str
    annotation: Any

    def __repr__(self) -> str:
        """Get the string representation of a task dependency."""
        return f"{self.param}: {self.annotation.__name__}"

    def __str__(self) -> str:
        """Get a human-readable string of a task dependency."""
        return f"{self.param}: {self.annotation.__name__}"


# Data which can be injected into a task.
# The keys should be class objects which define the type of the data.
StepData = dict[Any, Any]


class Step:
    """One steps in the workflow process.

    Each steps is composed of multiple tasks which will be executed within this steps.
    Multiple steps are executed sequentially.
    """

    name: str
    tasks: list[Type[Task[Any]]]

    def __init__(self, name: str):
        self.name = name
        self.tasks = []

    def add_tasks(self, *tasks: Type[Task[Any]]) -> Self:
        """Register a task to run in this step.

        :param tasks: The tasks to register.
        :return: The same steps, to use for function chaining.
        """
        for task in tasks:
            self.tasks.append(task)

        return self

    def initialize(self, step_data: StepData) -> InitializedStep:
        """Initialize a steps with data from previous steps.

        This allows data to be passed between steps and be added from the user.
        """
        return InitializedStep(self, step_data)


class InitializedStep:
    """A steps that has been initialized with data."""

    step: Step
    step_data: StepData

    def __init__(self, step: Step, step_data: StepData):
        self.step = step
        self.step_data = step_data

    def name(self) -> str:
        """Get the name of the steps."""
        return self.step.name

    def tasks(self) -> list[Type[Task[Any]]]:
        """Get the tasks that have to be executed during this steps."""
        return self.step.tasks

    def execute(self) -> StepData:
        """Execute the steps by executing the action of all tasks within it.

        The dependencies of each task are injected automatically.

        :raises InjectionError: If the `__init__` or `action` methods are missing type annotations.
        This is necessary to inject the dependencies automatically.
        :raises ScheduleError: If the tasks can't be scheduled,
        e.g. due to circular dependencies.
        :return: The steps data, including the one generated during this steps.
        """
        start_time = datetime.now()
        logger.info(f"Executing steps {self.name()}...")

        dependencies = self._task_dependencies()

        tasks_to_execute = [ext for ext in self.tasks()]

        while len(tasks_to_execute) > 0:
            has_executed = False

            missing_dependencies = {
                task: [
                    dep for dep in dependencies[task] if dep.annotation not in self.step_data.keys()
                ]
                for task in tasks_to_execute
            }

            for task in tasks_to_execute:
                if len(missing_dependencies[task]) == 0:
                    # Create the data parameters to instantiate the task
                    dep_data = {
                        dep.param: self.step_data[dep.annotation] for dep in dependencies[task]
                    }
                    # Determine what type of data is created by the task
                    data_annotation = task.get_return_type()

                    # Instantiate the task, using the data it requires
                    task_obj = task(**dep_data)

                    # Execute the action of the task and save the returned data
                    data = task_obj.execute()

                    if data is None and data_annotation is not None:
                        raise InjectionError(
                            f"Task {task} returned data, but has not type annotation for it. "
                            "This prevents the data from being accessible to other tasks."
                        )
                    elif data is not None:
                        # Make the data available to other tasks
                        self.step_data[data_annotation] = data

                    has_executed = True
                    tasks_to_execute = [ext2 for ext2 in tasks_to_execute if task != ext2]

            # Protection against infinite loops in case of circular or missing dependencies
            if not has_executed:
                ext_strs = [ext.__name__ for ext in tasks_to_execute]
                missing_deps_strs = "\n".join(
                    f"- {ext.__name__}: {missing_deps}"
                    for ext, missing_deps in missing_dependencies.items()
                )
                raise ScheduleError(
                    "The tasks could not be scheduled, "
                    f"{ext_strs} have unfulfilled dependencies:\n"
                    f"{missing_deps_strs}"
                )

        duration = datetime.now() - start_time

        logger.info(f"Finished steps {self.name()} in {duration.total_seconds():.2f}s.")

        return self.step_data

    def _task_dependencies(self) -> dict[Type[Task[Any]], list[TaskDependency]]:
        """Determine which task depends on which type of data.

        :return: For each task, a list of its dependencies.
        """
        dependencies: dict[Type[Task[Any]], list[TaskDependency]] = dict()

        # Collect the dependencies for each task
        for task in self.tasks():
            init_params = inspect.signature(task.__init__).parameters

            task_dependencies: list[TaskDependency] = []

            for param, signature in init_params.items():
                # We don't need to inject the `self` parameter, skip it
                if param == "self":
                    continue

                annotation = signature.annotation

                if annotation is None:
                    raise InjectionError(
                        f"The __init__ method of task {task} "
                        "needs type annotation on its parameters. "
                        "This is needed to properly inject the dependencies."
                    )

                task_dependencies.append(TaskDependency(param=param, annotation=annotation))

            dependencies[task] = task_dependencies

        return dependencies


X = TypeVar("X")
