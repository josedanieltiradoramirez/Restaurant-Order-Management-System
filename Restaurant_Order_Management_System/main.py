import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel,
                             QLineEdit, QTextEdit, QPushButton, 
                             QStackedLayout, QFormLayout,  QVBoxLayout, QHBoxLayout, 
                             QComboBox, QDateEdit, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QPixmap, QFont
from View.order_management_view import OrderManagementView
from Controller.order_controller import OrderController
from Infrastructure.order_repository import OrderRepository
from View.order_crud_view import OrderCrudView
from View.settings_view import SettingsView

class EmptyWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.startUI()
        


    def startUI(self):
        self.setGeometry(100,100,250,250)
        self.setWindowTitle("Order Management System")
        self.generate_window()
        self.show()
 

    def generate_window(self):

        # RIGHT SIDE PANEL MENU
        button_1 = QPushButton("Order Management")
        button_1.clicked.connect(self.change_window)
        button_2 = QPushButton("Order Database")
        button_2.clicked.connect(self.change_window)
        button_3 = QPushButton("Settings")
        button_3.clicked.connect(self.change_window)
        right_side_menu_layout = QVBoxLayout()
        right_side_menu_layout.addWidget(button_1)
        right_side_menu_layout.addWidget(button_2)
        right_side_menu_layout.addWidget(button_3)


        # PAGES CONTENT
        repository = OrderRepository("orders.db")
        order_management_controller = OrderController(repository)
        self.order_management_view = OrderManagementView(order_management_controller)
        open_orders = repository.load_open_orders()
        order_management_controller.set_orders(open_orders)
        self.order_management_view.render_orders()
        self.order_crud_view = OrderCrudView()
        # Link CRUD view to management view so it can trigger refreshes
        self.order_management_view.order_crud_view = self.order_crud_view
        self.settings_view = SettingsView()
        
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self._page_with_title("Order Management", self.order_management_view))
        self.stacked_layout.addWidget(self._page_with_title("Order Database", self.order_crud_view))
        self.stacked_layout.addWidget(self._page_with_title("Settings", self.settings_view))

        # MAIN LAYOUT
        main_layout = QHBoxLayout()
        main_layout.addLayout(right_side_menu_layout)
        main_layout.addLayout(self.stacked_layout)
        self.setLayout(main_layout)

    # METHODS
    def _page_with_title(self, title, view):
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        container_layout.setSpacing(8)
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #f9fafb;")
        container_layout.addWidget(title_label)
        container_layout.addWidget(view)
        return container

    def change_window(self):
        button = self.sender()
        if button.text().lower() =='order management':
            if self.order_management_view and hasattr(self.order_management_view, "load_products_from_menu_database"):
                self.order_management_view.load_products_from_menu_database()
            if self.order_management_view and hasattr(self.order_management_view, "load_tables_from_database"):
                self.order_management_view.load_tables_from_database()
            if self.order_management_view and hasattr(self.order_management_view, "refresh_orders_from_database"):
                self.order_management_view.refresh_orders_from_database()
            self.stacked_layout.setCurrentIndex(0)
        elif button.text().lower() =='order database':
            # Refresh the CRUD table when entering the tab
            if self.order_crud_view and hasattr(self.order_crud_view, "refresh_all_orders"):
                self.order_crud_view.refresh_all_orders()
            self.stacked_layout.setCurrentIndex(1)
        elif button.text().lower() =='settings':
            self.stacked_layout.setCurrentIndex(2)
            


        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = EmptyWindow()
    sys.exit(app.exec())

