"""Complete workflows, composed of steps which are composed of tasks."""
from __future__ import annotations

from typing import Any, Self

from .step import Step, StepData


class Workflow:
    """A complete workflow.

    The workflow is composed of steps, which are executed sequentially.
    Each steps is composed of tasks, which can depend on each other.
    """

    steps: list[Step]

    def __init__(self) -> None:
        self.steps = list()

    def add_steps(self, *steps: Step) -> Self:
        """Add steps to the workflow.

        The order in which the steps are added determines the order in which they are executed.
        """
        for step in steps:
            self.steps.append(step)

        return self

    def initialize(self, *args: Any) -> InitializedWorkflow:
        """Initialize the workflow with data.

        The data that needs to be added here is the data required by the tasks
        that is not generated by any other tasks.
        """
        step_data = {type(data): data for data in args if data is not None}

        return InitializedWorkflow(self, step_data)


class InitializedWorkflow:
    """A workflow initialized with data."""

    workflow: Workflow
    step_data: StepData

    def __init__(self, workflow: Workflow, step_data: StepData):
        self.workflow = workflow
        self.step_data = step_data

    def add_data(self, data: Any) -> Self:
        """Add additional data to the model.

        This can be used to add dependencies needed by tasks that can not
        be provided by other tasks, but is also not available at initialization.
        """
        data_type = type(data)
        self.step_data[data_type] = data
        return self

    def execute_step(self, index: int) -> StepData:
        """Execute the steps at the given index.

        The indexes start at 0, so 0 is the first steps.
        """
        step = self.workflow.steps[index]
        self.step_data = step.initialize(self.step_data).execute()
        return self.step_data

    def execute(self) -> StepData:
        """Execute all steps sequentially."""
        for step in self.workflow.steps:
            # Execute each steps sequentially and update the steps data
            self.step_data = step.initialize(self.step_data).execute()

        return self.step_data
