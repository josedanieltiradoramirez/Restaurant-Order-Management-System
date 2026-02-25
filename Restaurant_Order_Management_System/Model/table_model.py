from PyQt6.QtCore import QAbstractTableModel, Qt

class TableModel(QAbstractTableModel):
    def __init__(self, data, headers):
        super().__init__()
        self._data = data
        self._headers = headers

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()

        if row < 0 or row >= len(self._data):
            return None
        if column < 0:
            return None

        row_data = self._data[row]
        if column >= len(row_data):
            return ""

        return str(row_data[column])

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._headers[section]
            return section + 1
        
    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()
