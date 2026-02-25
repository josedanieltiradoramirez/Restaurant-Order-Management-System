

from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                            QPushButton, QLineEdit, QHBoxLayout, 
                            QVBoxLayout, QComboBox, QTabWidget, QTableView,
                            QFormLayout, QMessageBox, QGroupBox, QDateEdit, QCheckBox,
                            QDialog, QPlainTextEdit, QCalendarWidget, QGridLayout, QFrame)
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QColor
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from Infrastructure.connection_db import Database, MenuDatabase
from Infrastructure.order_repository import OrderRepository
from Model.table_model import TableModel
from Model.ticket_body import TicketBody
from Controller.order_crud_controller import OrderCrudController
from Controller.order_controller import OrderController
from View.order_management_view import OrderManagementView


class RevenueCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.revenue_by_date = {}

    def set_revenue_map(self, revenue_map):
        self.revenue_by_date = dict(revenue_map or {})
        try:
            self.updateCells()
        except RuntimeError:
            # Underlying C/C++ Qt object may have been deleted; ignore update
            return

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        key = date.toString("yyyy-MM-dd")
        amount = self.revenue_by_date.get(key)
        if amount is None:
            return
        painter.save()
        font = painter.font()
        font.setPointSize(max(7, font.pointSize() - 1))
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        shown_year = self.yearShown()
        shown_month = self.monthShown()
        in_current_month = (date.year() == shown_year and date.month() == shown_month)

        chip_rect = rect.adjusted(8, rect.height() - 24, -8, -6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#e2e8f0") if in_current_month else QColor("#f1f5f9"))
        painter.drawRoundedRect(chip_rect, 6, 6)

        painter.setPen(QColor("#1f2937") if in_current_month else QColor("#94a3b8"))
        amount_text = f"${amount:,.0f}" if float(amount).is_integer() else f"${amount:,.2f}"
        painter.drawText(chip_rect, Qt.AlignmentFlag.AlignCenter, amount_text)
        painter.restore()


class DayCardFrame(QFrame):
    clicked = pyqtSignal(QDate)

    def __init__(self, date, parent=None):
        super().__init__(parent)
        self.date = date

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.date)
        super().mousePressEvent(event)


class MonthCardFrame(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, month_number, parent=None):
        super().__init__(parent)
        self.month_number = int(month_number)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.month_number)
        super().mousePressEvent(event)


