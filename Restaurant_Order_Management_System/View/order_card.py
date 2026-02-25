from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent

class OrderCard(QWidget):
    remove_button_signal = pyqtSignal(str)
    toggle_status_button_signal = pyqtSignal(str)
    clicked = pyqtSignal(str)

    def __init__(self, order):
        super().__init__()
        self.order = order
        self.id = order.id
        self.name = order.name
        self.status = order.status
        self.status_label = None
        self.sent_status_label = None
        self.created_at_label = None
        self.to_go_label = None
        self.remove_button = None
        self.toggle_status_button = None
        
        self.setMinimumWidth(160)
        self.setMinimumHeight(96)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.init_ui()

    def init_ui(self):
        
        #-------------- NAME --------------
        name_label = QLabel(self.id)
        name_label.setStyleSheet("color: #1f1f1f;")
        name_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        #-------------- STATUS --------------
        self.status_label = QLabel(f"- {self.status}")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet("color: #6b7280;")
        self.sent_status_label = QLabel(self._sent_status_text())
        self.sent_status_label.setFont(QFont("Segoe UI", 9))
        self.sent_status_label.setStyleSheet("color: #6b7280;")
        self.created_at_label = QLabel(self._time_table_text())
        self.created_at_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.created_at_label.setStyleSheet("color: #111827;")
        self.to_go_label = QLabel(self._to_go_text())
        self.to_go_label.setFont(QFont("Segoe UI", 9))
        self.to_go_label.setStyleSheet("color: #6b7280;")
        self.to_go_label.setMinimumHeight(16)
        self.to_go_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        #-------------- ADD --------------
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_button_clicked)
        self.remove_button.setFixedHeight(22)
        self.remove_button.setEnabled(self.status != "Closed")
        self.toggle_status_button = QPushButton(self._toggle_status_button_text())
        self.toggle_status_button.clicked.connect(self.toggle_status_button_clicked)
        self.toggle_status_button.setFixedHeight(22)
        self.toggle_status_button.setEnabled(self.status != "Closed")

        #-------------- Layout --------------
        order_meta_layout = QHBoxLayout()
        order_meta_layout.setContentsMargins(0, 0, 0, 0)
        order_meta_layout.setSpacing(6)
        order_meta_layout.addWidget(name_label)
        order_meta_layout.addWidget(self.status_label)

        header_layout = QHBoxLayout()
        header_layout.addLayout(order_meta_layout)
        header_layout.addStretch(1)
        header_layout.addWidget(self.toggle_status_button)
        header_layout.addSpacing(8)
        header_layout.addWidget(self.remove_button)
        information_layout = QHBoxLayout()
        information_layout.setContentsMargins(0, 0, 0, 0)
        information_layout.setSpacing(6)
        information_layout.addWidget(self.created_at_label)
        information_layout.addStretch(1)
        information_layout.addWidget(self.to_go_label)

        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.sent_status_label)
        main_layout.addLayout(information_layout)
        
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(2)

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

    def update_from_order(self, order):
        self.order = order
        self.status = order.status
        if self.status_label is not None:
            self.status_label.setText(f"- {self.status}")
        if self.sent_status_label is not None:
            self.sent_status_label.setText(self._sent_status_text())
        if self.remove_button is not None:
            self.remove_button.setEnabled(self.status != "Closed")
        if self.toggle_status_button is not None:
            self.toggle_status_button.setEnabled(self.status != "Closed")
            self.toggle_status_button.setText(self._toggle_status_button_text())
        if self.created_at_label is not None:
            self.created_at_label.setText(self._time_table_text())
        if self.to_go_label is not None:
            self.to_go_label.setText(self._to_go_text())

    def _created_at_text(self):
        if hasattr(self.order, "created_time_text"):
            return str(self.order.created_time_text()).upper()
        return "--:--"

    def _table_text(self):
        table = (self.order.table or "").strip()
        return table.upper() if table else ""

    def _time_table_text(self):
        table_text = self._table_text()
        if table_text:
            return f"{self._created_at_text()} - {table_text}"
        return self._created_at_text()

    def _to_go_text(self):
        if not bool(self.order.to_go):
            return " "
        customer_name = (self.order.name or "").strip().upper()
        if customer_name:
            return f"TO GO - {customer_name}"
        return "TO GO"

    def _sent_status_text(self):
        return "Sent" if bool(getattr(self.order, "sent_status", False)) else "Not sent"

    def _toggle_status_button_text(self):
        return "Move to new" if self.status == "In progress" else "Move to in progress"

    def remove_button_clicked(self):
        self.remove_button_signal.emit(self.id)

    def toggle_status_button_clicked(self):
        self.toggle_status_button_signal.emit(self.id)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.id)
        super().mousePressEvent(event)
        



