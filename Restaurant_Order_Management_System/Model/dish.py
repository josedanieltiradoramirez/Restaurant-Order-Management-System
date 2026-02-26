from Model.product import Product
class Dish():
    def __init__(self, dish_id: str):
        self.id = dish_id
        self.name = ""
        self.additional_notes = ""
        self.products: dict[str:dict] = {}
        self.display_name = ""
        self.total_amount = 0
        self.status = "New"
        self.sent_count = 0
        self.to_go = False
        self.to_go_overridden = False


    def remove_product(self, product_name):
        del self.products[product_name]
        self.total()


    def total(self):
        self.total_amount = sum(
            p.price * p.quantity 
            for p in self.products.values()
        ) if self.products else 0


    def add_product(self, product):
        if product.name in self.products and not getattr(product, "is_custom", False):
            self.products[product.name].quantity += 1
            if getattr(product, "notes", "") and not self.products[product.name].notes:
                self.products[product.name].notes = product.notes
        else:
            shortcuts = getattr(product, "notes_shortcuts", None)
            notes = getattr(product, "notes", "")
            display_name = getattr(product, "display_name", None)
            is_custom = getattr(product, "is_custom", False)
            self.products[product.name] = Product(product.name, product.price, shortcuts, notes, is_custom, display_name)
        self.total()

    def rename_product(self, old_name: str, new_name: str) -> bool:
        if old_name not in self.products:
            return False
        if new_name in self.products and new_name != old_name:
            return False
        product = self.products.pop(old_name)
        product.name = new_name
        self.products[new_name] = product
        return True

    def set_product_quantity(self, product_name, quantity: int):
        if product_name not in self.products:
            return
        self.products[product_name].quantity = max(1, quantity)
        self.total()

    def set_status(self, status):
        self.status = status

    def sent_count_increase(self):
        self.sent_count += 1

    def set_to_go(self, to_go, overridden=False):
        self.to_go = to_go
        if overridden:
            self.to_go_overridden = True
