from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpinBox, QLineEdit
)
from PyQt6.QtGui import QFont, QMouseEvent, QDoubleValidator
from PyQt6.QtCore import Qt, pyqtSignal


class GuardedWheelSpinBox(QSpinBox):
    def wheelEvent(self, event):
        # Prevent accidental quantity changes while scrolling the parent view.
        if self.hasFocus():
            super().wheelEvent(event)
            return
        event.ignore()


class OrderElementCard(QWidget):
    remove_button_signal = pyqtSignal(str)          # product_id
    quantity_changed_signal = pyqtSignal(str, int) # product_id, quantity
    notes_changed_signal = pyqtSignal(str, str)    # product_id, notes
    price_changed_signal = pyqtSignal(str, float)  # product_id, price
    name_changed_signal = pyqtSignal(str, str)     # old_name, new_name
    clicked = pyqtSignal(str)                       # product_id

    def __init__(self, product):
        super().__init__()

        self.product = product
        self.remove_button = None
        self.shortcut_buttons = []

        self.setMinimumWidth(160)
        self.setFixedHeight(86)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self.init_ui()
        self.refresh()

    def init_ui(self):
        # -------- TOP ROW --------
        display_name = getattr(self.product, "display_name", self.product.name)
        self.name_label = QLabel(display_name)
        self.name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.name_label.setStyleSheet("color: #1f1f1f;")
        self.name_input = QLineEdit(display_name)
        self.name_input.editingFinished.connect(self.on_name_edited)

        self.price_label = QLabel(f"${self.product.price}")
        self.price_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.price_label.setStyleSheet("color: #111827;")
        self.price_prefix_label = QLabel("Precio:")
        self.price_prefix_label.setFont(QFont("Segoe UI", 9))
        self.price_prefix_label.setStyleSheet("color: #6b7280;")
        self.price_input = QLineEdit()
        self.price_input.setValidator(QDoubleValidator(0.0, 99999.0, 2))
        self.price_input.editingFinished.connect(self.on_price_edited)
        self.price_input.setStyleSheet(
            "font-weight: 600;"
            "color: #111827;"
        )

        self.quantity_label = QLabel("Cantidad:")
        self.quantity_label.setFont(QFont("Segoe UI", 9))
        self.quantity_label.setStyleSheet("color: #6b7280;")

        self.total_prefix_label = QLabel("Total:")
        self.total_prefix_label.setStyleSheet("color: #6b7280;")
        self.total_prefix_label.setFont(QFont("Segoe UI", 9))

        self.quantity_spinbox = GuardedWheelSpinBox()
        self.quantity_spinbox.setMinimum(1)
        self.quantity_spinbox.setMaximum(99)
        self.quantity_spinbox.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.quantity_spinbox.setKeyboardTracking(False)
        self.quantity_spinbox.valueChanged.connect(self.on_quantity_changed)

        self.total_label = QLabel()
        self.total_label.setStyleSheet("color: #111827;")
        self.total_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_button_clicked)
        self.remove_button.setFixedHeight(22)

        top_row = QHBoxLayout()
        if self.product.is_custom:
            top_row.addWidget(self.name_input)
            top_row.addSpacing(12)
            top_row.addWidget(self.price_prefix_label)
            top_row.addWidget(self.price_input)
        else:
            top_row.addWidget(self.name_label)
            top_row.addSpacing(12)
            top_row.addWidget(self.price_prefix_label)
            top_row.addWidget(self.price_label)
        top_row.addWidget(self.quantity_label)
        top_row.addWidget(self.quantity_spinbox)
        top_row.addWidget(self.total_prefix_label)
        top_row.addWidget(self.total_label)
        top_row.addStretch(1)
        top_row.addWidget(self.remove_button)
        top_row.setSpacing(8)

        # -------- NOTES ROW --------
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notas")
        self.notes_input.textChanged.connect(self.on_notes_changed)

        shortcuts = list(self.product.notes_shortcuts or [])
        shortcuts_row = QHBoxLayout()
        shortcuts_row.setSpacing(4)
        if shortcuts:
            for text in shortcuts:
                btn = QPushButton(text)
                btn.setObjectName("shortcut")
                btn.setFixedHeight(20)
                btn.clicked.connect(lambda _, t=text: self.append_note(t))
                self.shortcut_buttons.append(btn)
                shortcuts_row.addWidget(btn)
            shortcuts_row.addStretch(1)

        notes_row = QHBoxLayout()
        notes_row.addWidget(self.notes_input)
        if shortcuts:
            notes_row.addLayout(shortcuts_row)
        notes_row.setSpacing(6)

        # -------- MAIN LAYOUT --------
        layout = QVBoxLayout(self)
        layout.addLayout(top_row)
        layout.addLayout(notes_row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        self.setLayout(layout)
        self.setObjectName("card")
        self.setStyleSheet("""
            QWidget#card {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
            }
            QWidget#card:hover {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
            }
            QWidget#card[selected="true"] {
                background-color: #dbeafe;
                border: 1px solid #93c5fd;
            }
            QLineEdit {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 9pt;
                color: #111827;
                background-color: #ffffff;
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
            QPushButton#shortcut {
                background-color: #eef2f7;
                border: 1px solid #cbd5e1;
                font-size: 8pt;
                padding: 1px 6px;
            }
            QPushButton#shortcut:hover {
                background-color: #e2e8f0;
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

    def refresh(self):
        self.quantity_spinbox.blockSignals(True)
        self.quantity_spinbox.setValue(self.product.quantity)
        self.quantity_spinbox.blockSignals(False)
        if self.product.is_custom:
            display_name = getattr(self.product, "display_name", self.product.name)
            self.name_input.blockSignals(True)
            self.name_input.setText(display_name)
            self.name_input.blockSignals(False)
            self.price_input.blockSignals(True)
            self.price_input.setText(f"{float(self.product.price):.2f}")
            self.price_input.blockSignals(False)
        self.notes_input.blockSignals(True)
        self.notes_input.setText(self.product.notes)
        self.notes_input.blockSignals(False)
        self.update_total()

    def on_quantity_changed(self, value):
        self.product.quantity = value
        self.update_total()
        self.quantity_changed_signal.emit(self.product.name, value)

    def on_notes_changed(self, text):
        self.product.notes = text
        self.notes_changed_signal.emit(self.product.name, text)

    def on_price_edited(self):
        text = self.price_input.text().strip().replace(",", ".")
        if text == "":
            self.price_input.setText(f"{float(self.product.price):.2f}")
            return
        try:
            value = float(text)
        except ValueError:
            self.price_input.setText(f"{float(self.product.price):.2f}")
            return
        if value < 0:
            value = 0.0
        self.product.price = value
        self.price_input.setText(f"{value:.2f}")
        self.update_total()
        self.price_changed_signal.emit(self.product.name, value)

    def on_name_edited(self):
        new_name = self.name_input.text().strip()
        if not new_name:
            self.name_input.setText(getattr(self.product, "display_name", self.product.name))
            return
        old_name = self.product.name
        self.name_changed_signal.emit(old_name, new_name)

    def append_note(self, note):
        text = self.notes_input.text().strip()
        if not text:
            self.notes_input.setText(note)
            return
        parts = [p.strip() for p in text.split(",") if p.strip()]
        if note in parts:
            return
        parts.append(note)
        self.notes_input.setText(", ".join(parts))

    def update_total(self):
        total = self.product.quantity * self.product.price
        self.total_label.setText(f"${total}")

    def remove_button_clicked(self):
        self.remove_button_signal.emit(self.product.name)

    def set_selected(self, selected: bool):
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.product.name)
        super().mousePressEvent(event)

    def set_interaction_enabled(self, enabled: bool):
        if self.remove_button is not None:
            self.remove_button.setEnabled(enabled)
        self.quantity_spinbox.setEnabled(enabled)
        self.notes_input.setReadOnly(not enabled)
        if self.product.is_custom:
            self.name_input.setReadOnly(not enabled)
            self.price_input.setReadOnly(not enabled)
        for btn in self.shortcut_buttons:
            btn.setEnabled(enabled)
