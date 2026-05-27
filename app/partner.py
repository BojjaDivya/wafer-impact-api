"""
PartnerStore: persists partner activities to SQLite so uploads survive restarts.

Schema:
  partner_activities (partner_id TEXT, activity_name TEXT, activity_json TEXT)

We store each Activity as JSON; the database guarantees Company B's recipes
never pollute Company A's in-memory store.
"""

import json
import sqlite3
from .models import Activity, Exchange

DB_PATH = "partner_data.db"


def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS partner_activities (
            partner_id    TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            activity_json TEXT NOT NULL,
            PRIMARY KEY (partner_id, activity_name)
        )
    """)
    con.commit()
    con.close()


class PartnerStore:
    """Thread-safe (via SQLite) per-partner activity store."""

    def save(self, partner_id: str, activities: dict[str, Activity]):
        con = sqlite3.connect(DB_PATH)
        for name, act in activities.items():
            payload = _activity_to_json(act)
            con.execute(
                "INSERT OR REPLACE INTO partner_activities VALUES (?, ?, ?)",
                (partner_id, name, payload),
            )
        con.commit()
        con.close()

    def get(self, partner_id: str) -> dict[str, Activity] | None:
        con = sqlite3.connect(DB_PATH)
        rows = con.execute(
            "SELECT activity_name, activity_json FROM partner_activities WHERE partner_id = ?",
            (partner_id,),
        ).fetchall()
        con.close()

        if not rows:
            return None

        return {name: _activity_from_json(payload) for name, payload in rows}

    def list_partners(self) -> list[str]:
        con = sqlite3.connect(DB_PATH)
        rows = con.execute(
            "SELECT DISTINCT partner_id FROM partner_activities"
        ).fetchall()
        con.close()
        return [r[0] for r in rows]


# ─── serialization helpers ───────────────────────────────────────────────────

def _activity_to_json(act: Activity) -> str:
    return json.dumps({
        "name": act.name,
        "location": act.location,
        "unit": act.unit,
        "reference_product": act.reference_product,
        "exchanges": [
            {
                "name": e.name,
                "amount": e.amount,
                "unit": e.unit,
                "location": e.location,
                "type": e.type,
                "reference_product": e.reference_product,
            }
            for e in act.exchanges
        ],
    })


def _activity_from_json(payload: str) -> Activity:
    d = json.loads(payload)
    return Activity(
        name=d["name"],
        location=d["location"],
        unit=d["unit"],
        reference_product=d["reference_product"],
        exchanges=[Exchange(**e) for e in d["exchanges"]],
    )
