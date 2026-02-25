from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFormLayout,
    QMessageBox,
)


class NewTableView(QWidget):
    def __init__(self, controller, parent_dialog=None, row_data=None):
        super().__init__()
        self.controller = controller
        self.parent_dialog = parent_dialog
        self.row_data = row_data
        self.row_id = None

        # FORM
        self.form = QFormLayout()
        self.table_name = QLineEdit()
        self.position = QLineEdit()

        self.form.addRow("Table name: ", self.table_name)
        self.form.addRow("Position: ", self.position)

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

    def _load_row_data(self, row_data):
        if len(row_data) < 3:
            return
        self.row_id = row_data[0]
        self.table_name.setText(str(row_data[1]))
        self.position.setText(str(row_data[2]))

    def save_changes_button_clicked(self):
        if self.row_id is None:
            ok, message = self.controller.add_table_item(
                table_name=self.table_name.text(),
                position=self.position.text(),
            )
        else:
            ok, message = self.controller.update_table_item(
                row_id=self.row_id,
                table_name=self.table_name.text(),
                position=self.position.text(),
            )
        if not ok:
            QMessageBox.warning(self, "Invalid data", message)
            return
        if self.parent_dialog is not None:
            self.parent_dialog.accept()

    def close_button_clicked(self):
        if self.parent_dialog is not None:
            self.parent_dialog.reject()

