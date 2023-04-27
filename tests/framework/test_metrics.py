"""Tests for the metric classes of the framework."""
from datetime import timedelta

from optiframe.framework import ModelSize, StepTimes


class TestModelSize:
    def test_total_size_is_constraints_times_variables(self) -> None:
        """Test that the total size of the model is the constraint count times variable count."""
        model_size = ModelSize(variable_count=3, constraint_count=5)
        assert model_size.total_size == 15


class TestStepTimes:
    def test_total_is_sum_of_all_times(self) -> None:
        """Test that the total time is the sum of all step times."""
        step_times = StepTimes(
            validate=timedelta(seconds=1),
            pre_processing=timedelta(milliseconds=2),
            build_mip=timedelta(seconds=3),
            solve=timedelta(milliseconds=4),
            extract_solution=timedelta(seconds=5),
        )

        assert step_times.total == timedelta(seconds=9, milliseconds=6)
