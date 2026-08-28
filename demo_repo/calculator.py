"""Simple calculator module for demonstration."""
from typing import List


def calculate_total(items: List[float]) -> float:
    """Calculates the total sum of a list of item prices.
    
    Args:
        items: List of numeric item prices.
        
    Returns:
        The total sum of prices.
        
    Raises:
        ValueError: If any item price is negative.
    """
    if any(item < 0 for item in items):
        raise ValueError("Item prices cannot be negative.")
    return sum(items)
