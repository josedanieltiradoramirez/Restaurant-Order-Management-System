class Product:
    def __init__(self, name: str, price: int, notes_shortcuts=None, notes="", is_custom=False, display_name=None):
        #self.id
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.price = price
        self.quantity = 1
        self.details = []
        self.notes = notes
        self.notes_shortcuts = notes_shortcuts or []
        self.is_custom = is_custom
