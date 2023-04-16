"""The error classes for the optimization framework."""


class InfeasibleError(RuntimeError):
    """The optimization problem does not have a solution."""

    def __init__(self) -> None:
        super().__init__("The optimization problem does not have a solution")
