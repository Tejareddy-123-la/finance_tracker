"""
Smart Personal Finance Manager - backend (FastAPI + SQLite)

Run from the backend folder:   uvicorn main:app --reload
App:   http://127.0.0.1:8000        API docs:   http://127.0.0.1:8000/docs
"""
import base64
import calendar
import os
import re
import secrets
from datetime import date
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

import calculators as calc
from database import get_conn, init_db

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
APP_PASSWORD = os.getenv("APP_PASSWORD")  # set this when hosting online

app = FastAPI(title="Smart Personal Finance Manager")
init_db()


# ------------------------------------------------------------------ optional password
@app.middleware("http")
async def password_gate(request: Request, call_next):
    """If APP_PASSWORD is set, the browser asks for a password (any username)."""
    if APP_PASSWORD:
        ok = False
        header = request.headers.get("authorization", "")
        if header.startswith("Basic "):
            try:
                decoded = base64.b64decode(header[6:]).decode()
                ok = secrets.compare_digest(decoded.split(":", 1)[1], APP_PASSWORD)
            except Exception:
                ok = False
        if not ok:
            return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Finance"'})
    return await call_next(request)


# ------------------------------------------------------------------ models
class Txn(BaseModel):
    date: str
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: Optional[str] = None

    @field_validator("description")
    @classmethod
    def check_desc(cls, v: str):
        s = v.strip()
        if not re.match(r"^[a-zA-Z\s]+$", s):
            raise ValueError("Description must contain only alphabets and spaces (no numbers).")
        return s

    @field_validator("category")
    @classmethod
    def check_cat(cls, v: Optional[str]):
        if v:
            s = v.strip()
            if not re.match(r"^[a-zA-Z\s]+$", s):
                raise ValueError("Category must contain only alphabets and spaces (no numbers).")
            return s
        return None


class Budget(BaseModel):
    category: str = Field(min_length=1)
    monthly_limit: float = Field(gt=0)

    @field_validator("category")
    @classmethod
    def check_bcat(cls, v: str):
        s = v.strip()
        if not re.match(r"^[a-zA-Z\s]+$", s):
            raise ValueError("Category must contain only alphabets and spaces (no numbers).")
        return s


class Debt(BaseModel):
    name: str = Field(min_length=1)
    balance: float = Field(gt=0)
    annual_rate: float = Field(ge=0)
    min_payment: float = Field(gt=0)

    @field_validator("name")
    @classmethod
    def check_dname(cls, v: str):
        s = v.strip()
        if not re.match(r"^[a-zA-Z\s]+$", s):
            raise ValueError("Debt name must contain only alphabets and spaces (no numbers).")
        return s


class Goal(BaseModel):
    name: str = Field(min_length=1)
    target: float = Field(gt=0)
    saved: float = Field(ge=0, default=0)
    deadline: str

    @field_validator("name")
    @classmethod
    def check_gname(cls, v: str):
        s = v.strip()
        if not re.match(r"^[a-zA-Z\s]+$", s):
            raise ValueError("Goal name must contain only alphabets and spaces (no numbers).")
        return s


class Amount(BaseModel):
    amount: float = Field(gt=0)


class Quick(BaseModel):
    text: str = Field(min_length=1)


def check_date(value: str):
    try:
        date.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, f"Invalid date '{value}'. Use YYYY-MM-DD.")


def insert_txn(conn, t: Txn):
    check_date(t.date)
    raw_cat = (t.category or "").strip()
    category = (raw_cat or calc.categorize(t.description, t.type)).strip().title()
    conn.execute(
        "INSERT INTO transactions (date, description, amount, type, category) VALUES (?,?,?,?,?)",
        (t.date, t.description.strip(), t.amount, t.type, category),
    )


