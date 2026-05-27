"""
Tests for the Wafer Impact Calculator.

Run with:
    pytest tests/test_calculator.py -v
"""

import pytest
from app.models import Activity, Exchange
from app.calculator import ImpactCalculator

# ─── Fixtures ─────────────────────────────────────────────────────────────────

MATERIALS = {
    "Wheat flour": 0.8,
    "Sugar": 0.6,
    "Butter": 12.0,
    "Eggs": 4.5,
    "Milk": 1.3,
    "Cocoa powder": 6.0,
    "Baking powder": 1.0,
    "Vegetable oil": 3.0,
    "Water": 0.1,
}

ELECTRICITY = {
    "Renewable electricity": 0.2,
    "Natural gas electricity": 0.6,
    "Nuclear electricity": 0.1,
    "Coal electricity": 0.9,
}


def make_exc(name, amount, unit="kilogram", type_="technosphere"):
    return Exchange(name=name, amount=amount, unit=unit,
                    location="GLO", type=type_, reference_product=name)


def make_activity(name, exchanges):
    act = Activity(name=name, location="GLO", unit="kilogram",
                   reference_product=name)
    act.exchanges = exchanges
    return act


# ─── Electricity mix ──────────────────────────────────────────────────────────

def test_electricity_mix():
    """
    Electricity, GLO mix = 0.45*0.2 + 0.3*0.6 + 0.2*0.1 + 0.05*0.9
                         = 0.09 + 0.18 + 0.02 + 0.045 = 0.335 kg CO2/kWh
    """
    electricity_mix = make_activity("Electricity, GLO mix", [
        make_exc("Electricity, GLO mix", 1, unit="kilowatt hour", type_="production"),
        make_exc("Renewable electricity",    0.45, unit="kilowatt hour"),
        make_exc("Natural gas electricity",  0.30, unit="kilowatt hour"),
        make_exc("Nuclear electricity",      0.20, unit="kilowatt hour"),
        make_exc("Coal electricity",         0.05, unit="kilowatt hour"),
    ])
    activities = {"Electricity, GLO mix": electricity_mix}
    calc = ImpactCalculator(activities, MATERIALS, ELECTRICITY)
    result = calc.compute("Electricity, GLO mix")
    assert abs(result - 0.335) < 1e-6


# ─── Basic Biscuit Dough ──────────────────────────────────────────────────────

def test_basic_biscuit_dough():
    """
    Basic Biscuit Dough:
      0.5*0.8 + 0.2*0.6 + 0.15*12 + 0.1*4.5 + 0.01*1 + 0.04*0.1
      = 0.4 + 0.12 + 1.8 + 0.45 + 0.01 + 0.004 = 2.784
    """
    dough = make_activity("Basic Biscuit Dough", [
        make_exc("Basic Biscuit Dough", 1, type_="production"),
        make_exc("Wheat flour",    0.50),
        make_exc("Sugar",          0.20),
        make_exc("Butter",         0.15),
        make_exc("Eggs",           0.10),
        make_exc("Baking powder",  0.01),
        make_exc("Water",          0.04),
    ])
    activities = {"Basic Biscuit Dough": dough}
    calc = ImpactCalculator(activities, MATERIALS, ELECTRICITY)
    result = calc.compute("Basic Biscuit Dough")
    assert abs(result - 2.784) < 1e-6


# ─── Baked Biscuit Wafers (full recursive) ────────────────────────────────────

def test_baked_biscuit_wafers():
    """
    Full recursive calculation:
      dough_impact = 2.784
      elec_impact  = 0.335
      
      Baked Biscuit Wafers = 1*2.784 + 0.8*0.335 + 0.05*0.1
                           = 2.784 + 0.268 + 0.005 = 3.057
    """
    dough = make_activity("Basic Biscuit Dough", [
        make_exc("Basic Biscuit Dough", 1, type_="production"),
        make_exc("Wheat flour",   0.50),
        make_exc("Sugar",         0.20),
        make_exc("Butter",        0.15),
        make_exc("Eggs",          0.10),
        make_exc("Baking powder", 0.01),
        make_exc("Water",         0.04),
    ])
    electricity_mix = make_activity("Electricity, GLO mix", [
        make_exc("Electricity, GLO mix", 1, unit="kilowatt hour", type_="production"),
        make_exc("Renewable electricity",   0.45, unit="kilowatt hour"),
        make_exc("Natural gas electricity", 0.30, unit="kilowatt hour"),
        make_exc("Nuclear electricity",     0.20, unit="kilowatt hour"),
        make_exc("Coal electricity",        0.05, unit="kilowatt hour"),
    ])
    wafers = make_activity("Baked Biscuit Wafers", [
        make_exc("Baked Biscuit Wafers", 1, type_="production"),
        make_exc("Basic Biscuit Dough",  1.0),
        make_exc("Electricity, GLO mix", 0.8, unit="kilowatt hour"),
        make_exc("Water",                0.05),
    ])
    activities = {
        "Basic Biscuit Dough":  dough,
        "Electricity, GLO mix": electricity_mix,
        "Baked Biscuit Wafers": wafers,
    }
    calc = ImpactCalculator(activities, MATERIALS, ELECTRICITY)
    result = calc.compute("Baked Biscuit Wafers")
    assert abs(result - 3.057) < 1e-6


# ─── Edge cases ───────────────────────────────────────────────────────────────

def test_missing_activity_raises():
    calc = ImpactCalculator({}, MATERIALS, ELECTRICITY)
    with pytest.raises(KeyError):
        calc.compute("Nonexistent Activity")


def test_circular_dependency_raises():
    a = make_activity("A", [make_exc("B", 1)])
    b = make_activity("B", [make_exc("A", 1)])
    calc = ImpactCalculator({"A": a, "B": b}, MATERIALS, ELECTRICITY)
    with pytest.raises(RecursionError):
        calc.compute("A")


def test_memoization_consistency():
    """Computing the same activity twice should give identical results."""
    dough = make_activity("Basic Biscuit Dough", [
        make_exc("Basic Biscuit Dough", 1, type_="production"),
        make_exc("Wheat flour", 0.50),
        make_exc("Sugar",       0.20),
        make_exc("Butter",      0.15),
        make_exc("Eggs",        0.10),
        make_exc("Baking powder", 0.01),
        make_exc("Water",       0.04),
    ])
    calc = ImpactCalculator({"Basic Biscuit Dough": dough}, MATERIALS, ELECTRICITY)
    r1 = calc.compute("Basic Biscuit Dough")
    r2 = calc.compute("Basic Biscuit Dough")
    assert r1 == r2
