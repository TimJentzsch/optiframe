class InfeasibleError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("The optimization problem does not have a solution")
