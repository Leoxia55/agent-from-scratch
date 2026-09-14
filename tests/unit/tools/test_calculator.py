"""tools/_calculator.py 单元测试。"""

from __future__ import annotations

import pytest

from scratchagent.tools import calculator


class TestCalculator:
    def test_add(self):
        assert calculator("add", 1, 2) == 3.0

    def test_subtract(self):
        assert calculator("subtract", 5, 3) == 2.0

    def test_multiply(self):
        assert calculator("multiply", 4, 3) == 12.0

    def test_divide(self):
        assert calculator("divide", 10, 2) == 5.0

    def test_divide_by_zero(self):
        with pytest.raises(ValueError, match="divide by zero"):
            calculator("divide", 1, 0)

    def test_unknown_operator(self):
        with pytest.raises(ValueError, match="Unknown operator"):
            calculator("power", 2, 3)
