"""Errors that can occur in the workflow engine."""
from __future__ import annotations


class InjectionError(RuntimeError):
    """The dependencies for a task cannot be injected.

    This is often the case when the constructor of the task
    or its `.execute()` method is missing type annotations.
    """

    pass


class ScheduleError(RuntimeError):
    """The tasks of a steps cannot be scheduled.

    This can be the case if there are circular or missing dependencies.
    """

    pass
