import sqlite3

from Infrastructure.connection_db import TablesDatabase


class SetTablesController:
    def __init__(self, view):
        self.view = view
        self.db = TablesDatabase("orders.db", "tables")

    def get_table_rows(self):
        return self.db.fetch_all()

    def add_table_item(self, table_name, position):
        table_name = (table_name or "").strip()
        if not table_name:
            return False, "Table name is required."

        try:
            position_value = int(str(position).strip() or "0")
        except ValueError:
            return False, "Position must be an integer."

        try:
            self.db.insert(table_name=table_name, position=position_value)
        except sqlite3.IntegrityError:
            return False, "A table with that name already exists."

        self.refresh_table()
        return True, "Record added."

    def update_table_item(self, row_id, table_name, position):
        table_name = (table_name or "").strip()
        if not table_name:
            return False, "Table name is required."

        try:
            position_value = int(str(position).strip() or "0")
        except ValueError:
            return False, "Position must be an integer."

        try:
            self.db.update_by_id(
                row_id=row_id,
                table_name=table_name,
                position=position_value,
            )
        except sqlite3.IntegrityError:
            return False, "A table with that name already exists."

        self.refresh_table()
        return True, "Record updated."

    def refresh_table(self):
        if hasattr(self.view, "refresh_table"):
            self.view.refresh_table()

    def remove_registry_button_clicked(self):
        selected_ids = self.view.get_selected_table_ids()
        if not selected_ids:
            self.view.show_warning("Selection", "Select at least one record to remove.")
            return
        for row_id in selected_ids:
            self.db.delete_by_id(row_id)
        self.refresh_table()

    def edit_registry_button_clicked(self):
        selected_rows = self.view.get_selected_table_rows()
        if not selected_rows:
            self.view.show_warning("Selection", "Select one record to edit.")
            return
        if len(selected_rows) > 1:
            self.view.show_warning("Selection", "Select only one record to edit.")
            return
        row = selected_rows[0]
        self.view.show_edit_table_item_modal(row)


