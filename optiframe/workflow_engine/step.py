from __future__ import annotations

import inspect
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Self, Type, Any

from .task import Task


logger = logging.getLogger(__name__)


class InjectionError(RuntimeError):
    pass


class ScheduleError(RuntimeError):
    pass


@dataclass
class TaskDependency:
    param: str
    annotation: Any

    def __repr__(self):
        return f"{self.param}: {self.annotation.__name__}"

    def __str__(self):
        return f"{self.param}: {self.annotation.__name__}"


# Data which can be injected into an task.
# The keys should be class objects which define the type of the data.
StepData = dict[Any, Any]


class Step:
    """
    One step in the workflow process.

    Each step is composed of multiple tasks which will be executed within this step.
    Multiple steps are executed sequentially.
    """

    name: str
    tasks: list[Type[Task]]

    def __init__(self, name: str):
        self.name = name
        self.tasks = []

    def add_task(self, task: Type[Task]) -> Self:
        """
        Register a task to run in this step.

        :param task: The task to register.
        :return: The same step, to use for function chaining.
        """
        self.tasks.append(task)
        return self

    def initialize(self, step_data: StepData) -> InitializedStep:
        return InitializedStep(self, step_data)


class InitializedStep:
    step: Step
    step_data: StepData

    def __init__(self, step: Step, step_data: StepData):
        self.step = step
        self.step_data = step_data

    def name(self) -> str:
        return self.step.name

    def tasks(self) -> list[Type[Task]]:
        return self.step.tasks

    def execute(self) -> StepData:
        """
        Execute the step by executing the action of all tasks within it.

        The dependencies of each task are injected automatically.

        :raises InjectionError: If the `__init__` or `action` methods are missing type annotations.
        This is necessary to inject the dependencies automatically.
        :raises ScheduleError: If the tasks can't be scheduled,
        e.g. due to circular dependencies.
        :return: The step data, including the one generated during this step.
        """
        start_time = datetime.now()
        logger.info(f"Executing step {self.name()}...")

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
                    data_annotation = inspect.signature(task.execute).return_annotation

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

        logger.info(f"Finished step {self.name()} in {duration.total_seconds():.2f}s.")

        return self.step_data

    def _task_dependencies(self) -> dict[Type[Task], list[TaskDependency]]:
        """
        Determine which task depends on which type of data.

        :return: For each task, a list of its dependencies.
        """
        dependencies: dict[Type[Task], list[TaskDependency]] = dict()

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
