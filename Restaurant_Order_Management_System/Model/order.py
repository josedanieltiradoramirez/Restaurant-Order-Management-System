import uuid
from datetime import datetime
from Model.dish import Dish
class Order():
    def __init__(self, order_id: str):
        self.id = order_id
        self.created_at = datetime.now()
        self.service_date = self.created_at.date().isoformat()
        self.name = ""
        self.additional_notes = ""
        self.include_additional_notes_in_ticket = False
        self.dishes: dict[str:dict] = {}
        self.active_dish = None
        self.total_amount = 0
        self.status = "New"
        self.additional_request = {}
        self.to_go = False
        self.sent_status = False
        self.table = ""
        self.amount_paid = 0.0

    def add_dish(self):
        dish_id = str(uuid.uuid4())
        new_dish = Dish(dish_id)
        self.dishes[dish_id] = new_dish
        self.active_dish = new_dish
        self.renumber_dishes()
        self.total()
        return new_dish

    def remove_dish(self, dish_id):
        if dish_id in self.dishes:
            del self.dishes[dish_id]
            self.renumber_dishes()
            self.total()

    def set_active_dish(self, dish_id):
        self.active_dish = self.dishes[dish_id]
        dish = self.dishes[dish_id]
        return dish
    
    def renumber_dishes(self):
        for index, dish in enumerate(self.dishes.values(), start=1):
            dish.display_name = f"Dish {index}"


    def total(self):
        self.total_amount = sum(dish.total_amount for dish in self.dishes.values()) if self.dishes else 0

    def set_status(self, status):
        self.status = status

    def set_name(self, name):
        self.name = name

    def set_additional_notes(self, notes):
        self.additional_notes = str(notes or "").strip()

    def set_include_additional_notes_in_ticket(self, enabled):
        self.include_additional_notes_in_ticket = bool(enabled)
    
    def set_table(self, table):
        self.table = table

    def set_to_go(self, to_go):
        self.to_go = to_go

    def set_amount_paid(self, amount_paid):
        self.amount_paid = amount_paid

    def set_sent_status(self, sent_status: bool):
        self.sent_status = bool(sent_status)

    def set_service_date(self, service_date: str):
        self.service_date = service_date

    def created_time_text(self):
        return self.created_at.strftime("%H:%M")


