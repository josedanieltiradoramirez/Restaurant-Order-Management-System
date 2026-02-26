from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout)
from View.product_card import ProductCard
from View.order_element_card import OrderElementCard
from PyQt6.QtCore import Qt
from View.order_card import OrderCard
import uuid

class ItemsList(QWidget):
    def __init__(self):
        super().__init__()
        # INTERNAL STATE
        self.items: dict[str, QWidget] = {}

        # MAIN LAYOUT
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.active_item = None

        self.columns = 1

    def add_item(self, item_id: str, widget:QWidget):
        self.items[item_id] = widget
        self.layout.addWidget(widget)

    
    def remove_item(self, item_id:str):
        widget = self.items.pop(item_id, None)
        if not widget:
            return
        self.layout.removeWidget(widget)

        widget.deleteLater()

    def take_item(self, item_id: str):
        widget = self.items.pop(item_id, None)
        if not widget:
            return None
        self.layout.removeWidget(widget)
        return widget
    
    #def add_new_item(self, item_data, item_list):
    #    item_id = str(uuid.uuid4())
    #    new_item = item_list.add_item(
    #        item_id, item_data
    #    )
    #      return new_item
        

    def remove_item_by_instance(self, item):
        for key, value in self.items.items():
            if value is item:
                self.layout.removeWidget(item)
                del self.items[key]
                item.deleteLater()
                break

    def select_item(self, item):
        self.active_item = item
            

    def remove_element(self, id):
        if self.active_item:
            self.active_item.remove_item(id)

# Remove from UI
        widget = self.items.get(id)
        if widget:
            self.layout.removeWidget(widget)
            widget.deleteLater()
            del self.items[id]
    
    def render(self, order):
        self.clear()
        self.active_order = order
        if order is None:
            return
    
        for dish in order.dishes.values():
            card = OrderCard({"id": dish.id,"name": dish.name, "price":dish.additional_notes})
            #card.set_quantity(product.quantity)

            card.remove_button_signal.connect(self.remove_element)

            self.items[dish.name] = card
            self.layout.addWidget(card)

            
    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        # Clear internal state
        self.items.clear()

    def set_active(self, item_id: str):
        self.active_item = self.items.get(item_id)
        for key, widget in self.items.items():
            is_selected = key == item_id
            if hasattr(widget, "set_selected"):
                widget.set_selected(is_selected)
            else:
                widget.setProperty("selected", is_selected)
                widget.style().unpolish(widget)
                widget.style().polish(widget)


