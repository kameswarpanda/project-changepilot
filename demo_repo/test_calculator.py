"""Unit tests for baseline calculator."""
import pytest
from calculator import calculate_total


def test_calculate_total_basic():
    """Verify standard addition."""
    assert calculate_total([10.0, 20.0, 30.0]) == 60.0


def test_calculate_total_empty():
    """Verify empty list."""
    assert calculate_total([]) == 0.0


def test_calculate_total_negative_raises():
    """Verify negative item price raises ValueError."""
    with pytest.raises(ValueError, match="Item prices cannot be negative"):
        calculate_total([10.0, -5.0])
