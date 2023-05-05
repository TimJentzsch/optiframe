"""Tests for the task of the workflow engine."""
import abc
import inspect
from typing import Any, TypeVar

from optiframe import Task


class TestGetReturnType:
    """Tests for the determine_return_type function."""

    def test_execute_type_default(self) -> None:
        """The type of the execute method is fully specified."""

        class TestTask(Task[int]):
            """A test task."""

            def execute(self) -> int:
                """Execute some arbitrary code."""
                return 2

        actual = TestTask.get_return_type()
        assert actual == int

    def test_custom_return_type(self) -> None:
        """The type of the execute method is indirectly specified.

        The generic parameter is defined, but the actual return type not repeated.
        """
        T = TypeVar("T")

        class TestParentTask(Task[T], abc.ABC):
            """An abstract class inheriting from task."""

            def execute(self) -> T:
                """Execute the test function."""
                return self.foo()

            @classmethod
            def get_return_type(cls) -> Any:
                """Test overwriting the return type."""
                return inspect.signature(cls.foo).return_annotation

            @abc.abstractmethod
            def foo(self) -> T:
                """Test function that is called during execution."""
                pass

        class TestTask(TestParentTask[int]):
            def foo(self) -> int:
                return 2

        actual = TestTask.get_return_type()
        assert actual == int