# ------------------------------------------------------------------ transactions
@app.get("/api/transactions")
def list_transactions(month: Optional[str] = None):
    conn = get_conn()
    if month:
        rows = conn.execute("SELECT * FROM transactions WHERE date LIKE ? ORDER BY date DESC, id DESC",
                            (month + "%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/transactions")
def add_transaction(t: Txn):
    conn = get_conn()
    insert_txn(conn, t)
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/transactions/bulk")
def add_bulk(items: List[Txn]):
    conn = get_conn()
    for t in items:
        insert_txn(conn, t)
    conn.commit()
    conn.close()
    return {"ok": True, "imported": len(items)}


@app.delete("/api/transactions/{txn_id}")
def delete_transaction(txn_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/quickadd")
def quick_add(q: Quick):
    """'Spent 250 on lunch' -> expense 250, category Food. Works with voice input too."""
    match = re.search(r"(\d+(?:\.\d+)?)", q.text.replace(",", ""))
    if not match:
        raise HTTPException(400, "No amount found. Try: 'Spent 250 on lunch'.")
    is_income = re.search(r"\b(earned|received|salary|credited|got paid|income)\b", q.text.lower())
    
    clean_desc = re.sub(r"[^a-zA-Z\s]", " ", q.text)
    clean_desc = re.sub(r"\s+", " ", clean_desc).strip()
    if not clean_desc:
        clean_desc = "Salary Income" if is_income else "Daily Expense"

    t = Txn(date=date.today().isoformat(), description=clean_desc,
            amount=float(match.group(1)), type="income" if is_income else "expense")
    conn = get_conn()
    insert_txn(conn, t)
    conn.commit()
    conn.close()
    return {"ok": True, "type": t.type, "amount": t.amount,
            "category": calc.categorize(t.description, t.type)}


# ------------------------------------------------------------------ budgets
@app.get("/api/budgets")
def list_budgets():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM budgets ORDER BY category").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.put("/api/budgets")
def set_budget(b: Budget):
    conn = get_conn()
    cat_title = b.category.strip().title()
    conn.execute("INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
                 "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
                 (cat_title, b.monthly_limit))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/budgets/{category}")
def delete_budget(category: str):
    conn = get_conn()
    conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/budgets/suggest")
def suggest_budgets():
    """Smart cutoff engine: average of your last 3 full months per category, minus 10%."""
    this_month = date.today().strftime("%Y-%m")
    conn = get_conn()
    rows = conn.execute(
        "SELECT substr(date,1,7) AS m, category, SUM(amount) AS t FROM transactions "
        "WHERE type='expense' AND substr(date,1,7) < ? GROUP BY m, category", (this_month,)).fetchall()
    months = sorted({r["m"] for r in rows})[-3:]
    if not months:
        conn.close()
        raise HTTPException(400, "Need at least one past month of expenses to suggest budgets.")
    totals = {}
    for r in rows:
        if r["m"] in months:
            totals[r["category"]] = totals.get(r["category"], 0) + r["t"]
    suggestions = {}
    for cat, total in totals.items():
        limit = round(total / len(months) * 0.9, -1)
        if limit > 0:
            suggestions[cat] = limit
            conn.execute("INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
                         "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
                         (cat, limit))
    conn.commit()
    conn.close()
    return {"ok": True, "based_on_months": months, "budgets": suggestions}


# ------------------------------------------------------------------ dashboard summary
@app.get("/api/summary")
def summary(month: Optional[str] = None):
    month = month or date.today().strftime("%Y-%m")
    try:
        year, mon = map(int, month.split("-"))
        days_in_month = calendar.monthrange(year, mon)[1]
    except Exception:
        raise HTTPException(400, "month must look like 2026-10")

    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM transactions WHERE date LIKE ?", (month + "%",))]
    all_expenses = [dict(r) for r in conn.execute("SELECT * FROM transactions WHERE type='expense'")]
    budgets = {r["category"]: r["monthly_limit"] for r in conn.execute("SELECT * FROM budgets")}
    debts = [dict(r) for r in conn.execute("SELECT * FROM debts")]
    conn.close()

    income = sum(r["amount"] for r in rows if r["type"] == "income")
    expense = sum(r["amount"] for r in rows if r["type"] == "expense")
    balance = income - expense

    by_category = {}
    by_cat_lower = {}
    for r in rows:
        if r["type"] == "expense":
            cat_clean = r["category"].strip().title()
            by_category[cat_clean] = by_category.get(cat_clean, 0) + r["amount"]
            by_cat_lower[cat_clean.lower()] = by_cat_lower.get(cat_clean.lower(), 0) + r["amount"]

    today = date.today()
    if (today.year, today.month) == (year, mon):
        day = today.day
    elif (year, mon) < (today.year, today.month):
        day = days_in_month
    else:
        day = 1
    days_left = days_in_month - day + 1 if (today.year, today.month) == (year, mon) else 0
    projected = calc.forecast(expense, day, days_in_month)

    budget_status, alerts, exceeded = [], [], 0

    # 1. High-priority Overspending / Negative Balance Alerts
    if income > 0 and expense > income:
        over = expense - income
        alerts.append(f"🚨 CRITICAL OVERSPENDING: Total spent (₹{expense:,.0f}) exceeds your income (₹{income:,.0f}) by ₹{over:,.0f}! You are in negative balance (-₹{over:,.0f}).")
    elif income == 0 and expense > 0:
        alerts.append(f"⚠️ NEGATIVE BALANCE: You have spent ₹{expense:,.0f} this month with zero recorded income (Balance: -₹{expense:,.0f}).")

    if projected > income and income > 0:
        alerts.append(f"📈 FORECAST ALERT: At your current daily pace, month-end spending will reach ₹{projected:,.0f}, exceeding your income by ₹{projected - income:,.0f}.")

    # 2. Case-Insensitive Category Budget Matching & Alerts
    for cat, limit in budgets.items():
        cat_clean = cat.strip().title()
        spent = by_cat_lower.get(cat.strip().lower(), 0)
        pct = (spent / limit * 100) if limit > 0 else 0
        budget_status.append({
            "category": cat_clean,
            "limit": limit,
            "spent": round(spent, 2),
            "percent": round(pct)
        })
        if pct >= 100:
            exceeded += 1
            alerts.append(f"🔴 {cat_clean}: Budget exceeded ({pct:.0f}% used - spent ₹{spent:,.0f} of ₹{limit:,.0f} limit)")
        elif pct >= 80:
            alerts.append(f"🟡 {cat_clean}: High spending ({pct:.0f}% used - spent ₹{spent:,.0f} of ₹{limit:,.0f} limit)")

    discipline = 1 - exceeded / len(budgets) if budgets else 1

    total_budget = sum(budgets.values())
    daily_allowance = None
    if total_budget and days_left:
        daily_allowance = round((total_budget - expense) / days_left, 2)

    health = calc.health_score(income, expense, sum(d["min_payment"] for d in debts), discipline)
    anomalies = [a for a in calc.find_anomalies(all_expenses) if a["date"].startswith(month)]

    return {
        "month": month, "income": round(income, 2), "expense": round(expense, 2),
        "balance": round(balance, 2), "by_category": by_category,
        "budget_status": budget_status, "alerts": alerts,
        "forecast": {"projected": projected, "day": day, "days": days_in_month},
        "daily_allowance": daily_allowance, "total_budget": total_budget,
        "health": health,
        "insights": calc.make_insights(by_category, budgets, projected, income),
        "anomalies": anomalies[:10],
        "subscriptions": calc.detect_subscriptions(all_expenses),
    }


# ------------------------------------------------------------------ debts
@app.get("/api/debts")
def list_debts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM debts ORDER BY annual_rate DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/debts")
def add_debt(d: Debt):
    conn = get_conn()
    conn.execute("INSERT INTO debts (name, balance, annual_rate, min_payment) VALUES (?,?,?,?)",
                 (d.name.strip(), d.balance, d.annual_rate, d.min_payment))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/debts/{debt_id}")
def delete_debt(debt_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM debts WHERE id = ?", (debt_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/debts/analysis")
def debt_analysis(extra: float = 0):
    """Per-debt interest plus Avalanche vs Snowball comparison (the what-if slider uses `extra`)."""
    debts = list_debts()
    per_debt = []
    for d in debts:
        alone = calc.simulate_payoff([d], 0, "avalanche")
        per_debt.append({**d,
                         "monthly_interest": round(d["balance"] * d["annual_rate"] / 1200, 2),
                         "months_to_clear": alone["months"],
                         "total_interest": alone["total_interest"],
                         "paid_off": alone["paid_off"]})
    minimum_only = calc.simulate_payoff(debts, 0, "avalanche")
    avalanche = calc.simulate_payoff(debts, extra, "avalanche")
    snowball = calc.simulate_payoff(debts, extra, "snowball")
    return {
        "debts": per_debt,
        "total_monthly_interest": round(sum(d["monthly_interest"] for d in per_debt), 2),
        "minimum_only": minimum_only, "avalanche": avalanche, "snowball": snowball,
        "months_saved": minimum_only["months"] - avalanche["months"],
        "interest_saved": round(minimum_only["total_interest"] - avalanche["total_interest"], 2),
    }


# ------------------------------------------------------------------ calculators
@app.get("/api/calc/emi")
def calc_emi(principal: float, rate: float, months: int):
    if principal <= 0 or months <= 0 or rate < 0:
        raise HTTPException(400, "Principal and months must be positive; rate cannot be negative.")
    return calc.emi(principal, rate, months)


@app.get("/api/calc/interest")
def calc_interest(principal: float, rate: float, years: float):
    return {"simple": calc.simple_interest(principal, rate, years),
            "compound": calc.compound_interest(principal, rate, years)}


# ------------------------------------------------------------------ goals
@app.get("/api/goals")
def list_goals():
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM goals ORDER BY deadline")]
    conn.close()
    today = date.today()
    for g in rows:
        try:
            dl = date.fromisoformat(g["deadline"])
            months_left = max(1, (dl.year - today.year) * 12 + dl.month - today.month)
        except ValueError:
            months_left = 1
        g["months_left"] = months_left
        g["monthly_needed"] = round(max(g["target"] - g["saved"], 0) / months_left, 2)
        g["percent"] = min(100, round(g["saved"] / g["target"] * 100))
    return rows


@app.post("/api/goals")
def add_goal(g: Goal):
    check_date(g.deadline)
    conn = get_conn()
    conn.execute("INSERT INTO goals (name, target, saved, deadline) VALUES (?,?,?,?)",
                 (g.name.strip(), g.target, g.saved, g.deadline))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/goals/{goal_id}/add")
def add_to_goal(goal_id: int, a: Amount):
    conn = get_conn()
    conn.execute("UPDATE goals SET saved = saved + ? WHERE id = ?", (a.amount, goal_id))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/api/goals/{goal_id}")
def delete_goal(goal_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ------------------------------------------------------------------ frontend (same server)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
