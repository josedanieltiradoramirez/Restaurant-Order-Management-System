
from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                            QPushButton, QLineEdit, QHBoxLayout, 
                            QVBoxLayout, QComboBox, QTabWidget, QTableView,
                            QFormLayout, QMessageBox, QGroupBox, QDateEdit, QCheckBox,
                            QDialog, QPlainTextEdit)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QDate
from Infrastructure.connection_db import MenuDatabase
from Infrastructure.order_repository import OrderRepository
from Model.table_model import TableModel
from Model.ticket_body import TicketBody
from Controller.order_crud_controller import OrderCrudController
from Controller.order_controller import OrderController
from View.order_management_view import OrderManagementView
from Controller.set_menu_controller import SetMenuController
from View.new_product_view import NewProductView

class SetMenuView(QWidget):
    def __init__(self):
            super().__init__()
            self.controller = SetMenuController(self)

            # MAIN TABLE
            self.menu_table = QTableView()
            self.menu_table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
            self.menu_table.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
            data = self.controller.get_menu_rows()
            headers = ["ID", "Product name", "Cost", "Shortcuts", "Color", "Shape", "Position", "Type", "Active", "Created at"]

            self.main_model = TableModel(data, headers)
            self.menu_table.setModel(self.main_model)

            # ACTION BUTTONS
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

            buttons_layout = QHBoxLayout()
            buttons_layout.addWidget(self.add_registry_button)
            buttons_layout.addWidget(self.remove_registry_button)
            buttons_layout.addWidget(self.edit_registry_button)

            # MAIN LAYOUT
            self.main_layout = QVBoxLayout()
            self.main_layout.addWidget(self.menu_table)
            self.main_layout.addLayout(buttons_layout)
            self.setLayout(self.main_layout)


    def add_registry_button_clicked(self):
        modal = QDialog(self)
        modal.setWindowTitle("New product")
        modal.resize(1200, 760)
        new_product_view = NewProductView(self.controller, modal)
        modal_layout = QVBoxLayout(modal)
        modal_layout.addWidget(new_product_view)
        modal.exec()

    def remove_registry_button_clicked(self):
        self.controller.remove_registry_button_clicked()
    
    def edit_registry_button_clicked(self):
        self.controller.edit_registry_button_clicked()

    def show_edit_menu_item_modal(self, row_data):
         modal = QDialog(self)
         modal.setWindowTitle("Edit product")
         modal.resize(1200, 760)
         new_product_view = NewProductView(self.controller, modal, row_data=row_data)
         modal_layout = QVBoxLayout(modal)
         modal_layout.addWidget(new_product_view)
         modal.exec()

    def refresh_table(self):
        rows = self.controller.get_menu_rows()
        self.main_model.update_data(rows)

    def get_selected_menu_rows(self):
        indexes = self.menu_table.selectionModel().selectedRows()
        selected = []
        for index in sorted(indexes, key=lambda i: i.row()):
            row_idx = index.row()
            if 0 <= row_idx < len(self.main_model._data):
                selected.append(self.main_model._data[row_idx])
        return selected

    def get_selected_menu_ids(self):
        selected_ids = []
        for row in self.get_selected_menu_rows():
            try:
                selected_ids.append(int(row[0]))
            except (ValueError, TypeError, IndexError):
                continue
        return selected_ids

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)
         

