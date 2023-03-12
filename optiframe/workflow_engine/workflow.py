from __future__ import annotations

from typing import Self, Any

from .step import Step, StepData


class Workflow:
    """
    A complete workflow.

    The workflow is composed of steps, which are executed sequentially.
    Each step is composed of tasks, which can depend on each other.
    """

    steps: list[Step]

    def __init__(self):
        self.steps = list()

    def add_step(self, step: Step) -> Self:
        self.steps.append(step)
        return self

    def initialize(self, *args: Any) -> InitializedWorkflow:
        step_data = {type(data): data for data in args if data is not None}

        return InitializedWorkflow(self, step_data)


class InitializedWorkflow:
    workflow: Workflow
    step_data: StepData

    def __init__(self, workflow: Workflow, step_data: StepData):
        self.workflow = workflow
        self.step_data = step_data

    def add_data(self, data: Any) -> Self:
        data_type = type(data)
        self.step_data[data_type] = data
        return self

    def execute_step(self, index: int) -> StepData:
        step = self.workflow.steps[index]
        self.step_data = step.initialize(self.step_data).execute()
        return self.step_data

    def execute(self) -> StepData:
        for step in self.workflow.steps:
            # Execute each step sequentially and update the step data
            self.step_data = step.initialize(self.step_data).execute()

        return self.step_data
