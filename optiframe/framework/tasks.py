"""The abstract task types for each optimization steps."""
import abc
import inspect
from typing import Any, Generic, TypeVar

from optiframe.workflow_engine import Task

T = TypeVar("T")


class ValidationTask(Task[None], abc.ABC):
    """A task to validate the data describing the problem instance.

    The `execute` method should raise an `AssertionError` if the data is not valid.
    """

    def execute(self) -> None:
        """Execute the task by validating the data."""
        return self.validate()

    @classmethod
    def get_return_type(cls) -> Any:
        """Get the return type of the task."""
        return inspect.signature(cls.validate).return_annotation

    @abc.abstractmethod
    def validate(self) -> None:
        """Validate the data for the given module.

        This method should use assertions to perform the validation.

        :raises AssertionError: If the data is not valid.
        """
        pass


class PreProcessingTask(Task[T], abc.ABC, Generic[T]):
    """A task to pre-process the data to make the model smaller or more efficient.

    This can reduce the total time needed to solve the problem.
    """

    def execute(self) -> T:
        """Execute the task by pre-processing the data."""
        return self.pre_process()

    @classmethod
    def get_return_type(cls) -> Any:
        """Get the return type of the task."""
        return inspect.signature(cls.pre_process).return_annotation

    @abc.abstractmethod
    def pre_process(self) -> T:
        """Apply pre-processing techniques to the data of the problem instance."""
        pass


class MipConstructionTask(Task[T], abc.ABC, Generic[T]):
    """A task to construct (or modify) the mixed integer program.

    This is the central part of the optimization modules as it modifies the final result.
    """

    def execute(self) -> T:
        """Execute the task by constructing the MIP."""
        return self.construct_mip()

    @classmethod
    def get_return_type(cls) -> Any:
        """Get the return type of the task."""
        return inspect.signature(cls.construct_mip).return_annotation

    @abc.abstractmethod
    def construct_mip(self) -> T:
        """Modify the mixed integer program (MIP) to implement new decision criteria.

        You can add additional variables and constraints to modify the optimization.
        The MIP can be obtained by adding `problem: LpProblem` to the constructor.
        This will inject the MIP into the task.
        You can use the usual features of the `pulp` library to modify the MIP.

        If you add new variables to the MIP, you should return a dataclass
        containing the variables in this method.
        This allows other tasks to use the variables to define additional constraints.
        """
        pass


class SolutionExtractionTask(Task[T], abc.ABC):
    """A task to extract the relevant information from the solution of the MIP.

    In this task, variable values can be selected, discarded or aggregated.
    """

    def execute(self) -> T:
        """Execute the task by extracting the solution."""
        return self.extract_solution()

    @classmethod
    def get_return_type(cls) -> Any:
        """Get the return type of the task."""
        return inspect.signature(cls.extract_solution).return_annotation

    @abc.abstractmethod
    def extract_solution(self) -> T:
        """Extract the relevant parts of the solution.

        Once the MIP has been solved, the values for all variables are available.
        Often, these values should be filtered and interpreted to obtain the part
        relevant for the solution of the problem.

        The solved MIP can be obtained by adding `problem: LpProblem` as parameter
        to the constructor.
        The variable values can then be obtained via the functionality of the `pulp` library.
        """
        pass
