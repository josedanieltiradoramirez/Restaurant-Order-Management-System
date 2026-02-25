import sqlite3
from datetime import datetime
import re
from Model.order import Order
from Model.dish import Dish
from Model.product import Product


class OrderRepository:
    def __init__(self, db_path="orders.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                closed_at TEXT NOT NULL,
                service_date TEXT,
                in_progress INTEGER NOT NULL DEFAULT 0,
                sent_status INTEGER NOT NULL DEFAULT 0,
                name TEXT,
                table_name TEXT,
                status TEXT NOT NULL,
                to_go INTEGER NOT NULL,
                additional_notes TEXT NOT NULL DEFAULT '',
                include_additional_notes_in_ticket INTEGER NOT NULL DEFAULT 0,
                amount_paid REAL NOT NULL,
                total_amount REAL NOT NULL
            )
            """
        )
        self._ensure_orders_column("service_date", "TEXT")
        self._ensure_orders_column("in_progress", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_orders_column("sent_status", "INTEGER NOT NULL DEFAULT 0")
        self._ensure_orders_column("additional_notes", "TEXT NOT NULL DEFAULT ''")
        self._ensure_orders_column(
            "include_additional_notes_in_ticket",
            "INTEGER NOT NULL DEFAULT 0",
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_dishes (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                display_name TEXT,
                status TEXT NOT NULL,
                sent_count INTEGER NOT NULL,
                to_go INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_id TEXT NOT NULL,
                name TEXT NOT NULL,
                display_name TEXT,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL,
                notes TEXT,
                is_custom INTEGER NOT NULL,
                FOREIGN KEY(dish_id) REFERENCES order_dishes(id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS order_counter_state (
                key TEXT PRIMARY KEY,
                last_order_id TEXT
            )
            """
        )
        self.conn.commit()

    def _ensure_orders_column(self, column_name, column_type):
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(orders)")
        existing = {row[1] for row in cur.fetchall()}
        if column_name not in existing:
            cur.execute(f"ALTER TABLE orders ADD COLUMN {column_name} {column_type}")

    def save_order(self, order):
        cur = self.conn.cursor()
        cur.execute("BEGIN")
        try:
            cur.execute("SELECT closed_at FROM orders WHERE id = ?", (order.id,))
            existing = cur.fetchone()
            existing_closed_at = existing["closed_at"] if existing else ""
            if order.status == "Closed":
                closed_at_value = existing_closed_at or datetime.now().isoformat()
            else:
                closed_at_value = ""
            cur.execute(
                """
                INSERT OR REPLACE INTO orders (
                    id, created_at, closed_at, service_date, in_progress, sent_status, name, table_name, status,
                    to_go, additional_notes, include_additional_notes_in_ticket, amount_paid, total_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.id,
                    order.created_at.isoformat(),
                    closed_at_value,
                    (order.service_date or order.created_at.date().isoformat()),
                    1 if (order.status == "In progress") else 0,
                    int(bool(getattr(order, "sent_status", False))),
                    order.name,
                    order.table,
                    order.status,
                    int(bool(order.to_go)),
                    str(getattr(order, "additional_notes", "") or ""),
                    int(bool(getattr(order, "include_additional_notes_in_ticket", False))),
                    float(order.amount_paid),
                    float(order.total_amount),
                ),
            )

            cur.execute("DELETE FROM order_items WHERE dish_id IN (SELECT id FROM order_dishes WHERE order_id = ?)", (order.id,))
            cur.execute("DELETE FROM order_dishes WHERE order_id = ?", (order.id,))

            for dish in order.dishes.values():
                cur.execute(
                    """
                    INSERT INTO order_dishes (
                        id, order_id, display_name, status, sent_count, to_go, total_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dish.id,
                        order.id,
                        dish.display_name,
                        dish.status,
                        int(dish.sent_count),
                        int(bool(dish.to_go)),
                        float(dish.total_amount),
                    ),
                )

                for product in dish.products.values():
                    cur.execute(
                        """
                        INSERT INTO order_items (
                            dish_id, name, display_name, price, quantity, notes, is_custom
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            dish.id,
                            product.name,
                            product.display_name,
                            float(product.price),
                            int(product.quantity),
                            product.notes,
                            int(bool(product.is_custom)),
                        ),
                    )
            self.conn.commit()
            # Save order ID to prevent counter reset when orders are deleted
            self._update_max_order_id(order.id)
        except Exception:
            self.conn.rollback()
            raise

    def save_closed_order(self, order):
        self.save_order(order)

    def load_open_orders(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id FROM orders WHERE status != ? ORDER BY created_at ASC",
            ("Closed",),
        )
        rows = cur.fetchall()
        orders = {}
        for row in rows:
            order = self.load_order(row["id"])
            if order:
                orders[order.id] = order
        return orders

    def delete_order(self, order_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self.conn.commit()
        # Save the deleted order ID as historical max to prevent counter reset
        self._update_max_order_id(order_id)

    def get_latest_order_id(self):
        cur = self.conn.cursor()
        # First check if there's a saved historical max
        cur.execute("SELECT last_order_id FROM order_counter_state WHERE key = 'max_order_id'")
        row = cur.fetchone()
        if row and row["last_order_id"]:
            historical_max = row["last_order_id"]
            # Also check current orders for the actual max
            cur.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 200")
            rows = cur.fetchall()
            current_max = None
            for cur_row in rows:
                order_id = cur_row["id"]
                if re.fullmatch(r"O\d{8}\d{4}", str(order_id or "")):
                    current_max = order_id
                    break
            # Return the max between historical and current
            if current_max and self._compare_order_ids(current_max, historical_max) >= 0:
                return current_max
            return historical_max
        # Fallback: look for orders in the table
        cur.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 200")
        rows = cur.fetchall()
        for row in rows:
            order_id = row["id"]
            if re.fullmatch(r"O\d{8}\d{4}", str(order_id or "")):
                return order_id
        return None

    def _compare_order_ids(self, id1, id2):
        """Compare two order IDs. Returns: >0 if id1 > id2, 0 if equal, <0 if id1 < id2"""
        m1 = re.fullmatch(r"O(\d{8})(\d{4})", str(id1).strip())
        m2 = re.fullmatch(r"O(\d{8})(\d{4})", str(id2).strip())
        if not m1 or not m2:
            return 0
        date_cmp = m1.group(1) - m2.group(1) if isinstance(m1.group(1), int) else int(m1.group(1)) - int(m2.group(1))
        if date_cmp != 0:
            return date_cmp
        num_cmp = int(m1.group(2)) - int(m2.group(2))
        return num_cmp

    def _update_max_order_id(self, order_id):
        """Save order_id as the max historical order ID if it's newer than the current max"""
        if not re.fullmatch(r"O\d{8}\d{4}", str(order_id).strip()):
            return
        cur = self.conn.cursor()
        cur.execute("SELECT last_order_id FROM order_counter_state WHERE key = 'max_order_id'")
        row = cur.fetchone()
        current_max = row["last_order_id"] if row else None
        if not current_max or self._compare_order_ids(order_id, current_max) >= 0:
            cur.execute(
                "INSERT OR REPLACE INTO order_counter_state (key, last_order_id) VALUES (?, ?)",
                ("max_order_id", order_id)
            )
            self.conn.commit()

    def load_order(self, order_id):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order_row = cur.fetchone()
        if not order_row:
            return None

        order = Order(order_row["id"])
        try:
            order.created_at = datetime.fromisoformat(order_row["created_at"])
        except Exception:
            order.created_at = datetime.now()
        order.service_date = (
            order_row["service_date"]
            if "service_date" in order_row.keys() and order_row["service_date"]
            else order.created_at.date().isoformat()
        )
        order.name = order_row["name"] or ""
        order.table = order_row["table_name"] or ""
        raw_status = order_row["status"] or "New"
        if raw_status == "Sent":
            raw_status = "In progress"
        order.status = raw_status
        order.sent_status = bool(order_row["sent_status"]) if "sent_status" in order_row.keys() else False
        order.to_go = bool(order_row["to_go"])
        order.additional_notes = (
            str(order_row["additional_notes"] or "")
            if "additional_notes" in order_row.keys()
            else ""
        )
        order.include_additional_notes_in_ticket = (
            bool(order_row["include_additional_notes_in_ticket"])
            if "include_additional_notes_in_ticket" in order_row.keys()
            else False
        )
        order.amount_paid = float(order_row["amount_paid"] or 0.0)

        cur.execute(
            "SELECT * FROM order_dishes WHERE order_id = ? ORDER BY rowid",
            (order.id,),
        )
        dish_rows = cur.fetchall()

        for dish_row in dish_rows:
            dish = Dish(dish_row["id"])
            dish.display_name = dish_row["display_name"] or ""
            dish.status = dish_row["status"] or "New"
            dish.sent_count = int(dish_row["sent_count"] or 0)
            dish.to_go = bool(dish_row["to_go"])

            cur.execute(
                "SELECT * FROM order_items WHERE dish_id = ? ORDER BY id",
                (dish.id,),
            )
            item_rows = cur.fetchall()

            for item_row in item_rows:
                product = Product(
                    item_row["name"],
                    float(item_row["price"]),
                    [],
                    item_row["notes"] or "",
                    bool(item_row["is_custom"]),
                    item_row["display_name"]
                    if item_row["display_name"] is not None
                    else item_row["name"],
                )
                product.quantity = int(item_row["quantity"] or 1)
                dish.products[product.name] = product

            dish.total()
            order.dishes[dish.id] = dish

        if order.dishes:
            order.active_dish = next(iter(order.dishes.values()))
        else:
            order.active_dish = None
        order.total()
        return order
