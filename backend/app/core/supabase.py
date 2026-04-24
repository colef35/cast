"""
Thin DB abstraction — uses SQLite locally, Supabase when env vars are set.
"""
import os
import json
import uuid
from datetime import datetime
from app.core.database import get_db, init_db

_supabase_client = None
_use_supabase = False

if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"):
    try:
        from supabase import create_client as _create_client
        _supabase_client = _create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
        _use_supabase = True
    except Exception as e:
        print(f"[WARN] Supabase init failed ({e}), falling back to SQLite")

if not _use_supabase:
    init_db()


class _SQLiteTable:
    def __init__(self, table: str):
        self.table = table
        self._filters: list = []
        self._order_col = None
        self._order_desc = False
        self._single = False

    def select(self, cols="*"):
        return self

    def insert(self, row: dict):
        if "id" not in row:
            row["id"] = str(uuid.uuid4())
        self._insert_row = row
        return self

    def update(self, updates: dict):
        self._updates = updates
        return self

    def delete(self):
        self._delete = True
        return self

    def eq(self, col, val):
        self._filters.append((col, "=", val))
        return self

    def neq(self, col, val):
        self._filters.append((col, "!=", val))
        return self

    def lt(self, col, val):
        self._filters.append((col, "<", val))
        return self

    def lte(self, col, val):
        self._filters.append((col, "<=", val))
        return self

    def gt(self, col, val):
        self._filters.append((col, ">", val))
        return self

    def gte(self, col, val):
        self._filters.append((col, ">=", val))
        return self

    def order(self, col, desc=False):
        self._order_col = col
        self._order_desc = desc
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        conn = get_db()
        where = " AND ".join([f"{c}{op}?" for c, op, _ in self._filters])
        where_clause = f"WHERE {where}" if where else ""
        vals = [v for _, _, v in self._filters]

        if hasattr(self, "_insert_row"):
            row = self._insert_row
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            conn.execute(f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})", [
                json.dumps(v) if isinstance(v, (list, dict)) else v
                for v in row.values()
            ])
            conn.commit()
            result = conn.execute(f"SELECT * FROM {self.table} WHERE id=?", [row["id"]]).fetchone()
            conn.close()
            return _SQLiteResult([_row_to_dict(result, self.table)])

        if hasattr(self, "_delete"):
            rows = conn.execute(f"SELECT * FROM {self.table} {where_clause}", vals).fetchall()
            conn.execute(f"DELETE FROM {self.table} {where_clause}", vals)
            conn.commit()
            conn.close()
            return _SQLiteResult([_row_to_dict(r, self.table) for r in rows])

        if hasattr(self, "_updates"):
            set_clause = ", ".join([f"{k}=?" for k in self._updates])
            update_vals = list(self._updates.values()) + vals
            conn.execute(f"UPDATE {self.table} SET {set_clause} {where_clause}", update_vals)
            conn.commit()
            rows = conn.execute(f"SELECT * FROM {self.table} {where_clause}", vals).fetchall()
            conn.close()
            return _SQLiteResult([_row_to_dict(r, self.table) for r in rows])

        order = f"ORDER BY {self._order_col} {'DESC' if self._order_desc else 'ASC'}" if self._order_col else ""
        rows = conn.execute(f"SELECT * FROM {self.table} {where_clause} {order}", vals).fetchall()
        conn.close()
        data = [_row_to_dict(r, self.table) for r in rows]
        if self._single:
            return _SQLiteResult(data[0] if data else None, single=True)
        return _SQLiteResult(data)


class _SQLiteResult:
    def __init__(self, data, single=False):
        self.data = data if not single else data


def _row_to_dict(row, table: str) -> dict:
    if row is None:
        return None
    d = dict(row)
    # deserialize JSON columns
    for col in ("keywords",):
        if col in d and isinstance(d[col], str):
            try:
                d[col] = json.loads(d[col])
            except Exception:
                pass
    return d


class _DB:
    def table(self, name: str):
        if _use_supabase:
            return _supabase_client.table(name)
        return _SQLiteTable(name)


_db = _DB()


def get_supabase():
    return _db
