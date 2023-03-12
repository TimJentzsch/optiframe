class InfeasibleError(RuntimeError):
    def __init__(self):
        super().__init__("The optimization problem does not have a solution")
