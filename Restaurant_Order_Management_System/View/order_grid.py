from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout)
from View.product_card import ProductCard
from View.order_element_card import OrderElementCard
from PyQt6.QtCore import Qt
from Model.order import Order

class OrderGrid(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # INTERNAL STATE
        self.items = {}

        # MAIN LAYOUT
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.active_dish = None

        self.columns = 1  # ðŸ‘ˆ nÃºmero de columnas

    def add_element(self, element):
        
        name = element.product.name

    
        self.items[name] = element
        self.layout.addWidget(element)
        if hasattr(element, "clicked"):
            element.clicked.connect(self.set_active)
        
            

    def remove_element(self, name):
        if self.active_dish:
            self.active_dish.remove_item(name)

# Remove from UI
        widget = self.items.get(name)
        if widget:
            self.layout.removeWidget(widget)
            widget.deleteLater()
            del self.items[name]
    
    def render(self, dish):
        self.clear()
        self.active_dish = dish
        if dish is None:
            return
    
        for name, data in dish.items.items():
            card = OrderElementCard(name, data["price"])
            card.set_quantity(data["qty"])

            card.remove_button_signal.connect(self.remove_element)

            self.items[name] = card
            self.layout.addWidget(card)

            
    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # Clear internal state
        self.items.clear()
        self.active_item = None

    def set_active(self, item_id: str | None):
        self.active_item = self.items.get(item_id)
        for key, widget in self.items.items():
            is_selected = key == item_id
            if hasattr(widget, "set_selected"):
                widget.set_selected(is_selected)
            else:
                widget.setProperty("selected", is_selected)
                widget.style().unpolish(widget)
                widget.style().polish(widget)

    def show_order(self, order: Order):
        self.clear()
        self.active_order = order

        for dish in order.dishes.values():
            for product in dish.products.values():
                self.add_element(product)


