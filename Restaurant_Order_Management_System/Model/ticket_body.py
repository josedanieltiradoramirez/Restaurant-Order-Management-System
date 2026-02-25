from datetime import datetime
import textwrap


class TicketBody:
    WIDTH = 32  # typical width for a 58mm thermal printer
    TOP_PADDING_LINES = 3

    @staticmethod
    def _line(text: str = "") -> str:
        return text[:TicketBody.WIDTH]

    @classmethod
    def _wrap_lines(cls, text: str, center: bool = False):
        chunks = textwrap.wrap(str(text or ""), width=cls.WIDTH) or [""]
        if center:
            return [chunk.center(cls.WIDTH) for chunk in chunks]
        return chunks

    @staticmethod
    def _sep(char: str = "-") -> str:
        return char * TicketBody.WIDTH

    @staticmethod
    def _money(value: float) -> str:
        return f"${value:,.2f}"

    @classmethod
    def build(cls, order, use_print_time=False) -> str:
        if use_print_time:
            ticket_date = datetime.now().strftime("%d/%m/%Y %H:%M")
        else:
            created_at = getattr(order, "created_at", None)
            if isinstance(created_at, datetime):
                ticket_date = created_at.strftime("%d/%m/%Y %H:%M")
            else:
                ticket_date = datetime.now().strftime("%d/%m/%Y %H:%M")

        lines = ["" for _ in range(cls.TOP_PADDING_LINES)]
        lines.extend(cls._wrap_lines("TAQUERIA EL PADRINO", center=True))
        lines.extend(cls._wrap_lines("ESTILO CULIACAN", center=True))
        lines.extend(cls._wrap_lines("Avenida La Marina 239 Jardines del Toreo", center=True))
        lines.extend(cls._wrap_lines("6691513122", center=True))
        lines.extend(cls._wrap_lines("Mazatlan Sinaloa", center=True))
        lines.extend(cls._wrap_lines("ORDER TICKET", center=True))
        lines.append(cls._sep())
        lines.append(cls._line(f"Folio: {order.id}"))
        lines.append(cls._line(f"Date: {ticket_date}"))
        lines.extend(cls._wrap_lines(f"Customer: {order.name or 'GENERAL PUBLIC'}"))
        lines.append(cls._line(f"Table: {order.table or 'N/A'}"))
        lines.append(cls._line(f"To go: {'Yes' if order.to_go else 'No'}"))
        if bool(getattr(order, "include_additional_notes_in_ticket", False)):
            notes_text = str(getattr(order, "additional_notes", "") or "").strip()
            if notes_text:
                lines.extend(cls._wrap_lines(f"Additional notes: {notes_text}"))
        lines.append(cls._sep())

        for i, dish in enumerate(order.dishes.values(), start=1):
            lines.extend(cls._wrap_lines(f"[{i}] {dish.display_name or f'Dish {i}'}"))
            lines.append(cls._line(f"  To go: {'Yes' if dish.to_go else 'No'}"))
            for p in dish.products.values():
                subtotal = p.price * p.quantity
                pname = p.display_name or p.name
                lines.extend(cls._wrap_lines(f"  {p.quantity} x {pname}"))
                lines.append(cls._line(f"    {cls._money(p.price)} each  {cls._money(subtotal)}"))
                if p.notes:
                    lines.extend(cls._wrap_lines(f"    Note: {p.notes}"))
            lines.append(cls._line(f"  Dish subtotal: {cls._money(dish.total_amount)}"))
            lines.append(cls._sep("."))

        lines.append(cls._sep())
        lines.append(cls._line(f"TOTAL: {cls._money(order.total_amount)}".rjust(cls.WIDTH)))
        lines.append(cls._line(f"PAID: {cls._money(order.amount_paid)}".rjust(cls.WIDTH)))
        change = max(float(order.amount_paid) - float(order.total_amount), 0.0)
        lines.append(cls._line(f"CHANGE: {cls._money(change)}".rjust(cls.WIDTH)))
        lines.append(cls._sep())
        lines.extend(cls._wrap_lines("THANK YOU FOR YOUR PURCHASE!", center=True))
        lines.extend(cls._wrap_lines("FULL BELLY, HAPPY HEART", center=True))
        lines.append("\n\n\n")

        return "\n".join(lines)

