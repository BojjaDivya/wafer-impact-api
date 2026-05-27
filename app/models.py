"""
Core data models for the Wafer Impact Calculator.
Mirrors the BrightWay2 simplified format used in the Excel database.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Exchange:
    """
    A single exchange (input or output) within an activity.

    - 'production' exchanges represent the activity's own output.
    - 'technosphere' exchanges represent inputs: either raw materials
      (looked up in Materials/Electricity sheets) or other activities
      (resolved recursively).
    """
    name: str
    amount: float
    unit: str                                  # 'kilogram' | 'kilowatt hour'
    location: str
    type: Literal["production", "technosphere"]
    reference_product: str


@dataclass
class Activity:
    """
    A single cooking/processing activity with its full list of exchanges.
    """
    name: str
    location: str
    unit: str
    reference_product: str
    exchanges: list[Exchange] = field(default_factory=list)

    @property
    def inputs(self) -> list[Exchange]:
        """Return only technosphere (input) exchanges."""
        return [e for e in self.exchanges if e.type == "technosphere"]
