"""
Sales Demo API — dùng cho OpenClaw sales-advisor skill.
Chạy: uvicorn main:app --reload --port 8000
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
PRODUCTS_PATH = BASE_DIR / "data" / "products.json"
DB_PATH = BASE_DIR / "sales_agent.db"

app = FastAPI(title="Sales Demo API")


def load_products():
    with open(PRODUCTS_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            name TEXT,
            phone TEXT,
            channel TEXT,
            need TEXT,
            sku TEXT,
            status TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS handoff_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            reason TEXT,
            summary TEXT,
            channel TEXT,
            contact TEXT,
            status TEXT
        )"""
    )
    conn.commit()
    conn.close()


init_db()


# ---------- search_products ----------
@app.get("/search_products")
def search_products(query: str = "", max_price: Optional[int] = None):
    products = load_products()
    query_l = query.lower()
    results = []
    for p in products:
        text = f"{p['name']} {p['category']} {p['audience']}".lower()
        matches_query = query_l == "" or any(word in text for word in query_l.split())
        matches_price = max_price is None or p["price_vnd"] <= max_price
        if matches_query and matches_price:
            results.append(p)
    return {"count": len(results), "results": results[:5]}


# ---------- get_product_details ----------
@app.get("/get_product_details")
def get_product_details(sku: str):
    products = load_products()
    for p in products:
        if p["sku"].lower() == sku.lower():
            return p
    raise HTTPException(status_code=404, detail="SKU không tồn tại trong dữ liệu")


# ---------- check_inventory ----------
@app.get("/check_inventory")
def check_inventory(sku: str):
    products = load_products()
    for p in products:
        if p["sku"].lower() == sku.lower():
            return {"sku": p["sku"], "stock": p["stock"], "in_stock": p["stock"] > 0}
    raise HTTPException(status_code=404, detail="SKU không tồn tại trong dữ liệu")


# ---------- create_lead ----------
class LeadIn(BaseModel):
    name: str
    phone: str
    channel: str
    need: Optional[str] = None
    sku: Optional[str] = None


@app.post("/create_lead")
def create_lead(lead: LeadIn):
    conn = get_db()
    conn.execute(
        "INSERT INTO leads (created_at, name, phone, channel, need, sku, status) "
        "VALUES (?, ?, ?, ?, ?, ?, 'new')",
        (datetime.utcnow().isoformat(), lead.name, lead.phone, lead.channel, lead.need, lead.sku),
    )
    conn.commit()
    lead_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return {"lead_id": lead_id, "status": "created"}


# ---------- handoff_to_human ----------
class HandoffIn(BaseModel):
    reason: str
    summary: str
    channel: str
    contact: Optional[str] = None


@app.post("/handoff_to_human")
def handoff_to_human(ticket: HandoffIn):
    conn = get_db()
    conn.execute(
        "INSERT INTO handoff_tickets (created_at, reason, summary, channel, contact, status) "
        "VALUES (?, ?, ?, ?, ?, 'open')",
        (datetime.utcnow().isoformat(), ticket.reason, ticket.summary, ticket.channel, ticket.contact),
    )
    conn.commit()
    ticket_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.close()
    return {"ticket_id": ticket_id, "status": "open"}


# ---------- simple admin views (đủ dùng cho demo, không cần UI) ----------
@app.get("/admin/leads")
def admin_leads():
    conn = get_db()
    rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/admin/handoffs")
def admin_handoffs():
    conn = get_db()
    rows = conn.execute("SELECT * FROM handoff_tickets ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
