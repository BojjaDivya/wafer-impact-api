"""
Load Company A's reference Excel database and wire up a shared impact factor
store that the ImpactCalculator can use.
"""

import os
from .parser import parse_full_database
from .calculator import ImpactCalculator

# Module-level singletons populated once at startup
_materials: dict[str, float] = {}
_electricity: dict[str, float] = {}


def load_company_a_database(path: str) -> dict:
    """
    Parse Company A's Excel file and cache the impact factor tables.
    Returns the activities dict.
    """
    global _materials, _electricity

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Company A database not found at '{path}'. "
            "Place Company_A_database.xlsx in the working directory."
        )

    activities, materials, electricity = parse_full_database(path)
    _materials = materials
    _electricity = electricity
    return activities


def get_impact_tables() -> tuple[dict, dict]:
    """Return the cached (materials, electricity) impact factor tables."""
    return _materials, _electricity


def make_calculator(activities: dict) -> ImpactCalculator:
    """Construct an ImpactCalculator using Company A's impact factor tables."""
    return ImpactCalculator(activities, _materials, _electricity)