class RevenueMonthGridWidget(QWidget):
    day_clicked = pyqtSignal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.revenue_by_date = {}
        self.current_month = QDate.currentDate()
        self.current_month = QDate(self.current_month.year(), self.current_month.month(), 1)
        self._build_ui()
        self._render_month()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.month_label = QLabel("")
        self.month_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prev_button.setFixedWidth(34)
        self.next_button.setFixedWidth(34)
        self.prev_button.clicked.connect(self._go_prev_month)
        self.next_button.clicked.connect(self._go_next_month)

        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.month_label, 1)
        controls_layout.addWidget(self.next_button)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addLayout(controls_layout)
        self.main_layout.addLayout(self.grid)

    def set_revenue_map(self, revenue_map):
        self.revenue_by_date = dict(revenue_map or {})
        self._render_month()

    def _go_prev_month(self):
        self.current_month = self.current_month.addMonths(-1)
        self._render_month()

    def _go_next_month(self):
        self.current_month = self.current_month.addMonths(1)
        self._render_month()

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_month(self):
        self._clear_grid()
        self.month_label.setText(self.current_month.toString("MMMM yyyy").title())
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, name in enumerate(weekday_names):
            header = QLabel(name)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setStyleSheet("color: #64748b; font-weight: 600;")
            self.grid.addWidget(header, 0, col)

        first_day = self.current_month
        days_in_month = first_day.daysInMonth()
        month_amounts = {}
        for day_idx in range(1, days_in_month + 1):
            date_key = QDate(first_day.year(), first_day.month(), day_idx).toString("yyyy-MM-dd")
            month_amounts[date_key] = float(self.revenue_by_date.get(date_key, 0.0) or 0.0)

        positive_values = [value for value in month_amounts.values() if value > 0]
        high_keys = set()
        low_keys = set()
        if positive_values:
            max_value = max(positive_values)
            min_value = min(positive_values)
            high_keys = {key for key, value in month_amounts.items() if value == max_value}
            low_keys = {key for key, value in month_amounts.items() if value == min_value}

        start_col = first_day.dayOfWeek() - 1  # Monday=1
        day = 1
        row = 1
        col = start_col
        while day <= days_in_month:
            date = QDate(first_day.year(), first_day.month(), day)
            date_key = date.toString("yyyy-MM-dd")
            card = self._day_card(
                date,
                is_high=(date_key in high_keys),
                is_low=(date_key in low_keys),
            )
            self.grid.addWidget(card, row, col)
            day += 1
            col += 1
            if col > 6:
                col = 0
                row += 1

        for r in range(1, 8):
            self.grid.setRowStretch(r, 1)
        for c in range(7):
            self.grid.setColumnStretch(c, 1)

    def _day_card(self, date, is_high=False, is_low=False):
        card = DayCardFrame(date)
        card.clicked.connect(self.day_clicked.emit)
        card.setObjectName("dayCard")
        card.setMinimumHeight(94)
        border_color = "#e2e8f0"
        bg_color = "#f8fafc"
        amount_color = "#334155"
        if is_high:
            border_color = "#86efac"
            bg_color = "#f0fdf4"
            amount_color = "#166534"
        elif is_low:
            border_color = "#fca5a5"
            bg_color = "#fef2f2"
            amount_color = "#991b1b"

        card.setStyleSheet(
            "QFrame#dayCard {"
            f"  background-color: {bg_color};"
            f"  border: 1px solid {border_color};"
            "  border-radius: 0px;"
            "}"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)
        day_label = QLabel(str(date.day()))
        day_label.setStyleSheet("color: #64748b; font-size: 9pt; font-weight: 400;")
        amount = self.revenue_by_date.get(date.toString("yyyy-MM-dd"), 0.0)
        base_amount_text = f"${amount:,.0f}" if float(amount).is_integer() else f"${amount:,.2f}"
        amount_text = f"Total: {base_amount_text}"
        amount_label = QLabel(amount_text)
        amount_label.setStyleSheet(f"color: {amount_color}; font-size: 10pt; font-weight: 500;")
        layout.addWidget(day_label)
        layout.addStretch(1)
        layout.addWidget(amount_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        return card


class RevenueWeekWidget(QWidget):
    week_changed = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.revenue_by_date = {}
        today = QDate.currentDate()
        self.week_start = today.addDays(1 - today.dayOfWeek())  # Monday
        self._build_ui()
        self._render_week()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.week_label = QLabel("")
        self.week_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.week_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prev_button.setFixedWidth(34)
        self.next_button.setFixedWidth(34)
        self.prev_button.clicked.connect(self._go_prev_week)
        self.next_button.clicked.connect(self._go_next_week)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.week_label, 1)
        controls_layout.addWidget(self.next_button)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addLayout(controls_layout)
        self.main_layout.addLayout(self.grid)

    def set_revenue_map(self, revenue_map):
        self.revenue_by_date = dict(revenue_map or {})
        self._render_week()

    def _go_prev_week(self):
        self.week_start = self.week_start.addDays(-7)
        self._render_week()

    def _go_next_week(self):
        self.week_start = self.week_start.addDays(7)
        self._render_week()

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_week(self):
        self._clear_grid()
        week_end = self.week_start.addDays(6)
        self.week_label.setText(
            f"{self.week_start.toString('dd MMM yyyy')} - {week_end.toString('dd MMM yyyy')}"
        )

        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, name in enumerate(day_names):
            day_date = self.week_start.addDays(col)
            key = day_date.toString("yyyy-MM-dd")
            amount = float(self.revenue_by_date.get(key, 0.0) or 0.0)
            card = QFrame()
            card.setObjectName("weekDayCard")
            card.setStyleSheet(
                "QFrame#weekDayCard {"
                "  background-color: #f8fafc;"
                "  border: 1px solid #e2e8f0;"
                "  border-radius: 0px;"
                "}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(2)

            name_label = QLabel(name)
            name_label.setStyleSheet("color: #64748b; font-size: 9pt; font-weight: 500;")
            date_label = QLabel(day_date.toString("dd"))
            date_label.setStyleSheet("color: #334155; font-size: 10pt; font-weight: 600;")
            amount_text = f"${amount:,.0f}" if float(amount).is_integer() else f"${amount:,.2f}"
            total_label = QLabel(f"Total: {amount_text}")
            total_label.setStyleSheet("color: #334155; font-size: 9pt; font-weight: 500;")

            card_layout.addWidget(name_label)
            card_layout.addWidget(date_label)
            card_layout.addStretch(1)
            card_layout.addWidget(total_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            self.grid.addWidget(card, 0, col)
            self.grid.setColumnStretch(col, 1)
        self.week_changed.emit(self.week_start, week_end)


class RevenueYearWidget(QWidget):
    month_changed = pyqtSignal(QDate, QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.revenue_by_date = {}
        today = QDate.currentDate()
        self.current_year = today.year()
        self.selected_month = today.month()
        self._build_ui()
        self._render_year()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton("<")
        self.next_button = QPushButton(">")
        self.year_label = QLabel("")
        self.year_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.year_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.prev_button.setFixedWidth(34)
        self.next_button.setFixedWidth(34)
        self.prev_button.clicked.connect(self._go_prev_year)
        self.next_button.clicked.connect(self._go_next_year)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.year_label, 1)
        controls_layout.addWidget(self.next_button)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addLayout(controls_layout)
        self.main_layout.addLayout(self.grid)

    def set_revenue_map(self, revenue_map):
        self.revenue_by_date = dict(revenue_map or {})
        self._render_year()

    def _go_prev_year(self):
        self.current_year -= 1
        self._render_year()

    def _go_next_year(self):
        self.current_year += 1
        self._render_year()

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _month_total(self, month):
        total = 0.0
        for day in range(1, QDate(self.current_year, month, 1).daysInMonth() + 1):
            key = QDate(self.current_year, month, day).toString("yyyy-MM-dd")
            total += float(self.revenue_by_date.get(key, 0.0) or 0.0)
        return total

    def _render_year(self):
        self._clear_grid()
        self.year_label.setText(str(self.current_year))

        month_totals = {m: self._month_total(m) for m in range(1, 13)}
        positive_values = [value for value in month_totals.values() if value > 0]
        high_months = set()
        low_months = set()
        if positive_values:
            max_value = max(positive_values)
            min_value = min(positive_values)
            high_months = {m for m, v in month_totals.items() if v == max_value}
            low_months = {m for m, v in month_totals.items() if v == min_value}

        for month in range(1, 13):
            card = MonthCardFrame(month)
            card.clicked.connect(self._on_month_clicked)
            card.setObjectName("monthCard")
            border_color = "#e2e8f0"
            bg_color = "#f8fafc"
            text_color = "#334155"
            if month in high_months:
                border_color = "#86efac"
                bg_color = "#f0fdf4"
                text_color = "#166534"
            elif month in low_months:
                border_color = "#fca5a5"
                bg_color = "#fef2f2"
                text_color = "#991b1b"
            if month == self.selected_month:
                border_color = "#64748b"

            card.setStyleSheet(
                "QFrame#monthCard {"
                f"  background-color: {bg_color};"
                f"  border: 1px solid {border_color};"
                "  border-radius: 0px;"
                "}"
            )
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 6, 8, 6)
            card_layout.setSpacing(2)
            month_label = QLabel(QDate(self.current_year, month, 1).toString("MMM").upper())
            month_label.setStyleSheet("color: #64748b; font-size: 9pt; font-weight: 500;")
            total = month_totals[month]
            total_text = f"${total:,.0f}" if float(total).is_integer() else f"${total:,.2f}"
            total_label = QLabel(f"Total: {total_text}")
            total_label.setStyleSheet(f"color: {text_color}; font-size: 10pt; font-weight: 500;")
            card_layout.addWidget(month_label)
            card_layout.addStretch(1)
            card_layout.addWidget(total_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

            row = (month - 1) // 4
            col = (month - 1) % 4
            self.grid.addWidget(card, row, col)
            self.grid.setColumnStretch(col, 1)
            self.grid.setRowStretch(row, 1)

        self._emit_selected_month()

    def _on_month_clicked(self, month_number):
        self.selected_month = int(month_number)
        self._render_year()

    def _emit_selected_month(self):
        start = QDate(self.current_year, self.selected_month, 1)
        end = start.addMonths(1).addDays(-1)
        self.month_changed.emit(start, end)


class RevenueWeekdayWidget(QWidget):
    weekday_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.weekday_stats = {
            i: {"avg_total": 0.0, "sum_total": 0.0, "orders": 0, "day_count": 0, "avg_orders": 0.0}
            for i in range(1, 8)
        }
        self.selected_weekday = 1
        self._build_ui()
        self._render_weekdays()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        self.title_label = QLabel("Weekday view")
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.main_layout.addWidget(self.title_label)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(0)
        self.grid.setVerticalSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addLayout(self.grid)

    def set_weekday_stats(self, weekday_stats):
        base = {}
        for i in range(1, 8):
            src = weekday_stats.get(i, {}) if isinstance(weekday_stats, dict) else {}
            base[i] = {
                "avg_total": float(src.get("avg_total", 0.0) or 0.0),
                "sum_total": float(src.get("sum_total", 0.0) or 0.0),
                "orders": int(src.get("orders", 0) or 0),
                "day_count": int(src.get("day_count", 0) or 0),
                "avg_orders": float(src.get("avg_orders", 0.0) or 0.0),
            }
        self.weekday_stats = base
        self._render_weekdays()

    def _clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _render_weekdays(self):
        self._clear_grid()
        weekday_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
        positive_values = [v["avg_total"] for v in self.weekday_stats.values() if v.get("avg_total", 0.0) > 0]
        high_days = set()
        low_days = set()
        if positive_values:
            max_value = max(positive_values)
            min_value = min(positive_values)
            high_days = {d for d, v in self.weekday_stats.items() if v.get("avg_total", 0.0) == max_value}
            low_days = {d for d, v in self.weekday_stats.items() if v.get("avg_total", 0.0) == min_value}

        for idx, weekday in enumerate(range(1, 8)):
            card = MonthCardFrame(weekday)
            card.clicked.connect(self._on_day_clicked)
            card.setObjectName("weekdayCard")
            border_color = "#e2e8f0"
            bg_color = "#f8fafc"
            text_color = "#334155"
            if weekday in high_days:
                border_color = "#86efac"
                bg_color = "#f0fdf4"
                text_color = "#166534"
            elif weekday in low_days:
                border_color = "#fca5a5"
                bg_color = "#fef2f2"
                text_color = "#991b1b"
            if weekday == self.selected_weekday:
                border_color = "#64748b"
            card.setStyleSheet(
                "QFrame#weekdayCard {"
                f"  background-color: {bg_color};"
                f"  border: 1px solid {border_color};"
                "  border-radius: 0px;"
                "}"
            )
            layout = QVBoxLayout(card)
            layout.setContentsMargins(8, 6, 8, 6)
            layout.setSpacing(2)
            name_label = QLabel(weekday_names[weekday])
            name_label.setStyleSheet("color: #64748b; font-size: 9pt; font-weight: 500;")
            avg_amount = float(self.weekday_stats.get(weekday, {}).get("avg_total", 0.0) or 0.0)
            avg_text = f"${avg_amount:,.0f}" if float(avg_amount).is_integer() else f"${avg_amount:,.2f}"
            total_label = QLabel(f"Prom: {avg_text}")
            total_label.setStyleSheet(f"color: {text_color}; font-size: 10pt; font-weight: 500;")
            layout.addWidget(name_label)
            layout.addStretch(1)
            layout.addWidget(total_label, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            self.grid.addWidget(card, 0, idx)
            self.grid.setColumnStretch(idx, 1)
        self.weekday_changed.emit(self.selected_weekday)

    def _on_day_clicked(self, weekday_number):
        self.selected_weekday = int(weekday_number)
        self._render_weekdays()


class OrderCrudView(QWidget):
    def __init__(self):
        super().__init__()

        self.controller = OrderCrudController(self)
        self._orders_rows_cache = []
        self._selected_analysis_date = QDate.currentDate()

        tittle = QLabel("Page 1")
        tittle.setFont(QFont("Arial", 18))
        tittle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tabs = QTabWidget()
        tab_database_view = QWidget()
        tab_calendar_view = QWidget()
        tab_calendar_cards_view = QWidget()
        tab_weekly_view = QWidget()
        tab_yearly_view = QWidget()
        tab_weekday_view = QWidget()
        #--------------------------------------TAB 1 START---------------------------------------
        tab_create_database = QWidget()
        button_create_database = QPushButton("Create database")
        label_create_database = QLabel("Database name: ")
        label_create_database.setFixedWidth(100)
        line_create_database = QLineEdit()
        
        label_add_column = QLabel("Column name: ")
        label_add_column.setFixedWidth(100)
        label_data_type = QLabel("Data type: ")
        label_data_type.setFixedWidth(100)
        combobox_data_type = QComboBox()
        combobox_data_type.addItem("String")
        combobox_data_type.addItem("Integer")
        combobox_data_type.addItem("ID")
        line_add_column = QLineEdit()
        button_add_column = QPushButton("Add column")
        button_add_record = QPushButton("Add record")

        h_layout_1 = QHBoxLayout()
        h_layout_2 = QHBoxLayout()
        h_layout_3 = QHBoxLayout()
        h_layout_4 = QHBoxLayout()
        h_layout_5 = QHBoxLayout()

        h_layout_1.addWidget(label_create_database)
        h_layout_1.addWidget(line_create_database)
        h_layout_2.addWidget(button_create_database)
        h_layout_3.addWidget(label_add_column)
        h_layout_3.addWidget(line_add_column)
        h_layout_4.addWidget(label_data_type)
        h_layout_4.addWidget(combobox_data_type)
        h_layout_5.addWidget(button_add_column)
        

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout_1)
        v_layout.addLayout(h_layout_2)
        v_layout.addLayout(h_layout_3)
        v_layout.addLayout(h_layout_4)
        v_layout.addLayout(h_layout_5)

        tab_create_database.setLayout(v_layout)
        #--------------------------------------TAB 1 END---------------------------------------
        #--------------------------------------TAB 2 START---------------------------------------

        # MAIN TABLE
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        current_database = Database("orders.db","orders")
        data = current_database.fetch_all()
        headers = ["ID", "Created at", "Closed at", "Service date", "Name", "Table name", "Status", "To go", "Amount paid", "Total amount"]

        #
        self.main_model = TableModel(data, headers)
        self.table_view.setModel(self.main_model)

        #model = TableModel(data, headers)
        #self.table_view.setModel(model)
        tab2_layout_tab = QVBoxLayout()
        tab2_layout_tab.addWidget(self.table_view)

        # SELECTION CHECK MARK
        self.button_select_items = QPushButton("Select items")
        self.button_select_items.setCheckable(True)
        tab2_layout_tab.addWidget(self.button_select_items)

        # SELECTION TABLE
        self.selection_table = QTableView()
        self.headers = ["ID", "Name", "Labels", "Date", "Body"]
        self.selection_table_model = TableModel([],headers)
        self.selection_table.setModel(self.selection_table_model)
        self.selection_table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)

        
        group_selection_table = QGroupBox("Selected items")
        group_selection_table_layout = QVBoxLayout()
        group_selection_table_layout.addWidget(self.selection_table)
        group_selection_table.setLayout(group_selection_table_layout)

        tab2_layout_tab.addWidget(group_selection_table)

        self.table_view.selectionModel().selectionChanged.connect(self.update_selection_table)
        self.selection_table.doubleClicked.connect(self.selected_double_click)

        # FORM
        tab2_form = QFormLayout()
        self.tab2_form_line_order_id = QLineEdit()
        self.tab2_form_date_enabled = QCheckBox("Use date")
        self.tab2_form_line_date = QDateEdit()
        self.tab2_form_line_date.setCalendarPopup(True)
        self.tab2_form_line_date.setDisplayFormat("yyyy-MM-dd")
        self.tab2_form_line_date.setDate(QDate.currentDate())
        self.tab2_form_line_date.setEnabled(False)
        self.tab2_form_date_enabled.toggled.connect(self.tab2_form_line_date.setEnabled)
        self.tab2_form_line_name = QLineEdit()
        self.tab2_form_service_date_enabled = QCheckBox("Use date")
        self.tab2_form_line_service_date = QDateEdit()
        self.tab2_form_line_service_date.setCalendarPopup(True)
        self.tab2_form_line_service_date.setDisplayFormat("yyyy-MM-dd")
        self.tab2_form_line_service_date.setDate(QDate.currentDate())
        self.tab2_form_line_service_date.setEnabled(False)
        self.tab2_form_service_date_enabled.toggled.connect(self.tab2_form_line_service_date.setEnabled)
        self.tab2_form_line_table = QComboBox()
        self.tab2_form_line_table.addItem("")
        self.tab2_form_line_table.addItem("Table 1")
        self.tab2_form_line_table.addItem("Table 2")
        self.tab2_form_line_table.addItem("Table 3")
        self.tab2_form_line_table.addItem("Table 4")
        self.tab2_form_line_status = QComboBox()
        self.tab2_form_line_status.addItem("")
        self.tab2_form_line_status.addItem("New")
        self.tab2_form_line_status.addItem("In progress")
        self.tab2_form_line_status.addItem("Closed")
        self.tab2_form_line_to_go = QComboBox()
        self.tab2_form_line_to_go.addItem("")
        self.tab2_form_line_to_go.addItem("Yes")
        self.tab2_form_line_to_go.addItem("No")
        self.tab2_form_total_amount_operator = QComboBox()
        self.tab2_form_total_amount_operator.addItems(["=", ">", "<"])
        self.tab2_form_line_total_amount = QLineEdit()
        self.tab2_form_amount_paid_operator = QComboBox()
        self.tab2_form_amount_paid_operator.addItems(["=", ">", "<"])
        self.tab2_form_line_amount_paid = QLineEdit()


        tab2_form.addRow("Order ID: ", self.tab2_form_line_order_id)
        date_row = QHBoxLayout()
        date_row.addWidget(self.tab2_form_date_enabled)
        date_row.addWidget(self.tab2_form_line_date)
        tab2_form.addRow("Created at: ", date_row)
        service_date_row = QHBoxLayout()
        service_date_row.addWidget(self.tab2_form_service_date_enabled)
        service_date_row.addWidget(self.tab2_form_line_service_date)
        tab2_form.addRow("Service date: ", service_date_row)
        tab2_form.addRow("Name: ", self.tab2_form_line_name)
        tab2_form.addRow("Table: ", self.tab2_form_line_table)
        tab2_form.addRow("Status: ", self.tab2_form_line_status)
        tab2_form.addRow("To go: ", self.tab2_form_line_to_go)
        total_amount_row = QHBoxLayout()
        total_amount_row.addWidget(self.tab2_form_total_amount_operator)
        total_amount_row.addWidget(self.tab2_form_line_total_amount)
        tab2_form.addRow("Total amount: ", total_amount_row)
        amount_paid_row = QHBoxLayout()
        amount_paid_row.addWidget(self.tab2_form_amount_paid_operator)
        amount_paid_row.addWidget(self.tab2_form_line_amount_paid)
        tab2_form.addRow("Amount paid ", amount_paid_row)
        filters_group = QGroupBox("Search filters")
        filters_group_layout = QVBoxLayout()
        filters_group_layout.addLayout(tab2_form)
        filters_group.setLayout(filters_group_layout)
        
        #tab2_layout_form = QVBoxLayout()
        #tab2_layout_form.addLayout(tab2_form)

        # BUTTONS
        button_add_registry = QPushButton("Add registry")
        button_add_registry.clicked.connect(self.button_add_registry_clicked)
        button_search = QPushButton("Search")
        button_search.clicked.connect(self.button_search_clicked)
        button_delete = QPushButton("Delete")
        button_delete.clicked.connect(self.button_delete_clicked)
        tab2_layout_search = QHBoxLayout()
        tab2_layout_buttons = QHBoxLayout()
        button_edit = QPushButton("Edit")
        button_edit.clicked.connect(self.button_edit_clicked)
        tab2_layout_search.addWidget(button_search)
        tab2_layout_buttons.addWidget(button_add_registry)
        tab2_layout_buttons.addWidget(button_delete)
        tab2_layout_buttons.addWidget(button_edit)

        preview_group = QGroupBox("Ticket preview")
        preview_group_layout = QVBoxLayout()
        preview_row_layout = QHBoxLayout()
        preview_row_layout.addStretch(1)
        self.ticket_preview = QPlainTextEdit()
        self.ticket_preview.setReadOnly(True)
        self.ticket_preview.setPlaceholderText("Select an order to preview the ticket.")
        self.ticket_preview.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        preview_font = QFont("Consolas", 10)
        self.ticket_preview.setFont(preview_font)
        self.ticket_preview.setFixedWidth(self._ticket_preview_width(preview_font))
        preview_row_layout.addWidget(self.ticket_preview)
        preview_row_layout.addStretch(1)
        preview_group_layout.addLayout(preview_row_layout)
        preview_group.setLayout(preview_group_layout)


        tab2_layout_form_buttons = QVBoxLayout()
        tab2_layout_form_buttons.addWidget(filters_group)
        tab2_layout_form_buttons.addLayout(tab2_layout_search)
        tab2_layout_form_buttons.addWidget(preview_group)
        tab2_layout_form_buttons.addLayout(tab2_layout_buttons)

        tab2_main_layout = QHBoxLayout()
        tab2_main_layout.addLayout(tab2_layout_tab)
        tab2_main_layout.addLayout(tab2_layout_form_buttons)
        #--------------------------------------TAB 2 END---------------------------------------


        tab_database_view.setLayout(tab2_main_layout)

        calendar_layout = QVBoxLayout()
        calendar_title = QLabel("Calendar view")
        calendar_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.calendar_view = RevenueCalendarWidget()
        self.calendar_view.setGridVisible(True)
        self.calendar_view.setMinimumSize(920, 620)
        self.calendar_view.clicked.connect(self.on_calendar_date_clicked)
        self.calendar_view.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar_view.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.calendar_view.setStyleSheet(
            "QCalendarWidget {"
            "  background-color: #ffffff;"
            "  border: 1px solid #e2e8f0;"
            "  border-radius: 10px;"
            "}"
            "QCalendarWidget QWidget#qt_calendar_navigationbar {"
            "  background-color: #f8fafc;"
            "  border-bottom: 1px solid #e2e8f0;"
            "}"
            "QCalendarWidget QToolButton {"
            "  font-size: 10pt;"
            "  font-weight: 600;"
            "  color: #334155;"
            "  background-color: transparent;"
            "  border: none;"
            "  height: 34px;"
            "  min-width: 90px;"
            "  margin: 0 4px;"
            "}"
            "QCalendarWidget QToolButton:hover {"
            "  color: #0f172a;"
            "}"
            "QCalendarWidget QAbstractItemView {"
            "  outline: 0;"
            "}"
            "QCalendarWidget QAbstractItemView:enabled {"
            "  font-size: 11pt;"
            "  color: #0f172a;"
            "  background-color: #ffffff;"
            "  alternate-background-color: #f8fafc;"
            "  selection-background-color: #cbd5e1;"
            "  selection-color: #0f172a;"
            "  gridline-color: #e2e8f0;"
            "}"
            "QCalendarWidget QMenu {"
            "  background-color: #ffffff;"
            "  border: 1px solid #e2e8f0;"
            "}"
            "QCalendarWidget QSpinBox {"
            "  background-color: #ffffff;"
            "  color: #334155;"
            "  border: 1px solid #cbd5e1;"
            "  border-radius: 4px;"
            "  padding: 2px 6px;"
            "}"
        )
        calendar_table = self.calendar_view.findChild(QTableView)
        if calendar_table:
            calendar_table.horizontalHeader().setDefaultSectionSize(94)
            calendar_table.verticalHeader().setDefaultSectionSize(82)

        self.day_analysis_group = QGroupBox("Day analysis")
        self.day_analysis_title = QLabel("Select to day")
        self.day_analysis_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.day_analysis_text = QPlainTextEdit()
        self.day_analysis_text.setReadOnly(True)
        self.day_analysis_text.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        self.day_analysis_text.setMinimumWidth(280)
        analysis_layout = QVBoxLayout()
        analysis_layout.addWidget(self.day_analysis_title)
        analysis_layout.addWidget(self.day_analysis_text, 1)
        self.day_analysis_group.setLayout(analysis_layout)

        self.day_analysis_group_cards = QGroupBox("Day analysis")
        self.day_analysis_title_cards = QLabel("Select to day")
        self.day_analysis_title_cards.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.day_analysis_text_cards = QPlainTextEdit()
        self.day_analysis_text_cards.setReadOnly(True)
        self.day_analysis_text_cards.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        self.day_analysis_text_cards.setMinimumWidth(280)
        analysis_cards_layout = QVBoxLayout()
        analysis_cards_layout.addWidget(self.day_analysis_title_cards)
        analysis_cards_layout.addWidget(self.day_analysis_text_cards, 1)
        self.day_analysis_group_cards.setLayout(analysis_cards_layout)

        # Calendar tab was removed; keep day-analysis references pointing to the
        # active cards panel to avoid dangling Qt object references.
        self.day_analysis_title = self.day_analysis_title_cards
        self.day_analysis_text = self.day_analysis_text_cards

        calendar_with_analysis_layout = QHBoxLayout()
        calendar_with_analysis_layout.addLayout(calendar_layout, 1)
        calendar_with_analysis_layout.addWidget(self.day_analysis_group)
        calendar_layout.addWidget(calendar_title)
        calendar_layout.addWidget(self.calendar_view, 1)
        tab_calendar_view.setLayout(calendar_with_analysis_layout)

        cards_layout = QVBoxLayout()
        cards_title = QLabel("Calendar cards view")
        cards_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.calendar_cards_view = RevenueMonthGridWidget()
        self.calendar_cards_view.day_clicked.connect(self.on_calendar_date_clicked)
        cards_layout.addWidget(cards_title)
        cards_layout.addWidget(self.calendar_cards_view, 1)
        cards_with_analysis_layout = QHBoxLayout()
        cards_with_analysis_layout.addLayout(cards_layout, 1)
        cards_with_analysis_layout.addWidget(self.day_analysis_group_cards)
        tab_calendar_cards_view.setLayout(cards_with_analysis_layout)

        weekly_layout = QVBoxLayout()
        weekly_title = QLabel("Weekly view")
        weekly_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.weekly_view = RevenueWeekWidget()
        self.weekly_view.week_changed.connect(self.on_week_changed)
        weekly_layout.addWidget(weekly_title)
        self.weekly_view.setMaximumHeight(220)
        weekly_layout.addWidget(self.weekly_view)
        weekly_layout.addStretch(1)

        self.week_analysis_group = QGroupBox("Week analysis")
        self.week_analysis_title = QLabel("Select to week")
        self.week_analysis_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.week_analysis_text = QPlainTextEdit()
        self.week_analysis_text.setReadOnly(True)
        self.week_analysis_text.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        self.week_analysis_text.setMinimumWidth(300)
        week_analysis_layout = QVBoxLayout()
        week_analysis_layout.addWidget(self.week_analysis_title)
        week_analysis_layout.addWidget(self.week_analysis_text, 1)
        self.week_analysis_group.setLayout(week_analysis_layout)

        weekly_with_analysis_layout = QHBoxLayout()
        weekly_with_analysis_layout.addLayout(weekly_layout, 1)
        weekly_with_analysis_layout.addWidget(self.week_analysis_group)
        tab_weekly_view.setLayout(weekly_with_analysis_layout)

        yearly_layout = QVBoxLayout()
        yearly_title = QLabel("Yearly view")
        yearly_title.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.yearly_view = RevenueYearWidget()
        self.yearly_view.month_changed.connect(self.on_month_changed)
        yearly_layout.addWidget(yearly_title)
        yearly_layout.addWidget(self.yearly_view, 1)

        self.month_analysis_group = QGroupBox("Month analysis")
        self.month_analysis_title = QLabel("Select to month")
        self.month_analysis_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.month_analysis_text = QPlainTextEdit()
        self.month_analysis_text.setReadOnly(True)
        self.month_analysis_text.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        self.month_analysis_text.setMinimumWidth(300)
        month_analysis_layout = QVBoxLayout()
        month_analysis_layout.addWidget(self.month_analysis_title)
        month_analysis_layout.addWidget(self.month_analysis_text, 1)
        self.month_analysis_group.setLayout(month_analysis_layout)

        yearly_with_analysis_layout = QHBoxLayout()
        yearly_with_analysis_layout.addLayout(yearly_layout, 1)
        yearly_with_analysis_layout.addWidget(self.month_analysis_group)
        tab_yearly_view.setLayout(yearly_with_analysis_layout)

        weekday_layout = QVBoxLayout()
        weekday_controls_layout = QHBoxLayout()
        self.weekday_scope_combo = QComboBox()
        self.weekday_scope_combo.addItems(["Month", "AÃ±o"])
        self.weekday_scope_combo.currentTextChanged.connect(self.refresh_weekday_view)
        self.weekday_anchor_date = QDateEdit()
        self.weekday_anchor_date.setCalendarPopup(True)
        self.weekday_anchor_date.setDisplayFormat("yyyy-MM-dd")
        self.weekday_anchor_date.setDate(QDate.currentDate())
        self.weekday_anchor_date.dateChanged.connect(self.refresh_weekday_view)
        weekday_controls_layout.addWidget(QLabel("Rango:"))
        weekday_controls_layout.addWidget(self.weekday_scope_combo)
        weekday_controls_layout.addWidget(QLabel("Base date:"))
        weekday_controls_layout.addWidget(self.weekday_anchor_date)
        weekday_controls_layout.addStretch(1)
        weekday_layout.addLayout(weekday_controls_layout)
        self.weekday_view = RevenueWeekdayWidget()
        self.weekday_view.weekday_changed.connect(self.on_weekday_changed)
        self.weekday_view.setMaximumHeight(220)
        weekday_layout.addWidget(self.weekday_view)
        weekday_layout.addStretch(1)

        self.weekday_analysis_group = QGroupBox("Weekday analysis")
        self.weekday_analysis_title = QLabel("Select to weekday")
        self.weekday_analysis_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.weekday_analysis_text = QPlainTextEdit()
        self.weekday_analysis_text.setReadOnly(True)
        self.weekday_analysis_text.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 10pt;")
        self.weekday_analysis_text.setMinimumWidth(300)
        weekday_analysis_layout = QVBoxLayout()
        weekday_analysis_layout.addWidget(self.weekday_analysis_title)
        weekday_analysis_layout.addWidget(self.weekday_analysis_text, 1)
        self.weekday_analysis_group.setLayout(weekday_analysis_layout)

        weekday_with_analysis_layout = QHBoxLayout()
        weekday_with_analysis_layout.addLayout(weekday_layout, 1)
        weekday_with_analysis_layout.addWidget(self.weekday_analysis_group)
        tab_weekday_view.setLayout(weekday_with_analysis_layout)

        self.load_calendar_revenue()

        tabs.addTab(tab_database_view, "Database view")
        tabs.addTab(tab_calendar_cards_view, "Calendar")
        tabs.addTab(tab_weekly_view, "Weekly")
        tabs.addTab(tab_yearly_view, "Yearly")
        tabs.addTab(tab_weekday_view, "By Weekday")
        main_layout = QVBoxLayout()
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
 
    def button_add_registry_clicked(self):
        self.open_new_ticket_modal()

    def button_delete_clicked(self):
        self.controller.button_delete_clicked()
    
    def button_search_clicked(self):
        created_at_filter = ""
        if self.tab2_form_date_enabled.isChecked():
            created_at_filter = self.tab2_form_line_date.date().toString("yyyy-MM-dd")
        service_date_filter = ""
        if self.tab2_form_service_date_enabled.isChecked():
            service_date_filter = self.tab2_form_line_service_date.date().toString("yyyy-MM-dd")
        filters = {
            "id": self.tab2_form_line_order_id.text(),
            "created_at": created_at_filter,
            "service_date": service_date_filter,
            "table_name": self.tab2_form_line_table.currentText(),
            "name": self.tab2_form_line_name.text(),
            "status": self.tab2_form_line_status.currentText(),
            "to_go": self.tab2_form_line_to_go.currentText(),
            "total_amount_op": self.tab2_form_total_amount_operator.currentText(),
            "total_amount": self.tab2_form_line_total_amount.text(),
            "amount_paid_op": self.tab2_form_amount_paid_operator.currentText(),
            "amount_paid": self.tab2_form_line_amount_paid.text()
        }
        self.controller.search(filters)

    def button_delete_clicked(self):
        #index = self.table_view.currentIndex()
        
        #if not index.isValid():
        #    QMessageBox.warning(self, "Warning", "Select to row first")
        #    return
        
        #row = index.row()
        #self.controller.button_delete_clicked(row)
        self.controller.delete_selected()
        self.load_calendar_revenue()
        # Notify main order management view (if present) to reload open orders
        try:
            top = self.window()
            if top is not None and hasattr(top, "order_management_view"):
                # Refresh orders from database to get updated data
                if hasattr(top.order_management_view, "refresh_orders_from_database"):
                    top.order_management_view.refresh_orders_from_database()
                else:
                    # Fallback to manual refresh
                    main_repo = OrderRepository("orders.db")
                    open_orders = main_repo.load_open_orders()
                    # Check if active order was deleted
                    active_order = top.order_management_view.controller.get_active_order()
                    if active_order and active_order.id not in open_orders:
                        # Order was deleted, clear everything like remove_order_clicked does
                        top.order_management_view.controller.clear_active_selection()
                        top.order_management_view.orders_list_widget.set_active(None)
                        top.order_management_view.in_progress_orders_list_widget.set_active(None)
                        top.order_management_view.dish_list_widget.clear()
                        top.order_management_view.selected_products_list.clear()
                        top.order_management_view.update_active_dish_total_label()
                        top.order_management_view.update_active_order_total_label()
                        top.order_management_view.update_ticket_management_visibility()
                        top.order_management_view.clear_form()
                    # Update orders from database
                    top.order_management_view.controller.set_orders(open_orders)
                    top.order_management_view.render_orders()
        except Exception:
            pass

    def button_edit_clicked(self):
        index = self.table_view.currentIndex()

        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Select to row first")
            return
        
        row = index.row()
        model = self.table_view.model()
        order_id = str(model._data[row][0])
        self.open_ticket_modal(order_id)
    
    def update_selection_table(self, selected=None, deselected=None):
        self.controller.update_selection_table()
        self.update_ticket_preview_from_current_row()

    def selected_double_click(self, index):
        self.controller.selected_double_click(index)

    def button_bulk_edit_clicked(self):
        updates = {}

        if self.tab2_form_line_name.text():
            updates["name"] = self.tab2_form_line_name.text()

        if self.tab2_form_line_labels.text():
            updates["labels"] = self.tab2_form_line_labels.text()

        if self.tab2_form_date_enabled.isChecked():
            updates["created_at"] = self.tab2_form_line_date.date().toString("yyyy-MM-dd")

        if self.tab2_form_line_body.text():
            updates["body"] = self.tab2_form_line_body.text()

        if not updates:
            QMessageBox.warning(
                self,
                "Warning",
                "No fields to update"
            )
            return
        selected_rows = self.selection_table_model._data
        ids = [row[0] for row in selected_rows]
        self.controller.bulk_edit_clicked(ids, updates)

    def open_ticket_modal(self, order_id: str):
        repository = OrderRepository("orders.db")
        order = repository.load_order(order_id)
        if not order:
            QMessageBox.warning(self, "Ticket not found", f"Ticket {order_id} was not found.")
            return

        modal = QDialog(self)
        modal.setWindowTitle(f"Edit ticket {order_id}")
        modal.resize(1200, 760)
        modal_layout = QVBoxLayout(modal)

        order_controller = OrderController(repository)
        order_management_view = OrderManagementView(order_controller, show_orders_panel=False)
        order_management_view.set_single_order(order)
        modal_layout.addWidget(order_management_view)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save changes")
        close_button = QPushButton("Close")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(close_button)
        modal_layout.addLayout(buttons_layout)

        def save_changes():
            order_management_view.register_form_data()
            active_order = order_controller.get_active_order()
            if not active_order:
                QMessageBox.warning(modal, "No ticket", "There is no active ticket to save.")
                return
            try:
                repository.save_order(active_order)
            except Exception as exc:
                QMessageBox.critical(modal, "Error saving", f"Could not save the ticket.\n\nDetails: {exc}")
                return
            self.controller.refresh_table()
            self.load_calendar_revenue()
            # Notify main order management view (if present) to reload open orders
            try:
                top = self.window()
                if top is not None and hasattr(top, "order_management_view"):
                    # Refresh orders from database to get updated data
                    if hasattr(top.order_management_view, "refresh_orders_from_database"):
                        top.order_management_view.refresh_orders_from_database()
                    else:
                        # Fallback to manual refresh if method doesn't exist
                        main_repo = OrderRepository("orders.db")
                        open_orders = main_repo.load_open_orders()
                        top.order_management_view.controller.set_orders(open_orders)
                        top.order_management_view.render_orders()
                        # Re-select the updated order if it still exists
                        if active_order.id in open_orders:
                            top.order_management_view.order_selected(active_order.id)
            except Exception:
                pass
            QMessageBox.information(modal, "Saved", "Changes saved successfully.")

        save_button.clicked.connect(save_changes)
        close_button.clicked.connect(modal.accept)
        modal.exec()

    def open_new_ticket_modal(self):
        repository = OrderRepository("orders.db")
        order_controller = OrderController(repository)
        order_management_view = OrderManagementView(order_controller, show_orders_panel=False)

        new_order = order_controller.new_order_button_clicked()
        order_management_view.set_single_order(new_order)

        modal = QDialog(self)
        modal.setWindowTitle("New order")
        modal.resize(1200, 760)
        modal_layout = QVBoxLayout(modal)
        modal_layout.addWidget(order_management_view)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save new order")
        close_button = QPushButton("Close")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(close_button)
        modal_layout.addLayout(buttons_layout)

        def save_new_order():
            order_management_view.register_form_data()
            active_order = order_controller.get_active_order()
            if not active_order:
                QMessageBox.warning(modal, "No ticket", "There is no active ticket to save.")
                return
            try:
                repository.save_order(active_order)
            except Exception as exc:
                QMessageBox.critical(modal, "Error saving", f"Could not save the order.\n\nDetails: {exc}")
                return
            self.controller.refresh_table()
            self.load_calendar_revenue()
            # Notify main order management view (if present) to reload open orders
            try:
                top = self.window()
                if top is not None and hasattr(top, "order_management_view"):
                    main_repo = OrderRepository("orders.db")
                    open_orders = main_repo.load_open_orders()
                    top.order_management_view.controller.set_orders(open_orders)
                    top.order_management_view.render_orders()
            except Exception:
                pass
            QMessageBox.information(modal, "Saved", "Order created successfully.")
            modal.accept()

        save_button.clicked.connect(save_new_order)
        close_button.clicked.connect(modal.accept)
        modal.exec()

    def update_ticket_preview_from_current_row(self):
        index = self.table_view.currentIndex()
        if not index.isValid():
            self.ticket_preview.clear()
            return

        row = index.row()
        model = self.table_view.model()
        order_id = str(model._data[row][0])

        repository = OrderRepository("orders.db")
        order = repository.load_order(order_id)
        if not order:
            self.ticket_preview.setPlainText(f"Ticket {order_id} was not found.")
            return

        self.ticket_preview.setPlainText(TicketBody.build(order))

    def _ticket_preview_width(self, font: QFont) -> int:
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance("M" * TicketBody.WIDTH)
        return text_width + 36

    def refresh_all_orders(self):
        """Refresh the orders table with all database records"""
        try:
            rows = Database("orders.db", "orders").fetch_all()
            headers = ["ID", "Created at", "Closed at", "Service date", "Name", "Table name", "Status", "To go", "Amount paid", "Total amount"]
            self.main_model.update_data(rows)
        except Exception:
            pass

    def load_calendar_revenue(self):
        try:
            rows = Database("orders.db", "orders").fetch_all()
        except Exception:
            rows = []

        revenue_map = {}
        for row in rows:
            date_key = self._calendar_date_from_order_row(row)
            if not date_key:
                continue
            amount_paid = self._to_float(row[8]) if len(row) > 8 else 0.0
            total_amount = self._to_float(row[9]) if len(row) > 9 else 0.0
            amount = amount_paid if amount_paid > 0 else total_amount
            revenue_map[date_key] = revenue_map.get(date_key, 0.0) + amount

        self._orders_rows_cache = rows
        if hasattr(self, "calendar_view") and hasattr(self.calendar_view, "set_revenue_map"):
            self.calendar_view.set_revenue_map(revenue_map)
        if hasattr(self, "calendar_cards_view") and hasattr(self.calendar_cards_view, "set_revenue_map"):
            self.calendar_cards_view.set_revenue_map(revenue_map)
        if hasattr(self, "weekly_view") and hasattr(self.weekly_view, "set_revenue_map"):
            self.weekly_view.set_revenue_map(revenue_map)
        if hasattr(self, "yearly_view") and hasattr(self.yearly_view, "set_revenue_map"):
            self.yearly_view.set_revenue_map(revenue_map)
        self.refresh_weekday_view()
        self.update_day_analysis(self._selected_analysis_date)

    def _calendar_date_from_order_row(self, row):
        candidates = []
        if len(row) > 3:
            candidates.append(row[3])  # service_date
        if len(row) > 1:
            candidates.append(row[1])  # created_at
        if len(row) > 2:
            candidates.append(row[2])  # closed_at
        for value in candidates:
            text = str(value or "").strip()
            if len(text) >= 10:
                date_text = text[:10]
                if QDate.fromString(date_text, "yyyy-MM-dd").isValid():
                    return date_text
        return ""

    def _to_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def on_calendar_date_clicked(self, date):
        if not isinstance(date, QDate):
            return
        self._selected_analysis_date = date
        self.update_day_analysis(date)

    def on_week_changed(self, week_start, week_end):
        if not isinstance(week_start, QDate):
            return
        self.update_week_analysis(week_start, week_end)

    def on_month_changed(self, month_start, month_end):
        if not isinstance(month_start, QDate):
            return
        self.update_month_analysis(month_start, month_end)

    def on_weekday_changed(self, weekday_number):
        self.update_weekday_analysis(int(weekday_number))

    def refresh_weekday_view(self, _=None):
        if not hasattr(self, "weekday_view"):
            return
        stats, range_label = self._compute_weekday_stats_for_selected_range()
        self._weekday_range_label = range_label
        self._weekday_stats_cache = stats
        self.weekday_view.set_weekday_stats(stats)
        self.update_weekday_analysis(self.weekday_view.selected_weekday)

    def update_day_analysis(self, date):
        if not hasattr(self, "day_analysis_text"):
            return
        date_key = date.toString("yyyy-MM-dd")
        rows = []
        for row in self._orders_rows_cache:
            if self._calendar_date_from_order_row(row) == date_key:
                rows.append(row)

        if not rows:
            self.day_analysis_title.setText(f"Day: {date_key}")
            self.day_analysis_text.setPlainText("No records for this day.")
            if hasattr(self, "day_analysis_title_cards"):
                self.day_analysis_title_cards.setText(f"Day: {date_key}")
            if hasattr(self, "day_analysis_text_cards"):
                self.day_analysis_text_cards.setPlainText("No records for this day.")
            return

        total_revenue = 0.0
        paid_revenue = 0.0
        closed_count = 0
        to_go_count = 0
        tables = {}
        for row in rows:
            amount_paid = self._to_float(row[8]) if len(row) > 8 else 0.0
            total_amount = self._to_float(row[9]) if len(row) > 9 else 0.0
            total_revenue += (amount_paid if amount_paid > 0 else total_amount)
            paid_revenue += amount_paid
            status = str(row[6]).strip().lower() if len(row) > 6 else ""
            if status == "closed":
                closed_count += 1
            to_go_raw = str(row[7]).strip().lower() if len(row) > 7 else ""
            if to_go_raw in {"1", "true", "yes"}:
                to_go_count += 1
            table_name = str(row[5]).strip() if len(row) > 5 else ""
            if table_name:
                tables[table_name] = tables.get(table_name, 0) + 1

        orders_count = len(rows)
        avg_ticket = (total_revenue / orders_count) if orders_count else 0.0
        avg_total = total_revenue
        top_table = "-"
        if tables:
            top_table = max(tables.items(), key=lambda kv: kv[1])[0]
        top_dish_name, top_dish_qty = self._top_dish_for_rows(rows)
        top_food_name, top_food_qty, top_drink_name, top_drink_qty = self._top_food_and_drink_for_rows(rows)
        peak_hours_text = self._peak_hours_text_for_rows(rows)

        self.day_analysis_title.setText(f"Day: {date_key}")
        analysis_text = (
            f"Orders: {orders_count}\n"
            f"Total: ${total_revenue:,.2f}\n"
            f"Average total (day): ${avg_total:,.2f}\n"
            f"Paid: ${paid_revenue:,.2f}\n"
            f"Average ticket: ${avg_ticket:,.2f}\n"
            f"Closed: {closed_count}\n"
            f"To go: {to_go_count}\n"
            f"Most used table: {top_table}\n"
            f"Most purchased dish: {top_dish_name} ({top_dish_qty})\n"
            f"Most ordered food: {top_food_name} ({top_food_qty})\n"
            f"Most ordered drink: {top_drink_name} ({top_drink_qty})\n"
            f"Peak hours: {peak_hours_text}"
        )
        self.day_analysis_text.setPlainText(analysis_text)
        if hasattr(self, "day_analysis_title_cards"):
            self.day_analysis_title_cards.setText(f"Day: {date_key}")
        if hasattr(self, "day_analysis_text_cards"):
            self.day_analysis_text_cards.setPlainText(analysis_text)

    def _top_dish_for_rows(self, rows):
        counts = {}
        repository = OrderRepository("orders.db")
        for row in rows:
            order_id = str(row[0]).strip() if len(row) > 0 else ""
            if not order_id:
                continue
            order = repository.load_order(order_id)
            if not order:
                continue
            for dish in order.dishes.values():
                for product in dish.products.values():
                    display_name = (getattr(product, "display_name", None) or product.name or "").strip()
                    if not display_name:
                        continue
                    qty = int(getattr(product, "quantity", 0) or 0)
                    counts[display_name] = counts.get(display_name, 0) + max(qty, 0)
        if not counts:
            return "-", 0
        name, qty = max(counts.items(), key=lambda kv: kv[1])
        return name, qty

    def _top_food_and_drink_for_rows(self, rows):
        type_map = self._menu_product_type_map()
        food_counts = {}
        drink_counts = {}
        repository = OrderRepository("orders.db")
        for row in rows:
            order_id = str(row[0]).strip() if len(row) > 0 else ""
            if not order_id:
                continue
            order = repository.load_order(order_id)
            if not order:
                continue
            for dish in order.dishes.values():
                for product in dish.products.values():
                    product_name = (product.name or "").strip()
                    display_name = (getattr(product, "display_name", None) or product_name).strip()
                    if not display_name:
                        continue
                    qty = int(getattr(product, "quantity", 0) or 0)
                    if qty <= 0:
                        continue
                    product_type = type_map.get(product_name.lower(), "")
                    if product_type in {"food", "comida"}:
                        food_counts[display_name] = food_counts.get(display_name, 0) + qty
                    elif product_type in {"drink", "bebida"}:
                        drink_counts[display_name] = drink_counts.get(display_name, 0) + qty

        food_name, food_qty = ("-", 0)
        drink_name, drink_qty = ("-", 0)
        if food_counts:
            food_name, food_qty = max(food_counts.items(), key=lambda kv: kv[1])
        if drink_counts:
            drink_name, drink_qty = max(drink_counts.items(), key=lambda kv: kv[1])
        return food_name, food_qty, drink_name, drink_qty

    def _menu_product_type_map(self):
        try:
            menu_rows = MenuDatabase("orders.db", "menu").fetch_all()
        except Exception:
            menu_rows = []
        product_type_map = {}
        for row in menu_rows:
            if len(row) < 8:
                continue
            name = str(row[1] or "").strip().lower()
            product_type = str(row[7] or "").strip().lower()
            if not name:
                continue
            if product_type not in {"food", "drink", "comida", "bebida"}:
                product_type = "food"
            product_type_map[name] = product_type
        return product_type_map

    def _extract_order_hour(self, row):
        text = str(row[1] if len(row) > 1 else "").strip()  # created_at
        if len(text) >= 13 and text[10] in {"T", " "}:
            hour_text = text[11:13]
        elif len(text) >= 2:
            hour_text = text[:2]
        else:
            return -1
        try:
            hour = int(hour_text)
            if 0 <= hour <= 23:
                return hour
        except ValueError:
            return -1
        return -1

    def _peak_hours_text_for_rows(self, rows, top_n=3):
        hour_counts = {}
        for row in rows:
            hour = self._extract_order_hour(row)
            if hour < 0:
                continue
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        if not hour_counts:
            return "-"
        ranked = sorted(hour_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
        return ", ".join([f"{hour:02d}:00 ({count})" for hour, count in ranked])

    def update_week_analysis(self, week_start, week_end):
        if not hasattr(self, "week_analysis_text"):
            return
        rows = []
        for row in self._orders_rows_cache:
            date_text = self._calendar_date_from_order_row(row)
            if not date_text:
                continue
            date_value = QDate.fromString(date_text, "yyyy-MM-dd")
            if not date_value.isValid():
                continue
            if week_start <= date_value <= week_end:
                rows.append(row)

        range_text = f"{week_start.toString('yyyy-MM-dd')} to {week_end.toString('yyyy-MM-dd')}"
        self.week_analysis_title.setText(f"Week: {range_text}")
        if not rows:
            self.week_analysis_text.setPlainText("No records for this week.")
            return

        total_revenue = 0.0
        paid_revenue = 0.0
        closed_count = 0
        to_go_count = 0
        tables = {}
        for row in rows:
            amount_paid = self._to_float(row[8]) if len(row) > 8 else 0.0
            total_amount = self._to_float(row[9]) if len(row) > 9 else 0.0
            total_revenue += (amount_paid if amount_paid > 0 else total_amount)
            paid_revenue += amount_paid
            status = str(row[6]).strip().lower() if len(row) > 6 else ""
            if status == "closed":
                closed_count += 1
            to_go_raw = str(row[7]).strip().lower() if len(row) > 7 else ""
            if to_go_raw in {"1", "true", "yes"}:
                to_go_count += 1
            table_name = str(row[5]).strip() if len(row) > 5 else ""
            if table_name:
                tables[table_name] = tables.get(table_name, 0) + 1

        orders_count = len(rows)
        avg_ticket = (total_revenue / orders_count) if orders_count else 0.0
        day_count = max(1, week_start.daysTo(week_end) + 1)
        avg_total = total_revenue / day_count
        top_table = "-"
        if tables:
            top_table = max(tables.items(), key=lambda kv: kv[1])[0]
        top_dish_name, top_dish_qty = self._top_dish_for_rows(rows)
        top_food_name, top_food_qty, top_drink_name, top_drink_qty = self._top_food_and_drink_for_rows(rows)
        peak_hours_text = self._peak_hours_text_for_rows(rows)
        analysis_text = (
            f"Orders: {orders_count}\n"
            f"Total: ${total_revenue:,.2f}\n"
            f"Average total (week): ${avg_total:,.2f}\n"
            f"Paid: ${paid_revenue:,.2f}\n"
            f"Average ticket: ${avg_ticket:,.2f}\n"
            f"Closed: {closed_count}\n"
            f"To go: {to_go_count}\n"
            f"Most used table: {top_table}\n"
            f"Most purchased dish: {top_dish_name} ({top_dish_qty})\n"
            f"Most ordered food: {top_food_name} ({top_food_qty})\n"
            f"Most ordered drink: {top_drink_name} ({top_drink_qty})\n"
            f"Peak hours: {peak_hours_text}"
        )
        self.week_analysis_text.setPlainText(analysis_text)

    def update_month_analysis(self, month_start, month_end):
        if not hasattr(self, "month_analysis_text"):
            return
        rows = []
        for row in self._orders_rows_cache:
            date_text = self._calendar_date_from_order_row(row)
            if not date_text:
                continue
            date_value = QDate.fromString(date_text, "yyyy-MM-dd")
            if not date_value.isValid():
                continue
            if month_start <= date_value <= month_end:
                rows.append(row)

        range_text = f"{month_start.toString('yyyy-MM-dd')} to {month_end.toString('yyyy-MM-dd')}"
        self.month_analysis_title.setText(f"Month: {range_text}")
        if not rows:
            self.month_analysis_text.setPlainText("No records for this month.")
            return

        total_revenue = 0.0
        paid_revenue = 0.0
        closed_count = 0
        to_go_count = 0
        tables = {}
        for row in rows:
            amount_paid = self._to_float(row[8]) if len(row) > 8 else 0.0
            total_amount = self._to_float(row[9]) if len(row) > 9 else 0.0
            total_revenue += (amount_paid if amount_paid > 0 else total_amount)
            paid_revenue += amount_paid
            status = str(row[6]).strip().lower() if len(row) > 6 else ""
            if status == "closed":
                closed_count += 1
            to_go_raw = str(row[7]).strip().lower() if len(row) > 7 else ""
            if to_go_raw in {"1", "true", "yes"}:
                to_go_count += 1
            table_name = str(row[5]).strip() if len(row) > 5 else ""
            if table_name:
                tables[table_name] = tables.get(table_name, 0) + 1

        orders_count = len(rows)
        avg_ticket = (total_revenue / orders_count) if orders_count else 0.0
        day_count = max(1, month_start.daysTo(month_end) + 1)
        avg_total = total_revenue / day_count
        top_table = "-"
        if tables:
            top_table = max(tables.items(), key=lambda kv: kv[1])[0]
        top_dish_name, top_dish_qty = self._top_dish_for_rows(rows)
        top_food_name, top_food_qty, top_drink_name, top_drink_qty = self._top_food_and_drink_for_rows(rows)
        peak_hours_text = self._peak_hours_text_for_rows(rows)
        analysis_text = (
            f"Orders: {orders_count}\n"
            f"Total: ${total_revenue:,.2f}\n"
            f"Average total (month): ${avg_total:,.2f}\n"
            f"Paid: ${paid_revenue:,.2f}\n"
            f"Average ticket: ${avg_ticket:,.2f}\n"
            f"Closed: {closed_count}\n"
            f"To go: {to_go_count}\n"
            f"Most used table: {top_table}\n"
            f"Most purchased dish: {top_dish_name} ({top_dish_qty})\n"
            f"Most ordered food: {top_food_name} ({top_food_qty})\n"
            f"Most ordered drink: {top_drink_name} ({top_drink_qty})\n"
            f"Peak hours: {peak_hours_text}"
        )
        self.month_analysis_text.setPlainText(analysis_text)

    def update_weekday_analysis(self, weekday_number):
        if not hasattr(self, "weekday_analysis_text"):
            return
        weekday_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
        rows = self._rows_for_weekday_in_selected_range(weekday_number)

        day_name = weekday_names.get(weekday_number, str(weekday_number))
        range_label = getattr(self, "_weekday_range_label", "")
        title = f"Weekday: {day_name}"
        if range_label:
            title += f" ({range_label})"
        self.weekday_analysis_title.setText(title)
        if not rows:
            self.weekday_analysis_text.setPlainText("No records for this weekday.")
            return

        total_revenue = 0.0
        paid_revenue = 0.0
        closed_count = 0
        to_go_count = 0
        tables = {}
        for row in rows:
            amount_paid = self._to_float(row[8]) if len(row) > 8 else 0.0
            total_amount = self._to_float(row[9]) if len(row) > 9 else 0.0
            total_revenue += (amount_paid if amount_paid > 0 else total_amount)
            paid_revenue += amount_paid
            status = str(row[6]).strip().lower() if len(row) > 6 else ""
            if status == "closed":
                closed_count += 1
            to_go_raw = str(row[7]).strip().lower() if len(row) > 7 else ""
            if to_go_raw in {"1", "true", "yes"}:
                to_go_count += 1
            table_name = str(row[5]).strip() if len(row) > 5 else ""
            if table_name:
                tables[table_name] = tables.get(table_name, 0) + 1

        orders_count = len(rows)
        avg_ticket = (total_revenue / orders_count) if orders_count else 0.0
        top_table = "-"
        if tables:
            top_table = max(tables.items(), key=lambda kv: kv[1])[0]
        top_dish_name, top_dish_qty = self._top_dish_for_rows(rows)
        top_food_name, top_food_qty, top_drink_name, top_drink_qty = self._top_food_and_drink_for_rows(rows)
        peak_hours_text = self._peak_hours_text_for_rows(rows)
        stats = getattr(self, "_weekday_stats_cache", {}).get(weekday_number, {})
        day_count = int(stats.get("day_count", 0) or 0)
        avg_total = float(stats.get("avg_total", 0.0) or 0.0)
        avg_orders = float(stats.get("avg_orders", 0.0) or 0.0)
        analysis_text = (
            f"Calendar repeats: {day_count}\n"
            f"Orders: {orders_count}\n"
            f"Total: ${total_revenue:,.2f}\n"
            f"Average total ({day_name}): ${avg_total:,.2f}\n"
            f"Paid: ${paid_revenue:,.2f}\n"
            f"Average orders ({day_name}): {avg_orders:.2f}\n"
            f"Average ticket: ${avg_ticket:,.2f}\n"
            f"Closed: {closed_count}\n"
            f"To go: {to_go_count}\n"
            f"Most used table: {top_table}\n"
            f"Most purchased dish: {top_dish_name} ({top_dish_qty})\n"
            f"Most ordered food: {top_food_name} ({top_food_qty})\n"
            f"Most ordered drink: {top_drink_name} ({top_drink_qty})\n"
            f"Peak hours: {peak_hours_text}"
        )
        self.weekday_analysis_text.setPlainText(analysis_text)

    def _selected_weekday_range(self):
        anchor = self.weekday_anchor_date.date() if hasattr(self, "weekday_anchor_date") else QDate.currentDate()
        scope = self.weekday_scope_combo.currentText() if hasattr(self, "weekday_scope_combo") else "Month"
        if str(scope).strip().lower() == "year":
            start = QDate(anchor.year(), 1, 1)
            end = QDate(anchor.year(), 12, 31)
            label = str(anchor.year())
            return start, end, label
        start = QDate(anchor.year(), anchor.month(), 1)
        end = start.addMonths(1).addDays(-1)
        label = start.toString("yyyy-MM")
        return start, end, label

    def _rows_for_weekday_in_selected_range(self, weekday_number):
        start, end, _ = self._selected_weekday_range()
        rows = []
        for row in self._orders_rows_cache:
            date_text = self._calendar_date_from_order_row(row)
            if not date_text:
                continue
            date_value = QDate.fromString(date_text, "yyyy-MM-dd")
            if not date_value.isValid():
                continue
            if start <= date_value <= end and date_value.dayOfWeek() == int(weekday_number):
                rows.append(row)
        return rows

    def _compute_weekday_stats_for_selected_range(self):
        start, end, label = self._selected_weekday_range()
        stats = {
            i: {"sum_total": 0.0, "orders": 0, "day_count": 0, "avg_total": 0.0, "avg_orders": 0.0}
            for i in range(1, 8)
        }

        cursor = QDate(start)
        while cursor <= end:
            stats[cursor.dayOfWeek()]["day_count"] += 1
            cursor = cursor.addDays(1)

        for row in self._orders_rows_cache:
            date_text = self._calendar_date_from_order_row(row)
            if not date_text:
                continue
            date_value = QDate.fromString(date_text, "yyyy-MM-dd")
            if not date_value.isValid() or not (start <= date_value <= end):
                continue
            wd = date_value.dayOfWeek()
            amount_paid = self._to_float(row[8]) if len(row) > 8 else 0.0
            total_amount = self._to_float(row[9]) if len(row) > 9 else 0.0
            amount = amount_paid if amount_paid > 0 else total_amount
            stats[wd]["sum_total"] += amount
            stats[wd]["orders"] += 1

        for wd in range(1, 8):
            days = max(1, stats[wd]["day_count"])
            stats[wd]["avg_total"] = stats[wd]["sum_total"] / days
            stats[wd]["avg_orders"] = stats[wd]["orders"] / days

        return stats, label

        #layout = QVBoxLayout()
        #layout.addWidget(tittle)

        #self.setLayout(layout)


