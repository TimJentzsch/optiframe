"""The abstract task types for each optimization steps."""
import abc
from typing import TypeVar, Generic

from optiframe import Task

T = TypeVar("T")


class ValidateTask(Task[None], abc.ABC):
    """A task to validate the data describing the problem instance.

    The `execute` method should raise an `AssertionError` if the data is not valid.
    """

    pass


class PreProcessingTask(Task[T], abc.ABC, Generic[T]):
    """A task to pre-process the data to make the model smaller or more efficient.

    This can reduce the the total time needed to solve the problem.
    """

    pass


class BuildMipTask(Task[T], abc.ABC, Generic[T]):
    """A task to construct (or modify) the mixed integer program.

    This is the central part of the optimization modules as it modifies the final result.
    """

    pass


class ExtractSolutionTask(Task[T], abc.ABC):
    """A task to extract the relevant information from the solution of the MIP.

    In this task, variable values can be selected, discarded or aggregated.
    """

    pass
