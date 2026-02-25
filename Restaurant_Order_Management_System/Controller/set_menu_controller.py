import json

from Infrastructure.connection_db import MenuDatabase


class SetMenuController:
    def __init__(self, view):
        self.view = view
        self.db = MenuDatabase("orders.db", "menu")

    def get_menu_rows(self):
        rows = self.db.fetch_all()
        formatted_rows = []
        for row in rows:
            row_list = list(row)
            if len(row_list) > 3:
                shortcuts_value = row_list[3]
                shortcuts_list = self._parse_shortcuts_to_list(shortcuts_value)
                row_list[3] = ", ".join(shortcuts_list)
            formatted_rows.append(tuple(row_list))
        return formatted_rows

    def add_menu_item(self, product_name, cost, shortcuts, color, shape, position, product_type):
        product_name = (product_name or "").strip()
        if not product_name:
            return False, "Product name is required."

        try:
            cost_value = float(str(cost).strip() or "0")
        except ValueError:
            return False, "Cost must be numeric."

        try:
            position_value = int(str(position).strip() or "0")
        except ValueError:
            return False, "Position must be an integer."

        ok, shortcuts_json_or_error = self._normalize_shortcuts(shortcuts)
        if not ok:
            return False, shortcuts_json_or_error

        normalized_type = self._normalize_product_type(product_type)

        self.db.insert(
            product_name=product_name,
            cost=cost_value,
            shortcuts=shortcuts_json_or_error,
            color=(color or "").strip(),
            shape=(shape or "").strip(),
            position=position_value,
            product_type=normalized_type,
        )
        self.refresh_table()
        return True, "Record added."

    def update_menu_item(self, row_id, product_name, cost, shortcuts, color, shape, position, product_type):
        product_name = (product_name or "").strip()
        if not product_name:
            return False, "Product name is required."

        try:
            cost_value = float(str(cost).strip() or "0")
        except ValueError:
            return False, "Cost must be numeric."

        try:
            position_value = int(str(position).strip() or "0")
        except ValueError:
            return False, "Position must be an integer."

        ok, shortcuts_json_or_error = self._normalize_shortcuts(shortcuts)
        if not ok:
            return False, shortcuts_json_or_error

        normalized_type = self._normalize_product_type(product_type)

        self.db.update_by_id(
            row_id=row_id,
            product_name=product_name,
            cost=cost_value,
            shortcuts=shortcuts_json_or_error,
            color=(color or "").strip(),
            shape=(shape or "").strip(),
            position=position_value,
            product_type=normalized_type,
        )
        self.refresh_table()
        return True, "Record updated."

    def refresh_table(self):
        if hasattr(self.view, "refresh_table"):
            self.view.refresh_table()

    def remove_registry_button_clicked(self):
        selected_ids = self.view.get_selected_menu_ids()
        if not selected_ids:
            self.view.show_warning("Selection", "Select at least one record to remove.")
            return
        for row_id in selected_ids:
            self.db.delete_by_id(row_id)
        self.refresh_table()
    
    def edit_registry_button_clicked(self):
        selected_rows = self.view.get_selected_menu_rows()
        if not selected_rows:
            self.view.show_warning("Selection", "Select one record to edit.")
            return
        if len(selected_rows) > 1:
            self.view.show_warning("Selection", "Select only one record to edit.")
            return
        row = selected_rows[0]
        self.view.show_edit_menu_item_modal(row)

    def _normalize_shortcuts(self, raw_value):
        shortcuts_list = self._parse_shortcuts_to_list(raw_value)
        for item in shortcuts_list:
            if not isinstance(item, str):
                return False, "Shortcuts only accepts text."
        return True, json.dumps(shortcuts_list, ensure_ascii=False)

    def _parse_shortcuts_to_list(self, raw_value):
        if raw_value is None:
            return []

        if isinstance(raw_value, (list, tuple)):
            return [str(item).strip() for item in raw_value if str(item).strip()]

        text = str(raw_value).strip()
        if not text:
            return []

        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

        return [item.strip() for item in text.split(",") if item.strip()]

    def _normalize_product_type(self, product_type):
        value = str(product_type or "").strip().lower()
        if value in {"drink", "bebida"}:
            return "Drink"
        return "Food"


