from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFormLayout,
    QMessageBox,
    QColorDialog,
    QComboBox,
)


class NewProductView(QWidget):
    def __init__(self, controller, parent_dialog=None, row_data=None):
        super().__init__()
        self.controller = controller
        self.parent_dialog = parent_dialog
        self.row_data = row_data
        self.row_id = None

        # FORM
        self.form = QFormLayout()
        self.product_name = QLineEdit()
        self.cost = QLineEdit()
        self.shortcuts = QLineEdit()
        self.color_value = ""
        self.color_button = QPushButton("Select color")
        self.color_button.clicked.connect(self.select_color_clicked)
        self.shape = QComboBox()
        self.shape.addItems(
            ["Square", "Circle", "Ellipse", "Rectangle", "Rounded rectangle"]
        )
        self.shape.setEditable(False)
        self.position = QLineEdit()
        self.product_type = QComboBox()
        self.product_type.addItems(["Food", "Drink"])
        self.product_type.setEditable(False)

        self.form.addRow("Name: ", self.product_name)
        self.form.addRow("Cost: ", self.cost)
        self.form.addRow("Shortcuts: ", self.shortcuts)
        self.form.addRow("Color: ", self.color_button)
        self.form.addRow("Shape: ", self.shape)
        self.form.addRow("Position: ", self.position)
        self.form.addRow("Type: ", self.product_type)

        # ACTION BUTTONS
        save_changes_button = QPushButton("Save changes")
        save_changes_button.clicked.connect(self.save_changes_button_clicked)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close_button_clicked)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(save_changes_button)
        buttons_layout.addWidget(close_button)

        # MAIN LAYOUT
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.form)
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        if self.row_data is not None:
            self._load_row_data(self.row_data)
        else:
            self._apply_color("")

    def _load_row_data(self, row_data):
        if len(row_data) < 8:
            return
        self.row_id = row_data[0]
        self.product_name.setText(str(row_data[1]))
        self.cost.setText(str(row_data[2]))
        self.shortcuts.setText(str(row_data[3]))
        self._apply_color(str(row_data[4]))
        shape_text = str(row_data[5]).strip()
        shape_index = self.shape.findText(shape_text)
        if shape_index >= 0:
            self.shape.setCurrentIndex(shape_index)
        else:
            self.shape.setCurrentIndex(0)
        self.position.setText(str(row_data[6]))
        product_type_text = str(row_data[7]).strip()
        type_index = self.product_type.findText(product_type_text)
        if type_index >= 0:
            self.product_type.setCurrentIndex(type_index)
        else:
            self.product_type.setCurrentIndex(0)

    def _apply_color(self, color_text):
        text = (color_text or "").strip()
        self.color_value = text
        if text:
            self.color_button.setText(text)
            self.color_button.setStyleSheet(
                f"background-color: {text}; color: #111111; border: 1px solid #9ca3af; padding: 4px 8px;"
            )
        else:
            self.color_button.setText("Select color")
            self.color_button.setStyleSheet("")

    def select_color_clicked(self):
        selected = QColorDialog.getColor(parent=self)
        if not selected.isValid():
            return
        self._apply_color(selected.name())

    def save_changes_button_clicked(self):
        if self.row_id is None:
            ok, message = self.controller.add_menu_item(
                product_name=self.product_name.text(),
                cost=self.cost.text(),
                shortcuts=self.shortcuts.text(),
                color=self.color_value,
                shape=self.shape.currentText(),
                position=self.position.text(),
                product_type=self.product_type.currentText(),
            )
        else:
            ok, message = self.controller.update_menu_item(
                row_id=self.row_id,
                product_name=self.product_name.text(),
                cost=self.cost.text(),
                shortcuts=self.shortcuts.text(),
                color=self.color_value,
                shape=self.shape.currentText(),
                position=self.position.text(),
                product_type=self.product_type.currentText(),
            )
        if not ok:
            QMessageBox.warning(self, "Invalid data", message)
            return
        if self.parent_dialog is not None:
            self.parent_dialog.accept()

    def close_button_clicked(self):
        if self.parent_dialog is not None:
            self.parent_dialog.reject()

