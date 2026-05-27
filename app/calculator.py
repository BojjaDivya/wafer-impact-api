"""
ImpactCalculator: recursively resolves the climate-change impact of an activity.

Algorithm (BrightWay2 simplified):
  For each technosphere exchange of an activity:
    1. If the exchange name exists as another Activity → recurse.
    2. If the exchange unit is 'kilowatt hour' → look up in the electricity table.
    3. Otherwise → look up in the materials table.
    
  impact = Σ (exchange.amount × resolved_impact_per_unit)

Memoization avoids recomputing shared sub-activities.
"""

from functools import lru_cache
from .models import Activity


class ImpactCalculator:
    def __init__(
        self,
        activities: dict[str, Activity],
        materials: dict[str, float] | None = None,
        electricity: dict[str, float] | None = None,
    ):
        self._activities = activities
        self._materials = materials or {}
        self._electricity = electricity or {}
        self._memo: dict[str, float] = {}

    def compute(self, activity_name: str) -> float:
        """Return total kg CO2 per unit of product for the named activity."""
        if activity_name not in self._activities:
            raise KeyError(activity_name)
        return self._resolve(activity_name, visiting=set())

    def _resolve(self, name: str, visiting: set) -> float:
        """Recursively resolve an activity, detecting circular references."""
        if name in self._memo:
            return self._memo[name]

        if name in visiting:
            raise RecursionError(f"Circular dependency at '{name}'")

        if name not in self._activities:
            raise KeyError(name)

        visiting = visiting | {name}  # immutable copy per branch
        activity = self._activities[name]
        total = 0.0

        for exc in activity.inputs:
            if exc.name in self._activities:
                # Intermediate activity → recurse
                impact_per_unit = self._resolve(exc.name, visiting)
            elif exc.unit == "kilowatt hour":
                # Electricity leaf
                impact_per_unit = self._electricity.get(exc.name)
                if impact_per_unit is None:
                    raise KeyError(
                        f"Electricity factor not found for '{exc.name}'"
                    )
            else:
                # Raw material leaf
                impact_per_unit = self._materials.get(exc.name)
                if impact_per_unit is None:
                    raise KeyError(
                        f"Material factor not found for '{exc.name}'"
                    )

            total += exc.amount * impact_per_unit

        self._memo[name] = total
        return total
