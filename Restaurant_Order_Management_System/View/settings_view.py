from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedLayout,
    QVBoxLayout,
)

from View.set_menu_view import SetMenuView
from View.set_tables_view import SetTablesView


class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        # SETTINGS PAGES
        self.set_menu_view = SetMenuView()
        self.set_tables_view = SetTablesView()
        self._build_ui()

    def _build_ui(self):
        # LEFT NAVIGATION
        self.navigation_list = QListWidget()
        self.navigation_list.addItem("Set Menu")
        self.navigation_list.addItem("Set Tables")
        self.navigation_list.setMaximumWidth(180)
        self.navigation_list.currentRowChanged.connect(self._on_row_changed)

        # RIGHT CONTENT STACK
        self.content_layout = QStackedLayout()
        self.content_layout.addWidget(self.set_menu_view)
        self.content_layout.addWidget(self.set_tables_view)

        content_container = QWidget()
        content_container.setLayout(self.content_layout)

        # MAIN LAYOUT
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.navigation_list)
        main_layout.addWidget(content_container, 1)
        self.setLayout(main_layout)

        self.navigation_list.setCurrentRow(0)

    def _on_row_changed(self, row):
        if row < 0:
            return
        self.content_layout.setCurrentIndex(row)
