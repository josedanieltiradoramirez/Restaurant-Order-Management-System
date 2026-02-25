from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QTableView,
    QMessageBox,
    QDialog,
)

from Model.table_model import TableModel
from Controller.set_tables_controller import SetTablesController
from View.new_table_view import NewTableView


class SetTablesView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = SetTablesController(self)

        # MAIN TABLE
        self.tables_table = QTableView()
        self.tables_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tables_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        data = self.controller.get_table_rows()
        headers = ["ID", "Table name", "Position", "Active", "Created at"]

        self.main_model = TableModel(data, headers)
        self.tables_table.setModel(self.main_model)

        self.add_registry_button = QPushButton("Add registry")
        self.add_registry_button.clicked.connect(self.add_registry_button_clicked)
        self.remove_registry_button = QPushButton("Remove registry")
        self.remove_registry_button.clicked.connect(self.remove_registry_button_clicked)
        self.remove_registry_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #fee2e2;"
            "  color: #991b1b;"
            "  border: 1px solid #fecaca;"
            "  border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "  background-color: #fecaca;"
            "}"
            "QPushButton:pressed {"
            "  background-color: #fca5a5;"
            "}"
            "QPushButton:disabled {"
            "  background-color: #f3f4f6;"
            "  color: #9ca3af;"
            "  border: 1px solid #e5e7eb;"
            "}"
        )
        self.edit_registry_button = QPushButton("Edit registry")
        self.edit_registry_button.clicked.connect(self.edit_registry_button_clicked)

        # ACTION BUTTONS
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_registry_button)
        buttons_layout.addWidget(self.remove_registry_button)
        buttons_layout.addWidget(self.edit_registry_button)

        # MAIN LAYOUT
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.tables_table)
        self.main_layout.addLayout(buttons_layout)
        self.setLayout(self.main_layout)

    def add_registry_button_clicked(self):
        modal = QDialog(self)
        modal.setWindowTitle("New table")
        modal.resize(500, 220)
        new_table_view = NewTableView(self.controller, modal)
        modal_layout = QVBoxLayout(modal)
        modal_layout.addWidget(new_table_view)
        modal.exec()

    def remove_registry_button_clicked(self):
        self.controller.remove_registry_button_clicked()

    def edit_registry_button_clicked(self):
        self.controller.edit_registry_button_clicked()

    def show_edit_table_item_modal(self, row_data):
        modal = QDialog(self)
        modal.setWindowTitle("Edit table")
        modal.resize(500, 220)
        new_table_view = NewTableView(self.controller, modal, row_data=row_data)
        modal_layout = QVBoxLayout(modal)
        modal_layout.addWidget(new_table_view)
        modal.exec()

    def refresh_table(self):
        rows = self.controller.get_table_rows()
        self.main_model.update_data(rows)

    def get_selected_table_rows(self):
        indexes = self.tables_table.selectionModel().selectedRows()
        selected = []
        for index in sorted(indexes, key=lambda i: i.row()):
            row_idx = index.row()
            if 0 <= row_idx < len(self.main_model._data):
                selected.append(self.main_model._data[row_idx])
        return selected

    def get_selected_table_ids(self):
        selected_ids = []
        for row in self.get_selected_table_rows():
            try:
                selected_ids.append(int(row[0]))
            except (ValueError, TypeError, IndexError):
                continue
        return selected_ids

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

