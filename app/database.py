import os
import sqlite3
from datetime import datetime
from app.config import DATABASE_URL, BASE_DIR

try:
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

if HAS_SQLALCHEMY:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
else:
    # ----------------------------------------------------
    # 輕量級純 SQLite3 兼容層 (零外部依賴)
    # ----------------------------------------------------
    class MiniEngine:
        def __init__(self, db_url):
            path = db_url.replace("sqlite:///", "")
            if path.startswith("/"):
                self.db_path = path
            else:
                self.db_path = str(BASE_DIR / path.lstrip("./"))
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        def connect(self):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    engine = MiniEngine(DATABASE_URL)

    class MiniMetadata:
        def create_all(self, bind):
            conn = bind.connect()
            cur = conn.cursor()
            for cls in MiniBase._registry:
                cols = []
                for name, col in cls._columns.items():
                    ctype = "TEXT"
                    if col.col_type in ("Integer", int): ctype = "INTEGER"
                    elif col.col_type in ("Float", float): ctype = "REAL"
                    elif col.col_type in ("Boolean", bool): ctype = "INTEGER"
                    
                    line = [f'"{name}"', ctype]
                    if col.primary_key:
                        line.append("PRIMARY KEY AUTOINCREMENT")
                    elif not col.nullable:
                        line.append("NOT NULL")
                    cols.append(" ".join(line))
                cur.execute(f"CREATE TABLE IF NOT EXISTS {cls.__tablename__} ({', '.join(cols)});")
                cur.execute(f"PRAGMA table_info({cls.__tablename__});")
                curr_cols = {row[1] for row in cur.fetchall()}
                for name, col in cls._columns.items():
                    if name != "id" and name not in curr_cols:
                        ctype = "TEXT"
                        if col.col_type in ("Integer", int): ctype = "INTEGER"
                        elif col.col_type in ("Float", float): ctype = "REAL"
                        elif col.col_type in ("Boolean", bool): ctype = "INTEGER"
                        cur.execute(f"ALTER TABLE {cls.__tablename__} ADD COLUMN \"{name}\" {ctype};")
            conn.commit()
            conn.close()

    class MiniBase:
        _registry = []
        metadata = MiniMetadata()

        def __init__(self, **kwargs):
            self.id = None
            self._persisted = False
            for k, col in getattr(self, '_columns', {}).items():
                d = col.default
                setattr(self, k, d() if callable(d) else d)
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __init_subclass__(cls):
            super().__init_subclass__()
            cls._columns = {}
            for k, v in list(cls.__dict__.items()):
                if hasattr(v, '_is_column'):
                    v.name = k
                    v.table = cls.__tablename__
                    cls._columns[k] = v
            MiniBase._registry.append(cls)

    Base = MiniBase

    class MiniQuery:
        def __init__(self, model_or_func, engine):
            self.model_or_func = model_or_func
            self.engine = engine
            self._filters = []
            self._orders = []
            self._limit_val = None
            self._distinct_col = None

        def filter(self, *conditions):
            for cond in conditions:
                if cond is not None:
                    self._filters.append(cond)
            return self

        def order_by(self, *orders):
            for o in orders:
                if o is not None:
                    self._orders.append(o)
            return self

        def limit(self, n):
            self._limit_val = n
            return self

        def distinct(self):
            if hasattr(self.model_or_func, 'name'):
                self._distinct_col = self.model_or_func.name
            return self

        def _build_sql(self, select_clause=None):
            model = self.model_or_func
            if hasattr(model, '__tablename__'):
                table = model.__tablename__
            elif hasattr(model, 'table'):
                table = model.table
            elif hasattr(model, 'model') and hasattr(model.model, '__tablename__'):
                table = model.model.__tablename__
            else:
                table = "unknown"

            select_str = select_clause or "*"
            where_clauses = []
            params = []

            for f in self._filters:
                clause, p = self._parse_condition(f)
                if clause:
                    where_clauses.append(clause)
                    params.extend(p)

            where_str = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            order_parts = []
            for o in self._orders:
                if isinstance(o, tuple) and len(o) == 2:
                    order_parts.append(f'"{o[1]}" {o[0].upper()}')
            order_str = f" ORDER BY {', '.join(order_parts)}" if order_parts else ""
            limit_str = f" LIMIT {self._limit_val}" if self._limit_val is not None else ""

            return f"SELECT {select_str} FROM {table}{where_str}{order_str}{limit_str}", params

        def _parse_condition(self, f):
            if isinstance(f, tuple):
                op = f[0]
                if op == 'eq':
                    v = f[2]
                    if isinstance(v, bool): v = 1 if v else 0
                    return f'"{f[1]}" = ?', [v]
                elif op == 'ne':
                    v = f[2]
                    if isinstance(v, bool): v = 1 if v else 0
                    return f'"{f[1]}" != ?', [v]
                elif op == 'contains':
                    return f'"{f[1]}" LIKE ?', [f"%{f[2]}%"]
                elif op == 'or':
                    sub_clauses, sub_p = [], []
                    for sub in f[1]:
                        sc, sp = self._parse_condition(sub)
                        if sc:
                            sub_clauses.append(sc)
                            sub_p.extend(sp)
                    return f"({' OR '.join(sub_clauses)})", sub_p
            return "", []

        def all(self):
            sql, params = self._build_sql()
            conn = self.engine.connect()
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            conn.close()
            results = []
            model = self.model_or_func
            for r in rows:
                obj = model()
                for k in r.keys():
                    setattr(obj, k, r[k])
                obj._persisted = True
                results.append(obj)
            return results

        def first(self):
            old_limit = self._limit_val
            self._limit_val = 1
            res = self.all()
            self._limit_val = old_limit
            return res[0] if res else None

        def count(self):
            if self._distinct_col:
                select_clause = f'COUNT(DISTINCT "{self._distinct_col}")'
            else:
                select_clause = "COUNT(*)"
            sql, params = self._build_sql(select_clause=select_clause)
            conn = self.engine.connect()
            cur = conn.cursor()
            cur.execute(sql, params)
            cnt = cur.fetchone()[0]
            conn.close()
            return cnt

        def scalar(self):
            if hasattr(self.model_or_func, 'col_name'):
                col = self.model_or_func.col_name
                table = self.model_or_func.table
                sql = f'SELECT SUM("{col}") FROM {table}'
                conn = self.engine.connect()
                cur = conn.cursor()
                cur.execute(sql)
                res = cur.fetchone()[0]
                conn.close()
                return res or 0.0
            return 0.0

    class MiniSession:
        def __init__(self, engine):
            self.engine = engine
            self._to_add = []
            self._to_delete = []

        def query(self, target):
            return MiniQuery(target, self.engine)

        def add(self, obj):
            self._to_add.append(obj)

        def delete(self, obj):
            self._to_delete.append(obj)

        def commit(self):
            conn = self.engine.connect()
            cur = conn.cursor()
            for obj in self._to_add:
                table = obj.__tablename__
                cols = [k for k in obj._columns.keys() if k != 'id']
                if getattr(obj, '_persisted', False) and isinstance(getattr(obj, 'id', None), int):
                    # UPDATE
                    set_str = ", ".join([f'"{k}" = ?' for k in cols])
                    vals = []
                    for k in cols:
                        v = getattr(obj, k, None)
                        if isinstance(v, datetime): v = v.isoformat()
                        elif isinstance(v, bool): v = 1 if v else 0
                        vals.append(v)
                    vals.append(obj.id)
                    cur.execute(f"UPDATE {table} SET {set_str} WHERE id = ?", vals)
                else:
                    # INSERT
                    col_str = ", ".join([f'"{k}"' for k in cols])
                    placeholders = ", ".join(["?" for _ in cols])
                    vals = []
                    for k in cols:
                        v = getattr(obj, k, None)
                        if isinstance(v, datetime): v = v.isoformat()
                        elif isinstance(v, bool): v = 1 if v else 0
                        vals.append(v)
                    cur.execute(f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})", vals)
                    obj.id = cur.lastrowid
                    obj._persisted = True
            
            for obj in self._to_delete:
                table = obj.__tablename__
                if getattr(obj, 'id', None) and isinstance(obj.id, int):
                    cur.execute(f"DELETE FROM {table} WHERE id = ?", [obj.id])

            conn.commit()
            conn.close()
            self._to_add.clear()
            self._to_delete.clear()

        def refresh(self, obj):
            if not getattr(obj, 'id', None) or not isinstance(obj.id, int):
                return
            conn = self.engine.connect()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {obj.__tablename__} WHERE id = ?", [obj.id])
            row = cur.fetchone()
            conn.close()
            if row:
                for k in row.keys():
                    setattr(obj, k, row[k])
                obj._persisted = True

        def rollback(self):
            self._to_add.clear()
            self._to_delete.clear()

        def close(self):
            pass

    def SessionLocal():
        return MiniSession(engine)

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
