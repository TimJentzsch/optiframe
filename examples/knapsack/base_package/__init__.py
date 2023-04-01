from .build_mip import BuildMip
from .data import KnapsackData
from .extract_solution import ExtractSolution
from .validate import ValidateData
from optiframe.framework import OptimizationPackage


base_package = OptimizationPackage(
    validate=ValidateData, build_mip=BuildMip, extract_solution=ExtractSolution
)

__all__ = ["KnapsackData", "base_package"]
