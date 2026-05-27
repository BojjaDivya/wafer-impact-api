"""
Wafer Impact Calculator API
Company A's REST API for computing climate-change impact of wafer baking recipes.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import io

from .database import init_db
from .loader import load_company_a_database, make_calculator
from .calculator import ImpactCalculator
from .partner import PartnerStore
from .parser import parse_excel_database

app = FastAPI(
    title="Wafer Impact Calculator",
    description="Compute climate-change impact (kg CO2) of wafer baking activities.",
    version="1.0.0",
)

# In-memory stores
company_a_data = {}       # {activity_name: Activity}
partner_store = PartnerStore()  # Per-partner activity stores


@app.on_event("startup")
def startup():
    global company_a_data
    company_a_data = load_company_a_database("Company_A_database.xlsx")
    init_db()
    print(f"Loaded {len(company_a_data)} Company A activities.")


# ──────────────────────────────────────────
# Part 1 – Impact calculation
# ──────────────────────────────────────────

@app.get("/impact/{activity_name}", summary="Get climate-change impact of an activity")
def get_impact(activity_name: str, partner_id: str | None = None):
    """
    Returns total climate-change impact (kg CO2 per unit of product) for
    the given activity name.

    Optionally pass `partner_id` to also resolve activities from a specific
    partner's uploaded database (partner data is kept separate from Company A).
    """
    # Build a merged lookup: Company A base + optional partner layer
    merged = dict(company_a_data)  # copy; never mutate base

    if partner_id:
        partner_activities = partner_store.get(partner_id)
        if not partner_activities:
            raise HTTPException(status_code=404, detail=f"Partner '{partner_id}' not found.")
        # Partner activities overlay on top; they must not redefine Company A activities
        merged.update(partner_activities)

    calculator = make_calculator(merged)
    try:
        impact = calculator.compute(activity_name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Activity not found: {e}")
    except RecursionError:
        raise HTTPException(status_code=400, detail="Circular dependency detected in exchanges.")

    return {
        "activity": activity_name,
        "impact_kg_co2": round(impact, 6),
        "unit": "kg CO2 per unit of product",
        "partner_id": partner_id,
    }


@app.get("/activities", summary="List all known activities")
def list_activities(partner_id: str | None = None):
    """List all activity names available (base + optional partner layer)."""
    names = set(company_a_data.keys())
    if partner_id:
        partner_activities = partner_store.get(partner_id)
        if partner_activities:
            names |= set(partner_activities.keys())
    return {"activities": sorted(names)}


# ──────────────────────────────────────────
# Part 2 – Partner recipe upload
# ──────────────────────────────────────────

@app.post("/partner/{partner_id}/upload", summary="Upload a partner's recipe Excel file")
async def upload_partner_recipe(partner_id: str, file: UploadFile = File(...)):
    """
    Accepts an Excel file (.xlsx) containing partner activities in BrightWay2 format.
    The activities are persisted separately from Company A's base data.

    Partner activities may reference Company A activities but must not redefine them.
    """
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are accepted.")

    raw = await file.read()
    try:
        activities = parse_excel_database(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse Excel file: {e}")

    # Reject if partner tries to redefine a Company A activity
    conflicts = set(activities.keys()) & set(company_a_data.keys())
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=f"Partner file redefines Company A activities: {sorted(conflicts)}. "
                   "Partner data must not override the base database.",
        )

    partner_store.save(partner_id, activities)

    return {
        "partner_id": partner_id,
        "uploaded_activities": sorted(activities.keys()),
        "message": "Partner recipes uploaded successfully. Use GET /impact/{name}?partner_id={partner_id} to query.",
    }


@app.get("/partner/{partner_id}/activities", summary="List a partner's uploaded activities")
def list_partner_activities(partner_id: str):
    activities = partner_store.get(partner_id)
    if activities is None:
        raise HTTPException(status_code=404, detail=f"Partner '{partner_id}' not found.")
    return {"partner_id": partner_id, "activities": sorted(activities.keys())}
