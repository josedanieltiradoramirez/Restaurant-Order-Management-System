import sqlite3 as sql
class Database():
    def __init__(self, database, table):
        if not database.endswith(".db"):
            raise ValueError("Database name must end with .db")
        if not table.isidentifier():
            raise ValueError("Invalid table name")

        self.database = database
        self.table = table
        self.create_database()

    def connect(self):
        return sql.connect(self.database)

    def _base_select_query(self):
        if self.table == "orders":
            return (
                f"SELECT id, created_at, closed_at, service_date, name, table_name, "
                f"status, to_go, amount_paid, total_amount FROM {self.table}"
            )
        return f"SELECT * FROM {self.table}"
        
    def create_database(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    closed_at TEXT NOT NULL,
                    service_date TEXT,
                    sent_status INTEGER NOT NULL DEFAULT 0,
                    name TEXT,
                    table_name TEXT,
                    status TEXT NOT NULL,
                    to_go INTEGER NOT NULL,
                    amount_paid REAL NOT NULL,
                    total_amount REAL NOT NULL
                )
            """)
            self._ensure_column(conn, "service_date", "TEXT")
            self._ensure_column(conn, "sent_status", "INTEGER NOT NULL DEFAULT 0")
    
    def _ensure_column(self, conn, column_name, column_type):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.table})")
        existing = {row[1] for row in cursor.fetchall()}
        if column_name not in existing:
            cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN {column_name} {column_type}")

    def insert(self, id, created_at, closed_at, name, table_name, status, to_go, amount_paid, total_amount, service_date=None):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"INSERT INTO {self.table} (id, created_at, closed_at, service_date, name, table_name, status, to_go, amount_paid, total_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (id, created_at, closed_at, service_date, name, table_name, status, to_go, amount_paid, total_amount)
            )

    def fetch_all(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            query = self._base_select_query() + " ORDER BY id ASC"
            cursor.execute(query)
            return cursor.fetchall()
            

    def delete_by_id(self, row_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.table} WHERE id = ?",
                (row_id,)
            )

    def edit_by_id(self, id, created_at, closed_at, name, table_name, status, to_go, amount_paid, total_amount, service_date=None):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {self.table}
                SET
                    created_at = ?,
                    closed_at = ?,
                    service_date = ?,
                    name = ?,
                    table_name = ?,
                    status = ?,
                    to_go = ?, 
                    amount_paid = ?,
                    total_amount = ?
                WHERE id = ? 
                """, 
                (created_at, closed_at, service_date, name, table_name, status, to_go, amount_paid, total_amount, id)
            )

    def set_table(self, table_name): 
        if not table_name.isidentifier(): 
            raise ValueError("Invalid table") 
        self.table = table_name 
        self.create_table()


    def search(self, filters):
        where_clauses = []
        params = []
        numeric_columns = {"total_amount", "amount_paid"}
        allowed_ops = {"=", ">", "<"}

        for column, value in filters.items():
            if column.endswith("_op"):
                continue
            if value is None:
                continue
            if callable(value):
                value = value()
            value_text = str(value).strip()
            if not value_text:
                continue

            if column in numeric_columns:
                operator = str(filters.get(f"{column}_op", "=")).strip()
                if operator not in allowed_ops:
                    operator = "="
                try:
                    numeric_value = float(value_text)
                except ValueError:
                    continue
                where_clauses.append(f"CAST({column} AS REAL) {operator} ?")
                params.append(numeric_value)
            else:
                where_clauses.append(f"{column} LIKE ?")
                params.append(f"%{value_text}%")

        query = self._base_select_query()

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY id ASC"

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        
    def delete_many_by_ids(self, ids):
        placeholders = ",".join("?" for _ in ids)
        query = f"DELETE FROM {self.table} WHERE id IN ({placeholders})"

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, ids)

    def bulk_update(self, ids, updates):
        set_clause = ", ".join(f"{col} = ?" for col in updates.keys())
        placeholders = ",".join("?" for _ in ids)

        query = f"""
            UPDATE {self.table}
            SET {set_clause}
            WHERE id IN ({placeholders})
        """

        values = list(updates.values()) + ids

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)


