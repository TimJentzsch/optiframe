from .build_mip import BuildBaseMip
from .data import BaseData
from .extract_solution import ExtractSolution
from .validate import ValidateBaseData
from optiframe.framework import OptimizationPackage


base_package = OptimizationPackage(
    validate=ValidateBaseData, build_mip=BuildBaseMip, extract_solution=ExtractSolution
)

__all__ = ["BaseData", "base_package"]
