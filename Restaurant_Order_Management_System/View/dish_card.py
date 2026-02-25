from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QCheckBox,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent

class DishCard(QWidget):
    remove_button_signal = pyqtSignal(str)
    send_button_signal = pyqtSignal(str)
    to_go_changed_signal = pyqtSignal(str, bool)
    clicked = pyqtSignal(str)

    def __init__(self, dish):
        super().__init__()
        self.dish = dish
        self.id = dish.id
        self.name = dish.display_name
        self.send_button = None
        self.remove_button = None
        self.to_go_checkbox = None
        self.setMinimumWidth(160)
        self.setMinimumHeight(64)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.init_ui()

    def init_ui(self):
        
        #-------------- NAME --------------
        name_label = QLabel(self.name)
        name_label.setStyleSheet("color: #1f1f1f;")
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        status_label = QLabel(f"- {self._display_status()}")
        status_label.setFont(QFont("Segoe UI", 9))
        status_label.setStyleSheet("color: #6b7280;")
        #-------------- TOTAL / STATUS --------------
        total_label = QLabel(f"Total: {self.dish.total_amount}")
        total_label.setFont(QFont("Segoe UI", 9))
        total_label.setStyleSheet("color: #6b7280;")
        self.to_go_checkbox = QCheckBox("")
        self.to_go_checkbox.setChecked(self.dish.to_go)
        self.to_go_checkbox.setStyleSheet("color: #111111;")
        self.to_go_checkbox.toggled.connect(self.to_go_checkbox_toggled)
        to_go_text_label = QLabel("To go")
        to_go_text_label.setStyleSheet("color: #111111;")
        to_go_text_label.setFont(QFont("Segoe UI", 9))
        #-------------- ADD --------------
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_button_clicked)
        self.send_button.setFixedHeight(22)
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_button_clicked)
        self.remove_button.setFixedHeight(22)

        #-------------- Layout --------------
        dish_meta_layout = QHBoxLayout()
        dish_meta_layout.setContentsMargins(0, 0, 0, 0)
        dish_meta_layout.setSpacing(6)
        dish_meta_layout.addWidget(name_label)
        dish_meta_layout.addWidget(status_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(6)
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.remove_button)

        controls_layout = QVBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(2)
        controls_layout.addLayout(buttons_layout)

        header_layout = QHBoxLayout()
        header_layout.addLayout(dish_meta_layout)
        header_layout.addStretch(1)
        header_layout.addLayout(controls_layout)

        bottom_row_layout = QHBoxLayout()
        bottom_row_layout.setContentsMargins(0, 0, 0, 0)
        bottom_row_layout.setSpacing(6)
        bottom_row_layout.addWidget(total_label)
        bottom_row_layout.addStretch(1)
        bottom_row_layout.addWidget(to_go_text_label)
        bottom_row_layout.addWidget(self.to_go_checkbox)

        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addLayout(bottom_row_layout)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(4)

        self.setLayout(main_layout)
        self.setObjectName("card")
        self.setStyleSheet("""
            QWidget#card {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
            }
            QWidget#card[selected="true"] {
                background-color: #d1d5db;
                border: 1px solid #6b7280;
            }
            QWidget#card[selected="false"]:hover {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
            }

            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                font-size: 9pt;
            }

            QPushButton:hover {
                background-color: #e5e7eb;
            }

            QPushButton:pressed {
                background-color: #d1d5db;
            }
        """)
        self.remove_button.setStyleSheet(
            "QPushButton {"
            "  background-color: #fee2e2;"
            "  color: #991b1b;"
            "  border: 1px solid #fecaca;"
            "  border-radius: 4px;"
            "  font-size: 9pt;"
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

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def remove_button_clicked(self):
        self.remove_button_signal.emit(self.id)

    def send_button_clicked(self):
        self.send_button_signal.emit(self.id)

    def to_go_checkbox_toggled(self, checked):
        self.to_go_changed_signal.emit(self.id, checked)

    def _display_status(self):
        status = (self.dish.status or "").strip().lower()
        return "Sent" if status == "sent" else "New"

    def set_interaction_enabled(self, enabled: bool):
        if self.send_button is not None:
            self.send_button.setEnabled(enabled)
        if self.remove_button is not None:
            self.remove_button.setEnabled(enabled)
        if self.to_go_checkbox is not None:
            self.to_go_checkbox.setEnabled(enabled)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.id)
        super().mousePressEvent(event)
        