class MenuDatabase():
    def __init__(self, database, table):
        if not database.endswith(".db"):
            raise ValueError("Database name must end with .db")
        if not table.isidentifier():
            raise ValueError("Invalid table name")
        self.database = database
        self.table = table
        self.create_database()

    def connect(self):
        return sql.connect(self.database)

    def create_database(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (self.table,),
            )
            exists = cursor.fetchone() is not None

            if not exists:
                self._create_menu_schema(conn)
                return

            cursor.execute(f"PRAGMA table_info({self.table})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if "product_name" not in existing_columns:
                backup_name = f"{self.table}_legacy"
                cursor.execute(f"DROP TABLE IF EXISTS {backup_name}")
                cursor.execute(f"ALTER TABLE {self.table} RENAME TO {backup_name}")
                self._create_menu_schema(conn)
                self._migrate_legacy_menu_data(conn, backup_name)
                return

            if "is_active" not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
            if "product_type" not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN product_type TEXT NOT NULL DEFAULT 'Food'")
            if "created_at" not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN created_at TEXT")
                cursor.execute(
                    f"UPDATE {self.table} "
                    "SET created_at = datetime('now', 'localtime') "
                    "WHERE created_at IS NULL"
                )

    def _create_menu_schema(self, conn):
        cursor = conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                cost REAL NOT NULL DEFAULT 0,
                shortcuts TEXT NOT NULL DEFAULT '',
                color TEXT NOT NULL DEFAULT '',
                shape TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL DEFAULT 0,
                product_type TEXT NOT NULL DEFAULT 'Food',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )

    def _migrate_legacy_menu_data(self, conn, backup_name):
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({backup_name})")
        columns = {row[1] for row in cursor.fetchall()}
        if "name" not in columns:
            return
        cursor.execute(
            f"""
            INSERT INTO {self.table} (product_name, cost, shortcuts, color, shape, position, product_type, is_active)
            SELECT
                COALESCE(name, ''),
                0,
                '',
                '',
                '',
                0,
                'Food',
                1
            FROM {backup_name}
            WHERE COALESCE(name, '') != ''
            """
        )

    def insert(self, product_name, cost, shortcuts, color, shape, position, product_type):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.table}
                (product_name, cost, shortcuts, color, shape, position, product_type, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (product_name, cost, shortcuts, color, shape, position, product_type),
            )

    def fetch_all(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, product_name, cost, shortcuts, color, shape, position, product_type, is_active, created_at
                FROM {self.table}
                ORDER BY position ASC, id ASC
                """
            )
            return cursor.fetchall()

    def delete_by_id(self, row_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table} WHERE id = ?", (row_id,))

    def fetch_by_id(self, row_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, product_name, cost, shortcuts, color, shape, position, product_type, is_active, created_at
                FROM {self.table}
                WHERE id = ?
                """,
                (row_id,),
            )
            return cursor.fetchone()

    def update_by_id(self, row_id, product_name, cost, shortcuts, color, shape, position, product_type):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {self.table}
                SET product_name = ?, cost = ?, shortcuts = ?, color = ?, shape = ?, position = ?, product_type = ?
                WHERE id = ?
                """,
                (product_name, cost, shortcuts, color, shape, position, product_type, row_id),
            )


class TablesDatabase():
    def __init__(self, database, table, seed_from_orders=False):
        if not database.endswith(".db"):
            raise ValueError("Database name must end with .db")
        if not table.isidentifier():
            raise ValueError("Invalid table name")
        self.database = database
        self.table = table
        self.seed_from_orders = bool(seed_from_orders)
        self.create_database()

    def connect(self):
        return sql.connect(self.database)

    def create_database(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL UNIQUE,
                    position INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                )
                """
            )
            cursor.execute(f"PRAGMA table_info({self.table})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if "position" not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN position INTEGER NOT NULL DEFAULT 0")
            if "is_active" not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
            if "created_at" not in existing_columns:
                cursor.execute(f"ALTER TABLE {self.table} ADD COLUMN created_at TEXT")
                cursor.execute(
                    f"UPDATE {self.table} "
                    "SET created_at = datetime('now', 'localtime') "
                    "WHERE created_at IS NULL"
                )
            if self.seed_from_orders:
                self._seed_from_orders(conn)

    def _seed_from_orders(self, conn):
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {self.table}")
        count = int(cursor.fetchone()[0] or 0)
        if count > 0:
            return
        try:
            cursor.execute(
                """
                SELECT DISTINCT TRIM(table_name) AS table_name
                FROM orders
                WHERE COALESCE(TRIM(table_name), '') != ''
                ORDER BY table_name
                """
            )
            rows = cursor.fetchall()
        except sql.OperationalError:
            rows = []
        for idx, row in enumerate(rows):
            name = str(row[0]).strip()
            if not name:
                continue
            cursor.execute(
                f"""
                INSERT OR IGNORE INTO {self.table}
                (table_name, position, is_active)
                VALUES (?, ?, 1)
                """,
                (name, idx),
            )

    def insert(self, table_name, position):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.table}
                (table_name, position, is_active)
                VALUES (?, ?, 1)
                """,
                (table_name, position),
            )

    def fetch_all(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT id, table_name, position, is_active, created_at
                FROM {self.table}
                ORDER BY position ASC, id ASC
                """
            )
            return cursor.fetchall()

    def delete_by_id(self, row_id):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {self.table} WHERE id = ?", (row_id,))

    def update_by_id(self, row_id, table_name, position):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {self.table}
                SET table_name = ?, position = ?
                WHERE id = ?
                """,
                (table_name, position, row_id),
            )

