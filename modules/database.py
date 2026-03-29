import sqlite3
import os
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "expenses.db")


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            vendor TEXT NOT NULL DEFAULT '',
            amount INTEGER NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            description TEXT NOT NULL DEFAULT '',
            receipt_path TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_expense(date: str, vendor: str, amount: int, category: str,
                description: str = "", receipt_path: str = "") -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO expenses (date, vendor, amount, category, description, receipt_path, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (date, vendor, amount, category, description, receipt_path,
         datetime.now().isoformat()),
    )
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def get_expenses(start_date: str = None, end_date: str = None,
                 category: str = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_expense(expense_id: int, **kwargs) -> None:
    allowed = {"date", "vendor", "amount", "category", "description", "receipt_path"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    conn = get_connection()
    conn.execute(
        f"UPDATE expenses SET {set_clause} WHERE id = ?",
        list(fields.values()) + [expense_id],
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


def get_categories() -> list[str]:
    return [
        "交通費",
        "交際費",
        "会議費",
        "消耗品費",
        "通信費",
        "旅費交通費",
        "新聞図書費",
        "雑費",
        "その他",
    ]
