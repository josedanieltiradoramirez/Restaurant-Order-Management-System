from PyQt6.QtWidgets import QWidget, QGridLayout

class ProductsGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # MAIN GRID
        self.grid = QGridLayout(self)
        self.grid.setSpacing(16)
        self.grid.setContentsMargins(16, 16, 16, 16)

        self.columns = 3  # ðŸ‘ˆ nÃºmero de columnas

    def add_card(self, card):
        count = self.grid.count()
        row = count // self.columns
        col = count % self.columns
        self.grid.addWidget(card, row, col)
