"""A task in the workflow which executes a specific action."""
import abc
from typing import Generic, TypeVar

T = TypeVar("T")


class Task(abc.ABC, Generic[T]):
    """A task in the workflow which executes a specific action.

    The task can generate data and return it from the `execute` function.
    This data will be made available to the other tasks of the workflow.

    The task can also depend on data by other tasks by specifying dependencies in the constructor.
    The type annotation of the constructor parameters determine which dependency will be injected.
    If the data is generated by a task in the same steps, the task will be executed before this one.
    """

    @abc.abstractmethod
    def execute(self) -> T:
        """Execute the action of this task.

        This method is called once all the dependencies of the task have been gathered.
        It can access the data of the dependencies through the `self` parameter.

        The data that is returned from this method can be used by other tasks.
        """
        pass
