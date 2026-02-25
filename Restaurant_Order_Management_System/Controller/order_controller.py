import json
from datetime import date

from Infrastructure.connection_db import MenuDatabase, TablesDatabase
from Model.order import Order
from Model.order_number_genetator import OrderNumberGenerator


class OrderController():
    def __init__(self, order_repository):
        self.orders = {}
        self.active_order_id = None
        self.dishes = {}
        self.active_dish_id = None
        self.order_number_generator = OrderNumberGenerator()
        self.custom_product_counter = 0
        self.order_repository = order_repository
        try:
            latest_order_id = self.order_repository.get_latest_order_id()
            self.order_number_generator.seed_from_order_id(latest_order_id)
        except Exception:
            pass

    def get_orders(self):
        return self.orders

    def set_orders(self, orders):
        self.orders = orders or {}
        self.active_order_id = None
        return self.orders

    def set_single_order(self, order):
        if not order:
            self.orders = {}
            self.active_order_id = None
            return None
        self.orders = {order.id: order}
        self.active_order_id = order.id
        if order.dishes:
            order.active_dish = next(iter(order.dishes.values()))
        else:
            order.active_dish = None
        return order

    def get_active_order(self):
        if self.active_order_id is None:
            return None
        return self.orders.get(self.active_order_id)

    def get_active_dish(self):
        order = self.get_active_order()
        if not order:
            return None
        return order.active_dish

    def new_order_button_clicked(self):
        #order_id = str(uuid.uuid4())
        #new_order = Order(order_id)
        #new_order.name = "Generic"
        order_id = self.order_number_generator.next()
        self.orders[order_id] = Order(order_id)
        self.order_selected(order_id)
        #self.orders[order_id] = new_order
        #self.order_selected(order_id)
        return self.orders[order_id]
        
        

        return new_order

        

    def new_dish_button_clicked(self):
        order = self.get_active_order()
        if not order:
            return None
        new_dish = order.add_dish()
        new_dish.set_to_go(order.to_go)
        self._refresh_order_status_from_dishes(order)
        return new_dish


    def remove_order_clicked(self, order_id):
        was_active = self.active_order_id == order_id
        try:
            self.order_repository.delete_order(order_id)
        except Exception:
            pass
        if order_id in self.orders:
            del self.orders[order_id]

        if was_active:
            self.active_order_id = None
            return None

        return self.get_active_order()
        
    def remove_dish_clicked(self, dish_id):
        order = self.get_active_order()
        if not order:
            return None

        was_active = order.active_dish and order.active_dish.id == dish_id
        order.remove_dish(dish_id)
        self._refresh_order_status_from_dishes(order)

        if not was_active:
            return order.active_dish

        if order.dishes:
            next_dish = next(iter(order.dishes.values()))
            order.active_dish = next_dish
            return next_dish

        order.active_dish = None
        return None

    def remove_product_clicked(self, product_name):
        order = self.get_active_order()
        if not order or not order.active_dish:
            return None
        dish = order.active_dish
        dish.remove_product(product_name)
        order.total()
        return dish

    def product_quantity_changed(self, product_name, quantity: int):
        order = self.get_active_order()
        if not order or not order.active_dish:
            return None
        dish = order.active_dish
        dish.set_product_quantity(product_name, quantity)
        order.total()
        return dish

    def product_price_changed(self, product_name, price: float):
        order = self.get_active_order()
        if not order or not order.active_dish:
            return None
        dish = order.active_dish
        if product_name not in dish.products:
            return None
        dish.products[product_name].price = price
        dish.total()
        order.total()
        return dish

    def product_name_changed(self, old_name: str, new_name: str) -> bool:
        order = self.get_active_order()
        if not order or not order.active_dish:
            return False
        dish = order.active_dish
        if old_name not in dish.products:
            return False
        product = dish.products[old_name]
        if getattr(product, "is_custom", False):
            product.display_name = new_name
            return True
        ok = dish.rename_product(old_name, new_name)
        if ok:
            order.total()
        return ok

    def product_card_add_button_clicked(self, product):
        order = self.orders.get(self.active_order_id)
        if not order or not order.active_dish:
            return None
        
        order.active_dish.add_product(product)
        order.total()
        return order.active_dish
            
    def order_selected(self, order_id:str):
        self.active_order_id = order_id
        order = self.orders[order_id]
        if order.active_dish and order.active_dish.id in order.dishes:
            return order

        if order.dishes:
            order.active_dish = next(iter(order.dishes.values()))
        else:
            order.active_dish = None
        return order

    def dish_selected(self, dish_id:str):
        self.orders[self.active_order_id].set_active_dish(dish_id)
        dish = self.orders[self.active_order_id].dishes[dish_id]
        return dish

    def fill_order_form(self, order: Order):
        if not order:
            return {"name": "", "table": ""}
        return {"name": order.name, "table": order.table}
    
    def close_order_button_clicked(self):
        order = self.get_active_order()
        if not order:
            return None
        order.set_status("Closed")
        self.order_repository.save_order(order)
        return order

    def reopen_order_button_clicked(self):
        order = self.get_active_order()
        if not order:
            return None
        if order.status != "Closed":
            return order
        # Reopen transitions the ticket out of "Closed" and recalculates
        # the live status from current dishes.
        order.set_status("New")
        return order

    def clear_active_selection(self):
        self.active_order_id = None

    def next_custom_product_key(self):
        self.custom_product_counter += 1
        return f"producto_libre_{self.custom_product_counter}"

    def send_order_button_clicked(self):
        order = self.get_active_order()
        if not order:
            return
        for dish in order.dishes.values():
            if dish.status != "Sent":
                dish.sent_count_increase()
            dish.set_status("Sent")
        self._refresh_sent_status_from_dishes(order)

    def set_active_order_status(self, status: str):
        order = self.get_active_order()
        if not order:
            return None
        if order.status == "Closed":
            return order
        normalized = (status or "").strip().title()
        if normalized not in {"New", "In Progress"}:
            return order
        if normalized == "In Progress":
            order.set_status("In progress")
            return order
        order.set_status("New")
        return order

    def send_dish_button_clicked(self, dish_id):
        order = self.get_active_order()
        if not order or dish_id not in order.dishes:
            return None
        dish = order.dishes[dish_id]
        if dish.status != "Sent":
            dish.sent_count_increase()
        dish.set_status("Sent")
        self._refresh_sent_status_from_dishes(order)
        return dish

    def _refresh_order_status_from_dishes(self, order):
        # Order status is now independent from dish sent state.
        if not order:
            return
        if order.status not in {"New", "In progress", "Closed"}:
            order.set_status("New")

    def _refresh_sent_status_from_dishes(self, order):
        if not order:
            return
        if not order.dishes:
            order.set_sent_status(False)
            return
        all_sent = all(dish.status == "Sent" for dish in order.dishes.values())
        order.set_sent_status(all_sent)

    def register_form_data(
        self,
        name,
        table,
        to_go,
        amount_paid,
        additional_notes="",
        include_additional_notes_in_ticket=False,
        service_date="",
    ):
        order = self.get_active_order()
        if not order:
            return
        order.set_name(name)
        order.set_table(table)
        order.set_to_go(to_go)
        order.set_additional_notes(additional_notes)
        order.set_include_additional_notes_in_ticket(include_additional_notes_in_ticket)
        normalized_service_date = self._normalize_service_date(service_date, getattr(order, "service_date", ""))
        order.set_service_date(normalized_service_date)
        order.set_amount_paid(amount_paid)
        self._sync_dishes_to_go_from_order(order)

    def _normalize_service_date(self, value, fallback=""):
        text = str(value or "").strip()
        if not text:
            return str(fallback or date.today().isoformat())
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            return str(fallback or date.today().isoformat())

    def dish_to_go_changed(self, dish_id, to_go):
        order = self.get_active_order()
        if not order or dish_id not in order.dishes:
            return None
        dish = order.dishes[dish_id]
        dish.set_to_go(to_go, overridden=True)
        return dish

    def apply_order_to_go_to_all_dishes(self, to_go):
        order = self.get_active_order()
        if not order:
            return
        for dish in order.dishes.values():
            dish.set_to_go(to_go)
            dish.to_go_overridden = False

    def _sync_dishes_to_go_from_order(self, order):
        if not order:
            return
        for dish in order.dishes.values():
            if not dish.to_go_overridden:
                dish.set_to_go(order.to_go)

    def persist_active_order(self):
        order = self.get_active_order()
        if not order:
            return None
        self.order_repository.save_order(order)
        return order

    def is_order_editable(self, order, unlocked_closed_order_ids=None):
        if not order:
            return False
        unlocked = unlocked_closed_order_ids or set()
        return order.status != "Closed" or order.id in unlocked

    def get_menu_products_for_view(self, db_path="orders.db"):
        try:
            rows = MenuDatabase(db_path, "menu").fetch_all()
        except Exception:
            rows = []

        products = []
        for row in rows:
            if len(row) < 9 or not bool(row[8]):
                continue
            item = self._menu_row_to_product_data(row)
            if item:
                products.append(item)

        products.append(
            {
                "name": "Custom product",
                "price": 0,
                "notes_shortcuts": [],
                "shape": "Rectangle",
                "is_custom": True,
            }
        )
        return products

    def get_active_table_names_for_view(self, db_path="orders.db"):
        try:
            rows = TablesDatabase(db_path, "tables").fetch_all()
        except Exception:
            rows = []

        names = []
        for row in rows:
            if len(row) < 4 or not bool(row[3]):
                continue
            table_name = str(row[1]).strip()
            if table_name and table_name not in names:
                names.append(table_name)

        if not names:
            names = ["Table 1", "Table 2", "Table 3", "Table 4"]
        return names

    def _menu_row_to_product_data(self, row):
        try:
            name = str(row[1]).strip()
            price = float(row[2]) if row[2] is not None else 0.0
            shortcuts_raw = row[3]
            color = str(row[4]).strip() if row[4] is not None else ""
            shape = str(row[5]).strip() if row[5] is not None else "Rectangle"
        except (ValueError, TypeError, IndexError):
            return None

        if not name:
            return None

        return {
            "name": name,
            "price": price,
            "notes_shortcuts": self._parse_shortcuts(shortcuts_raw),
            "color": color,
            "shape": shape,
        }

    def _parse_shortcuts(self, shortcuts_raw):
        if shortcuts_raw is None:
            return []
        if isinstance(shortcuts_raw, list):
            return [str(item).strip() for item in shortcuts_raw if str(item).strip()]

        text = str(shortcuts_raw).strip()
        if not text:
            return []

        if text.startswith("[") and text.endswith("]"):
            try:
                decoded = json.loads(text)
                if isinstance(decoded, list):
                    return [str(item).strip() for item in decoded if str(item).strip()]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        return [item.strip() for item in text.split(",") if item.strip()]
