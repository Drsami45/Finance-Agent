"""SQLite persistence layer for the Finance Agent.

Handles all reads/writes for transactions and budgets. Kept independent
of LangChain/LangGraph so it can be tested or reused on its own.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "finance.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL
            )
        """)


def add_transaction(date: str, type_: str, category: str, amount: float, note: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO transactions (date, type, category, amount, note, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date, type_, category, amount, note, datetime.now().isoformat()),
        )
        return cur.lastrowid


def delete_transaction(transaction_id: int) -> bool:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        return cur.rowcount > 0


def get_transactions(category: str = None, type_: str = None,
                        start_date: str = None, end_date: str = None, limit: int = 200):
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if type_:
        query += " AND type = ?"
        params.append(type_)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def get_balance():
    with get_connection() as conn:
        income = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='income'"
        ).fetchone()[0]
        expense = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='expense'"
        ).fetchone()[0]
        return {"income": income, "expense": expense, "balance": income - expense}


def spending_by_category(start_date: str = None, end_date: str = None):
    query = "SELECT category, COALESCE(SUM(amount),0) as total FROM transactions WHERE type='expense'"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " GROUP BY category ORDER BY total DESC"
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def set_budget(category: str, monthly_limit: float):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit",
            (category, monthly_limit),
        )


def get_budgets():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM budgets").fetchall()
        return [dict(r) for r in rows]


def get_budget_status(month: str = None):
    """Return spend-vs-limit status per budgeted category. month format: 'YYYY-MM'."""
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    budgets = get_budgets()
    spend = spending_by_category(start_date=f"{month}-01", end_date=f"{month}-31")
    spend_map = {s["category"]: s["total"] for s in spend}
    status = []
    for b in budgets:
        spent = spend_map.get(b["category"], 0)
        status.append({
            "category": b["category"],
            "limit": b["monthly_limit"],
            "spent": spent,
            "remaining": b["monthly_limit"] - spent,
            "percent_used": round((spent / b["monthly_limit"] * 100), 1) if b["monthly_limit"] else 0,
        })
    return status