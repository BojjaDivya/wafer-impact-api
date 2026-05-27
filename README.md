# Wafer Impact Calculator API

A Python REST API for computing the climate-change impact (kg CO₂) of wafer baking activities, built for Company A's BrightWay2-format recipe database.

---

## Quick Start

### 1. Install dependencies

```bash
pip install fastapi uvicorn openpyxl python-multipart sqlalchemy pytest
```

### 2. Place the data file

Copy `Company_A_database.xlsx` into the project root (same directory as `README.md`).

### 3. Run the API

```bash
uvicorn app.main:app --reload
```

The API starts at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## API Endpoints

### Part 1 – Impact Calculation

#### `GET /impact/{activity_name}`

Returns the total climate-change impact of an activity in kg CO₂ per unit of product.

**Parameters:**
- `activity_name` (path) – exact name of the activity, e.g. `Baked Biscuit Wafers`
- `partner_id` (query, optional) – include a partner's uploaded recipes in the lookup

**Example:**
```bash
curl "http://localhost:8000/impact/Baked%20Biscuit%20Wafers"
```

**Response:**
```json
{
  "activity": "Baked Biscuit Wafers",
  "impact_kg_co2": 3.057,
  "unit": "kg CO2 per unit of product",
  "partner_id": null
}
```

#### `GET /activities`

List all known activity names (base + optional partner layer).

---

### Part 2 – Partner Recipe Upload

#### `POST /partner/{partner_id}/upload`

Upload a partner's recipe Excel file. The file must follow the BrightWay2 format (same as `Company_A_database.xlsx`, `BW database` sheet). Partner data is stored separately in SQLite and never pollutes Company A's base data.

**Constraints enforced:**
- Partner activities may *reference* Company A activities but must not redefine them.
- Conflict detection raises HTTP 409 if the partner tries to override a base activity.

**Example:**
```bash
curl -X POST "http://localhost:8000/partner/company_b/upload" \
     -F "file=@Company_B_request.xlsx"
```

#### Query a partner's recipe impact

```bash
curl "http://localhost:8000/impact/Baked%20Chocolate%20Wafers?partner_id=company_b"
```

**Response:**
```json
{
  "activity": "Baked Chocolate Wafers",
  "impact_kg_co2": 2.2974,
  "unit": "kg CO2 per unit of product",
  "partner_id": "company_b"
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 6 tests cover:
- Electricity mix calculation
- Basic Biscuit Dough (leaf materials)
- Baked Biscuit Wafers (full recursive resolution)
- Missing activity error handling
- Circular dependency detection
- Memoization consistency

---

## Computed Impact Values (reference)

| Activity | Impact (kg CO₂/unit) |
|---|---|
| Electricity, GLO mix | 0.335 kg CO₂/kWh |
| Basic Biscuit Dough | 2.784 kg CO₂/kg |
| Chocolate Wafer Batter | 1.940 kg CO₂/kg |
| Baked Biscuit Wafers | 3.057 kg CO₂/kg |
| **Baked Chocolate Wafers** (Company B) | **2.297 kg CO₂/kg** |

---

## Project Structure

```
wafer_api/
├── app/
│   ├── main.py         # FastAPI app, route handlers
│   ├── models.py       # Activity, Exchange dataclasses
│   ├── parser.py       # Excel → Activity parser (BW2 format)
│   ├── calculator.py   # Recursive impact resolver with memoization
│   ├── loader.py       # Company A database loader
│   ├── partner.py      # Partner store (SQLite persistence)
│   └── database.py     # DB initialisation
├── tests/
│   └── test_calculator.py
├── README.md
└── DESIGN.md
```
