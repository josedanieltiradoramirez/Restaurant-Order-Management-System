from datetime import datetime
import re

class OrderNumberGenerator:
    def __init__(self):
        self.last_date = None
        self.counter = 0

    def seed_from_order_id(self, order_id: str | None):
        if not order_id:
            return
        match = re.fullmatch(r"O(\d{8})(\d{4})", str(order_id).strip())
        if not match:
            return
        self.last_date = match.group(1)
        self.counter = int(match.group(2))

    def next(self) -> str:
        today = datetime.now().strftime("%Y%m%d")

        if self.last_date != today:
            self.last_date = today
            self.counter = 1
        else:
            self.counter += 1

        return f"O{today}{self.counter:04d}"
