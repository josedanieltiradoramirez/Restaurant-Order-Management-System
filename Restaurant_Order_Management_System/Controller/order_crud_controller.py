from Model.table_model import TableModel
from Infrastructure.connection_db import Database
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QItemSelectionModel

class OrderCrudController():
    def __init__(self, view):
        self.view = view
        self.db = Database("orders.db","orders")

    def show_table(self, data, headers, table_view, layout):
        model = TableModel(data, headers)
        table_view.setModel(model)
        tab2_layout = layout()
        tab2_layout.addWidget(table_view)
        #tabs.addTab(tab_database_view, "Database view")

    def button_add_registry_clicked(self):
        name = self.view.tab2_form_line_name.text()
        labels = self.view.tab2_form_line_labels.text()
        date = self.view.tab2_form_line_date.text()
        body = self.view.tab2_form_line_body.text()
        self.db.insert(name, labels, date, body)
        self.refresh_table()

    def button_delete_clicked(self,row):
        model = self.view.table_view.model()
        row_id = model._data[row][0]

        confirm = QMessageBox.question(
            self.view, "Confirm delete", f"Delete record ID {row_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No

        )

        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        self.db.delete_by_id(row_id)
        self.refresh_table()

    def button_edit_clicked(self,row):
        model = self.view.table_view.model()
        row_id = model._data[row][0]
        name = self.view.tab2_form_line_name.text()
        labels = self.view.tab2_form_line_labels.text()
        date = self.view.tab2_form_line_date.text()
        body = self.view.tab2_form_line_body.text()
        self.db.edit_by_id(row_id, name, labels, date, body)
        self.refresh_table()

    
    def refresh_table(self):
        data = self.db.fetch_all()
        #model = TableModel(
        #    data,
        #    ["ID", "Name", "Labels", "Date", "Body"]
        #)
        #self.view.table_view.setModel(model)
        #
        self.view.main_model.update_data(data)

    def search(self, filters):
        data = self.db.search(filters)

        #model = TableModel(
        #    data,
        #    ["ID", "Name", "Labels", "Date", "Body"]
        #)
        #self.view.table_view.setModel(model)
        self.view.main_model.update_data(data)

    ## SELECTION TABLE CONTROLLER
    def update_selection_table(self):
        indexes = self.view.table_view.selectionModel().selectedRows()
        model = self.view.table_view.model()

        rows = []

        for index in indexes:
            row = index.row()
            rows.append([
                model._data[row][0],  # ID
                model._data[row][1],  # Name
                model._data[row][2],  # Labels
                model._data[row][3],  # Date
                model._data[row][4],  # Body
            ])

        self.view.selection_table_model.update_data(rows)

    def selected_double_click(self, index):
        row_id = self.view.selection_table_model._data[index.row()][0]

        for i, row in enumerate(self.view.main_model._data):
            if row[0] == row_id:
                self.view.table_view.selectRow(i)
                self.view.table_view.scrollTo(
                    self.view.main_model.index(i, 0)
                )
                break

    def delete_selected(self):
        rows = self.view.selection_table_model._data

        if not rows:
            QMessageBox.warning(
                self.view,
                "Warning",
                "No selected items"
            )
            return

        ids = [row[0] for row in rows]

        confirm = QMessageBox.question(
            self.view,
            "Confirm delete",
            f"Delete {len(ids)} selected items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.db.delete_many_by_ids(ids)

        self.refresh_table()
        self.view.selection_table_model.update_data([])
        self.view.table_view.clearSelection()

    def bulk_edit_clicked(self, ids, updates):
        self.db.bulk_update(ids, updates)
        self.refresh_table()
        self.view.selection_table_model.update_data([])
        self.view.table_view.clearSelection()

