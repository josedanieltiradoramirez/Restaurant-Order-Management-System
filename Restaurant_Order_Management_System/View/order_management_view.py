from PyQt6.QtWidgets import (QWidget, QLabel, QVBoxLayout,
                            QPushButton, QLineEdit, QHBoxLayout, 
                            QVBoxLayout, QTabWidget, QTableView, QDateEdit,
                            QFormLayout, QMessageBox, QGroupBox, QCheckBox, QStackedLayout,
                            QDialog, QPlainTextEdit, QFrame, QComboBox)
from PyQt6.QtGui import QFont, QTextDocument, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtWidgets import QListWidgetItem
from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo
from View.product_card import ProductCard
from View.order_card import OrderCard
from View.dish_card import DishCard
from PyQt6.QtWidgets import QScrollArea
from View.product_grid import ProductsGrid
from View.order_grid import OrderGrid
from Model.order import Order
from View.items_list import ItemsList
from Model.dish import Dish
from View.order_element_card import OrderElementCard
from Model.ticket_body import TicketBody
import os
import html
import ctypes
from datetime import date
from ctypes import wintypes
from types import SimpleNamespace


class OrderManagementView(QWidget):
    def __init__(self, controller, show_orders_panel=True):
        super().__init__()
        self.controller = controller
        self.show_orders_panel = show_orders_panel
        self._loading_order_form = False
        # PRINTER CONNECTION
        self.ticket_printer_name = (
            os.getenv("TICKET_PRINTER_NAME", "").strip() or "BlueTooth Printer"
        )
        self.ticket_logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logo_tacos_el_padrino.jpeg",
        )
        self.unlocked_closed_order_ids = set()
        main_layout = QHBoxLayout()

        # NEW ORDERS LIST WIDGET
        self.orders_list_widget = ItemsList()
        
        # ORDERS IN PROGRES LIST WIDGET
        self.in_progress_orders_list_widget = ItemsList()
        self.orders_lists_tabs = None
        if self.show_orders_panel:
            self.orders_lists_tabs = QTabWidget()
            self.scroll_orders_list = QScrollArea()
            self.scroll_orders_list.setWidgetResizable(True)
            self.scroll_orders_list.setWidget(self.orders_list_widget)
            self.scroll_in_progress_orders_list = QScrollArea()
            self.scroll_in_progress_orders_list.setWidgetResizable(True)
            self.scroll_in_progress_orders_list.setWidget(self.in_progress_orders_list_widget)
            self.orders_lists_tabs.addTab(self.scroll_orders_list, "New")
            self.orders_lists_tabs.addTab(self.scroll_in_progress_orders_list, "In progress")

        # MENU
        self.products_grid = ProductsGrid()
        scroll_products_grid = QScrollArea()
        scroll_products_grid.setWidgetResizable(True)
        scroll_products_grid.setWidget(self.products_grid)
        self.load_products_from_menu_database()
        

        # FORM
        self.order_form = QFormLayout()
        self.order_form_name = QLineEdit()
        self.order_form_name.setPlaceholderText("Name")
        self.order_form_name.textChanged.connect(self.order_name_or_table_changed)
        self.order_form_service_date_label = QLabel("Service date:")
        self.order_form_service_date = QDateEdit()
        self.order_form_service_date.setCalendarPopup(True)
        self.order_form_service_date.setDisplayFormat("yyyy-MM-dd")
        self.order_form_service_date.setDate(QDate.currentDate())
        self.order_form_service_date.dateChanged.connect(lambda _: self.order_name_or_table_changed(None))
        self.order_form_table_label = QLabel("Table:")
        self.order_form_table_row_widget = QWidget()
        self.order_form_table_row_layout = QHBoxLayout(self.order_form_table_row_widget)
        self.order_form_table_row_layout.setContentsMargins(0, 0, 0, 0)
        self.order_form_table_row_layout.setSpacing(6)
        self.order_form_table_layout = QHBoxLayout()
        self.order_form_table_layout.setContentsMargins(0, 0, 0, 0)
        self.order_form_table_layout.setSpacing(4)
        self.order_form_table_items = []
        self.order_form_table_buttons = []
        self._order_form_table_selected_index = -1
        self._order_form_table_signals_blocked = False
        self.order_form_amount_paid = QLineEdit()
        self.order_form_amount_paid.setPlaceholderText("0.00")
        self.order_form_amount_paid.textChanged.connect(self.amount_paid_text_changed)
        self.order_form_to_go = QCheckBox("To go")
        self.order_form_to_go.setStyleSheet(
            "QCheckBox::indicator {"
            "  width: 16px;"
            "  height: 16px;"
            "}"
        )
        self.order_form_to_go.toggled.connect(self.order_to_go_toggled)
        self.order_form_additional_notes = QLineEdit()
        self.order_form_additional_notes.setPlaceholderText("Additional notes")
        self.order_form_additional_notes.textChanged.connect(self.order_name_or_table_changed)
        self.order_form_include_notes_in_ticket = QCheckBox("Include notes in ticket")
        self.order_form_include_notes_in_ticket.setChecked(False)
        self.order_form_include_notes_in_ticket.toggled.connect(self.order_name_or_table_changed)
        self.additional_notes_row_widget = QWidget()
        self.additional_notes_row_layout = QHBoxLayout(self.additional_notes_row_widget)
        self.additional_notes_row_layout.setContentsMargins(0, 0, 0, 0)
        self.additional_notes_row_layout.setSpacing(8)
        self.additional_notes_row_layout.addWidget(self.order_form_additional_notes, 1)
        self.additional_notes_row_layout.addWidget(self.order_form_include_notes_in_ticket, 0)
        self.order_name_row_widget = QWidget()
        self.order_name_row_layout = QHBoxLayout(self.order_name_row_widget)
        self.order_name_row_layout.setContentsMargins(0, 0, 0, 0)
        self.order_name_row_layout.setSpacing(8)
        self.order_form_name.setMaximumWidth(260)
        self.order_name_row_layout.addWidget(self.order_form_name, 0)
        self.order_name_row_layout.addWidget(self.order_form_to_go, 0)
        self.order_name_row_layout.addStretch(1)
        self.order_name_row_layout.addWidget(self.order_form_service_date_label, 0)
        self.order_name_row_layout.addWidget(self.order_form_service_date, 0)
        self.order_form_table_row_layout.addWidget(self.order_form_table_label, 0)
        self.order_form_table_row_layout.addLayout(self.order_form_table_layout, 1)

        self.load_tables_from_database()

        self.order_form.addRow("Name: ", self.order_name_row_widget)
        self.order_form.addRow(self.order_form_table_row_widget)
        self.order_form.addRow("Additional notes: ", self.additional_notes_row_widget)

        # SELECTED PRODUCTS
        self.selected_products_list = OrderGrid()
        scroll_selected_product_list = QScrollArea()
        scroll_selected_product_list.setWidgetResizable(True)
        scroll_selected_product_list.setWidget(self.selected_products_list)

        # SELECTED PRODUCTS TOTAL
        self.active_dish_total_label = QLabel()
        self.active_dish_total_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.active_dish_total_label.setStyleSheet("color: #6b7280;")
        self.update_active_dish_total_label()

        # DISH LIST
        self.dish_list_widget = ItemsList()
        scroll_dish_list_widget = QScrollArea()
        scroll_dish_list_widget.setWidgetResizable(True)
        scroll_dish_list_widget.setWidget(self.dish_list_widget)

        # SELECTED DISHES TOTAL
        self.active_order_total_label = QLabel()
        self.active_order_total_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        self.active_order_total_label.setStyleSheet("color: #6b7280;")
        self.cash_row_widget = QWidget()
        cash_row_layout = QHBoxLayout(self.cash_row_widget)
        cash_row_layout.setContentsMargins(0, 0, 0, 0)
        cash_row_layout.addWidget(QLabel("Cash: $"))
        cash_row_layout.addWidget(self.order_form_amount_paid)

        self.change_label = QLabel("Change: $0.00")
        self.change_label.setFont(QFont("Segoe UI", 9))
        self.change_label.setStyleSheet("color: #6b7280;")
        self.update_active_order_total_label()

        # BUTTONS
        new_order_button = QPushButton("New order")
        new_order_button.clicked.connect(self.new_order_button_clicked)
        self.new_dish_button = QPushButton("New dish")
        self.new_dish_button.clicked.connect(self.new_dish_button_clicked)
        self.preview_ticket_button = QPushButton("Preview ticket")
        self.preview_ticket_button.clicked.connect(self.show_ticket_preview)
        self.send_order_button = QPushButton("Print ticket")
        self.send_order_button.clicked.connect(self.send_order_button_clicked)
        self.mark_sent_button = QPushButton("Send")
        self.mark_sent_button.clicked.connect(self.mark_sent_button_clicked)
        self.change_status_button = QPushButton("Mark in progress")
        self.change_status_button.clicked.connect(self.change_status_button_clicked)
        self.close_order_button = QPushButton("Close order")
        self.close_order_button.clicked.connect(self.close_order_button_clicked)
        self.reopen_ticket_button = QPushButton("Reopen ticket")
        self.reopen_ticket_button.clicked.connect(self.reopen_ticket_button_clicked)
        self.toggle_ticket_edit_button = QPushButton("Enable ticket edit")
        self.toggle_ticket_edit_button.clicked.connect(self.toggle_ticket_edit_button_clicked)
        
        # Status dropdown for modal mode
        self.order_status_label = QLabel("Status: ")
        self.order_status_dropdown = QComboBox()
        self.order_status_dropdown.addItems(["New", "In progress", "Closed"])
        self.order_status_dropdown.currentTextChanged.connect(self.on_status_dropdown_changed)
        self.order_status_dropdown_container = QWidget()
        status_dropdown_layout = QHBoxLayout(self.order_status_dropdown_container)
        status_dropdown_layout.setContentsMargins(0, 0, 0, 0)
        status_dropdown_layout.addWidget(self.order_status_label)
        status_dropdown_layout.addWidget(self.order_status_dropdown)
        status_dropdown_layout.addStretch(1)

        # LAYOUTS
        first_column_layout = QVBoxLayout()
        self.ticket_management_panel = QWidget()
        second_column_layout = QVBoxLayout(self.ticket_management_panel)
        self.ticket_placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.ticket_placeholder)
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder_label = QLabel("Select an order")
        placeholder_label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        placeholder_label.setStyleSheet("color: #6b7280;")
        placeholder_layout.addWidget(placeholder_label)

        buttons_row_layout = QHBoxLayout()
        menu_group = QGroupBox("Menu")
        menu_group_layout = QVBoxLayout()
        menu_group_layout.addWidget(scroll_products_grid)
        menu_group.setLayout(menu_group_layout)

        order_content_group = QGroupBox("Order content")
        order_content_layout = QVBoxLayout()
        self.selected_order_folio_label = QLabel("ID: -")
        self.selected_order_folio_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        self.selected_order_folio_label.setStyleSheet("color: #4b5563; padding: 0;")
        order_content_layout.addWidget(self.selected_order_folio_label)
        order_content_layout.addLayout(self.order_form)
        order_content_layout.addWidget(scroll_selected_product_list, 3)
        order_content_layout.addWidget(self.active_dish_total_label)
        order_content_layout.addWidget(self.new_dish_button)
        order_content_layout.addWidget(scroll_dish_list_widget, 2)
        order_content_layout.addWidget(self.active_order_total_label)
        order_content_layout.addWidget(self.cash_row_widget)
        order_content_layout.addWidget(self.change_label)
        order_content_layout.addWidget(self._build_section_line())
        order_content_group.setLayout(order_content_layout)

        # SHOW ORDERS PANEL
        if self.show_orders_panel:
            orders_group = QGroupBox("Orders")
            orders_group_layout = QVBoxLayout()
            orders_group_layout.addWidget(self.orders_lists_tabs)
            orders_group_layout.addWidget(new_order_button)
            orders_group.setLayout(orders_group_layout)
            first_column_layout.addWidget(orders_group)
        first_column_layout.addWidget(menu_group)
        buttons_row_layout.addWidget(self.preview_ticket_button)
        buttons_row_layout.addWidget(self.send_order_button)
        buttons_row_layout.addWidget(self.mark_sent_button)
        # In management mode: show status buttons; in modal mode: show dropdown
        if self.show_orders_panel:
            buttons_row_layout.addWidget(self.change_status_button)
            buttons_row_layout.addWidget(self.close_order_button)
        else:
            buttons_row_layout.addWidget(self.order_status_dropdown_container)
            buttons_row_layout.addWidget(self.toggle_ticket_edit_button)
        order_content_layout.addLayout(buttons_row_layout)
        second_column_layout.addWidget(order_content_group)

        main_layout = QHBoxLayout()
        self.ticket_stack_container = QWidget()
        self.ticket_stack = QStackedLayout(self.ticket_stack_container)
        self.ticket_stack.addWidget(self.ticket_placeholder)
        self.ticket_stack.addWidget(self.ticket_management_panel)
        main_layout.addLayout(first_column_layout)
        main_layout.addWidget(self.ticket_stack_container)
        self.setLayout(main_layout)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.setInterval(800)
        self.autosave_timer.timeout.connect(self.persist_active_order)
        self.update_ticket_management_visibility()

    # METHODS
    def on_status_dropdown_changed(self, new_status):
        """Handle status dropdown change in modal mode"""
        if not hasattr(self, "_loading_order_form") or self._loading_order_form:
            return
        order = self.controller.get_active_order()
        if not order or order.status == new_status:
            return
        # In the CRUD "Edit Registry" modal we must not trigger the full
        # close-order workflow (which persists/removes the ticket from the view).
        # Instead, treat the dropdown as a simple field edit and let the modal
        # "Save changes" button persist it.
        if not self.show_orders_panel:
            order.set_status(new_status)
            self.update_ticket_management_visibility()
            self.apply_order_edit_mode()
            return

        # Full order-management mode behavior
        if new_status == "Closed":
            self.close_order_button_clicked()
        elif new_status == "In progress":
            self.change_status_button_clicked()
        elif new_status == "New":
            if order.status == "In progress":
                self.change_status_button_clicked()

    def set_single_order(self, order):
        self.controller.set_single_order(order)
        self.orders_list_widget.clear()
        self.in_progress_orders_list_widget.clear()
        if self.show_orders_panel and order is not None:
            card = OrderCard(order)
            card.remove_button_signal.connect(self.remove_order_clicked)
            card.toggle_status_button_signal.connect(self.toggle_order_status_from_card)
            card.clicked.connect(self.order_selected)
            self._place_order_card(order, card)
        order = self.controller.get_active_order()
        self.set_selected_order_card(order.id if order else "")
        self.update_ticket_management_visibility()
        self.fill_order_form(order)
        self.render_dishes(order)
        dish = self.controller.get_active_dish()
        if dish:
            self.dish_list_widget.set_active(dish.id)
            self.render_products(dish)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()

    def new_order_button_clicked(self): 
        self.register_form_data()
        new_order = self.controller.new_order_button_clicked()
        new_order_card = OrderCard(new_order)
        new_order_card.remove_button_signal.connect(self.remove_order_clicked)
        new_order_card.toggle_status_button_signal.connect(self.toggle_order_status_from_card)
        new_order_card.clicked.connect(self.order_selected)
        self.orders_list_widget.add_item(new_order.id, new_order_card)
        self.selected_products_list.clear()
        self.dish_list_widget.clear()
        self.set_selected_order_card(new_order.id)
        self.update_ticket_management_visibility()
        self.fill_order_form(new_order)
        self.new_dish_button_clicked()
        self.persist_active_order()

    def new_dish_button_clicked(self): 
        if not self.is_active_order_editable():
            return
        # Persist current form values so the new dish inherits current order.to_go.
        self.register_form_data()
        new_dish = self.controller.new_dish_button_clicked()
        if not new_dish:
            return
        order = self.controller.get_active_order()
        self.render_dishes(order)
        self.dish_list_widget.set_active(new_dish.id)
        self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.schedule_autosave()

    def remove_order_clicked(self, order_id): 
        active_before = self.controller.get_active_order()
        was_active = active_before is not None and active_before.id == order_id
        self.unlocked_closed_order_ids.discard(order_id)
        self.controller.remove_order_clicked(order_id)
        self.orders_list_widget.remove_item(order_id)
        self.in_progress_orders_list_widget.remove_item(order_id)
        active_order = self.controller.get_active_order()
        if was_active or active_order is None:
            self.controller.clear_active_selection()
            self.orders_list_widget.set_active(None)
            self.in_progress_orders_list_widget.set_active(None)
            self.dish_list_widget.clear()
            self.selected_products_list.clear()
        else:
            self.set_selected_order_card(active_order.id)
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.update_ticket_management_visibility()
        self.clear_form()
        self.schedule_autosave()
        # Notify CRUD view to refresh table if linked
        if hasattr(self, "order_crud_view") and self.order_crud_view:
            if hasattr(self.order_crud_view, "refresh_all_orders"):
                self.order_crud_view.refresh_all_orders()

        
    def remove_dish_clicked(self, dish_id): 
        if not self.is_active_order_editable():
            return
        self.controller.remove_dish_clicked(dish_id)
        order = self.controller.get_active_order()
        self.render_dishes(order)
        active_dish = self.controller.get_active_dish()
        if active_dish:
            self.dish_list_widget.set_active(active_dish.id)
            self.render_products(active_dish)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.schedule_autosave()

    

    def order_selected(self, order_id: str):
        # Persist current form values on the currently active order before switching.
        self.register_form_data()
        order = self.controller.order_selected(order_id)
        self.set_selected_order_card(order_id)
        self.update_ticket_management_visibility()
        self.fill_order_form(order)

        self.render_dishes(order)

        # If the order already has dishes
        dish = self.controller.get_active_dish()
        if dish:
            self.dish_list_widget.set_active(dish.id)
            self.render_products(dish)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.apply_order_edit_mode()

    def dish_selected(self, dish_id:str): 
        dish = self.controller.dish_selected(dish_id)
        self.dish_list_widget.set_active(dish_id)
        self.render_products(dish)
        self.update_active_dish_total_label()

    
    def render_dishes(self, order):
        self.dish_list_widget.clear()
        if not order:
            return
        for dish in order.dishes.values():
            card = DishCard(dish)
            card.remove_button_signal.connect(self.remove_dish_button_clicked)
            card.send_button_signal.connect(self.send_dish_button_clicked)
            card.to_go_changed_signal.connect(self.dish_to_go_changed)
            if hasattr(card, "set_interaction_enabled"):
                card.set_interaction_enabled(self.is_active_order_editable())
            self.dish_list_widget.add_item(dish.id, card)
            card.clicked.connect(lambda _, d_id=dish.id: self.dish_selected(d_id))

    def render_products(self, dish):
        self.selected_products_list.clear()
        for product in dish.products.values():
            card = OrderElementCard(product)
            card.remove_button_signal.connect(self.remove_product_button_clicked)
            if hasattr(card, "quantity_changed_signal"):
                card.quantity_changed_signal.connect(self.product_quantity_changed)
            if hasattr(card, "price_changed_signal"):
                card.price_changed_signal.connect(self.product_price_changed)
            if hasattr(card, "name_changed_signal"):
                card.name_changed_signal.connect(self.product_name_changed)
            if hasattr(card, "set_interaction_enabled"):
                card.set_interaction_enabled(self.is_active_order_editable())
            self.selected_products_list.add_element(card)

    def render_orders(self):
        # Clear existing orders before rendering new ones
        self.orders_list_widget.clear()
        self.in_progress_orders_list_widget.clear()
        
        orders = self.controller.get_orders()
        for order in orders.values():
            card = OrderCard(order)
            card.remove_button_signal.connect(self.remove_order_clicked)
            card.toggle_status_button_signal.connect(self.toggle_order_status_from_card)
            card.clicked.connect(self.order_selected)
            self._place_order_card(order, card)
        self._sort_items_list_by_created_at(self.orders_list_widget)
        self._sort_items_list_by_created_at(self.in_progress_orders_list_widget)

    

    def fill_order_form(self, order: Order): 
        if not order:
            self.clear_form()
            return
        self.selected_order_folio_label.setText(f"ID: {order.id}")
        self._loading_order_form = True
        self.order_form_name.blockSignals(True)
        self._order_form_table_signals_blocked = True
        self.order_form_amount_paid.blockSignals(True)
        self.order_form_to_go.blockSignals(True)
        self.order_form_service_date.blockSignals(True)
        self.order_form_additional_notes.blockSignals(True)
        self.order_form_include_notes_in_ticket.blockSignals(True)
        try:
            self.order_form_name.setText(order.name or "")
            table_index = self._find_table_button_index(order.table or "")
            if table_index >= 0:
                self._set_table_button_selected_index(table_index, emit=False)
            else:
                self._set_table_button_selected_index(0, emit=False)
            self.order_form_amount_paid.setText(f"{float(order.amount_paid):.2f}")
            self.order_form_to_go.setChecked(bool(order.to_go))
            self._set_service_date_value(str(getattr(order, "service_date", "") or ""))
            self.order_form_additional_notes.setText(str(getattr(order, "additional_notes", "") or ""))
            self.order_form_include_notes_in_ticket.setChecked(
                bool(getattr(order, "include_additional_notes_in_ticket", False))
            )
        finally:
            self.order_form_name.blockSignals(False)
            self._order_form_table_signals_blocked = False
            self.order_form_amount_paid.blockSignals(False)
            self.order_form_to_go.blockSignals(False)
            self.order_form_service_date.blockSignals(False)
            self.order_form_additional_notes.blockSignals(False)
            self.order_form_include_notes_in_ticket.blockSignals(False)
            self._loading_order_form = False
        self.update_change_label()


    def remove_product_button_clicked(self, product_name):
        if not self.is_active_order_editable():
            return
        self.controller.remove_product_clicked(product_name)
        dish = self.controller.get_active_dish()
        if dish:
            self.render_products(dish)
            order = self.controller.get_active_order()
            self.render_dishes(order)
            self.dish_list_widget.set_active(dish.id)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.schedule_autosave()
        
    def remove_dish_button_clicked(self, dish_id):
        if not self.is_active_order_editable():
            return
        self.remove_dish_clicked(dish_id)
        self.update_active_order_total_label()

    def send_dish_button_clicked(self, dish_id):
        if not self.is_active_order_editable():
            return
        dish = self.controller.send_dish_button_clicked(dish_id)
        order = self.controller.get_active_order()
        self.render_dishes(order)
        if dish:
            self.dish_list_widget.set_active(dish.id)
        active_dish = self.controller.get_active_dish()
        if active_dish:
            self.render_products(active_dish)
        else:
            self.selected_products_list.clear()
        if order:
            card = self.orders_list_widget.items.get(order.id) or self.in_progress_orders_list_widget.items.get(order.id)
            if card and hasattr(card, "update_from_order"):
                card.update_from_order(order)
            self._place_order_card(order, card)
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.persist_active_order()

    def dish_to_go_changed(self, dish_id, to_go):
        if not self.is_active_order_editable():
            return
        dish = self.controller.dish_to_go_changed(dish_id, to_go)
        order = self.controller.get_active_order()
        self.render_dishes(order)
        if dish:
            self.dish_list_widget.set_active(dish.id)
        active_dish = self.controller.get_active_dish()
        if active_dish:
            self.render_products(active_dish)
        else:
            self.selected_products_list.clear()
        self.schedule_autosave()

    def product_add_button_clicked(self, product):
        if not self.is_active_order_editable():
            return
        if getattr(product, "is_custom", False):
            unique_name = self.controller.next_custom_product_key()
            custom = SimpleNamespace(
                name=unique_name,
                display_name="Custom product",
                price=0.0,
                notes_shortcuts=[],
                notes="",
                is_custom=True,
            )
            dish = self.controller.product_card_add_button_clicked(custom)
        else:
            dish = self.controller.product_card_add_button_clicked(product)
        if dish:
            self.render_products(dish)
            order = self.controller.get_active_order()
            self.render_dishes(order)
            self.dish_list_widget.set_active(dish.id)
            self.update_active_dish_total_label()
            self.update_active_order_total_label()
            self.schedule_autosave()

    def product_quantity_changed(self, product_name: str, quantity: int):
        if not self.is_active_order_editable():
            return
        dish = self.controller.product_quantity_changed(product_name, quantity)
        if dish:
            order = self.controller.get_active_order()
            self.render_dishes(order)
            self.dish_list_widget.set_active(dish.id)
            self.update_active_dish_total_label()
            self.update_active_order_total_label()
            self.schedule_autosave()

    def product_price_changed(self, product_name: str, price: float):
        if not self.is_active_order_editable():
            return
        dish = self.controller.product_price_changed(product_name, price)
        if dish:
            order = self.controller.get_active_order()
            self.render_dishes(order)
            self.dish_list_widget.set_active(dish.id)
            self.update_active_dish_total_label()
            self.update_active_order_total_label()
            self.schedule_autosave()

    def product_name_changed(self, old_name: str, new_name: str):
        if not self.is_active_order_editable():
            return
        ok = self.controller.product_name_changed(old_name, new_name)
        if not ok:
            QMessageBox.warning(self, "Invalid name", "A product with that name already exists.")
            # Re-render to restore the original name
        dish = self.controller.get_active_dish()
        if dish:
            self.render_products(dish)
            order = self.controller.get_active_order()
            self.render_dishes(order)
            self.dish_list_widget.set_active(dish.id)
            self.update_active_dish_total_label()
            self.update_active_order_total_label()
            self.schedule_autosave()

    def update_active_dish_total_label(self):
        dish = self.controller.get_active_dish()
        if dish:
            self.active_dish_total_label.setText(f"TOTAL: ${dish.total_amount}")
            self.active_dish_total_label.show()
        else:
            self.active_dish_total_label.setText("TOTAL: $0")
            self.active_dish_total_label.hide()
    
    def update_active_order_total_label(self):
        order = self.controller.get_active_order()
        if order:
            self.active_order_total_label.setText(f"TOTAL: ${order.total_amount}")
            self.active_order_total_label.show()
            self.cash_row_widget.show()
            self.change_label.show()
        else:
            self.active_order_total_label.setText("TOTAL: $0")
            self.active_order_total_label.hide()
            self.cash_row_widget.hide()
            self.change_label.hide()
        self.update_change_label()
        self.apply_order_edit_mode()

    def close_order_button_clicked(self):
        if not self.is_active_order_editable():
            return
        self.register_form_data()
        try:
            active_order = self.controller.close_order_button_clicked()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Error closing order",
                f"Could not save the order to the database.\n\nDetails: {exc}",
            )
            return
        if active_order:
            self.unlocked_closed_order_ids.discard(active_order.id)
            card = self.orders_list_widget.items.get(active_order.id) or self.in_progress_orders_list_widget.items.get(active_order.id)
            if card and hasattr(card, "update_from_order"):
                card.update_from_order(active_order)
            self.orders_list_widget.take_item(active_order.id)
            self.in_progress_orders_list_widget.take_item(active_order.id)
        self.controller.clear_active_selection()
        self.orders_list_widget.set_active(None)
        self.in_progress_orders_list_widget.set_active(None)
        self.dish_list_widget.clear()
        self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.update_ticket_management_visibility()
        self.clear_form()

    def reopen_ticket_button_clicked(self):
        order = self.controller.get_active_order()
        if not order or order.status != "Closed":
            return
        reopened = self.controller.reopen_order_button_clicked()
        if not reopened:
            return
        self.unlocked_closed_order_ids.discard(reopened.id)
        if self.show_orders_panel:
            card = self.orders_list_widget.items.get(reopened.id) or self.in_progress_orders_list_widget.items.get(reopened.id)
            if card and hasattr(card, "update_from_order"):
                card.update_from_order(reopened)
            # If the card was removed when the order was closed, recreate it so
            # the reopened order appears again in the orders panel.
            if card is None:
                card = OrderCard(reopened)
                card.remove_button_signal.connect(self.remove_order_clicked)
                card.toggle_status_button_signal.connect(self.toggle_order_status_from_card)
                card.clicked.connect(self.order_selected)
            self._place_order_card(reopened, card)
            self.set_selected_order_card(reopened.id)
            self.fill_order_form(reopened)
            self.render_dishes(reopened)
            active_dish = self.controller.get_active_dish()
            if active_dish:
                self.dish_list_widget.set_active(active_dish.id)
                self.render_products(active_dish)
            else:
                self.selected_products_list.clear()
            self.update_active_dish_total_label()
            self.update_active_order_total_label()
            self.update_ticket_management_visibility()
            self.persist_active_order()
            return

        self.controller.order_selected(reopened.id)
        self.fill_order_form(reopened)
        self.render_dishes(reopened)
        active_dish = self.controller.get_active_dish()
        if active_dish:
            self.dish_list_widget.set_active(active_dish.id)
            self.render_products(active_dish)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.update_ticket_management_visibility()
        self.persist_active_order()

    def toggle_ticket_edit_button_clicked(self):
        order = self.controller.get_active_order()
        if not order or order.status != "Closed":
            return
        if order.id in self.unlocked_closed_order_ids:
            self.unlocked_closed_order_ids.discard(order.id)
        else:
            self.unlocked_closed_order_ids.add(order.id)
        self.apply_order_edit_mode()

    def send_order_button_clicked(self):
        order = self.controller.get_active_order()
        if not order:
            return
        self.register_form_data()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.update_ticket_management_visibility()
        self.persist_active_order()
        self.print_active_ticket()

    def change_status_button_clicked(self):
        self.toggle_order_status_from_card()

    def toggle_order_status_from_card(self, order_id: str | None = None):
        if order_id:
            self.register_form_data()
            selected = self.controller.order_selected(order_id)
            if not selected:
                return
        order = self.controller.get_active_order()
        if not order or order.status == "Closed":
            return
        target_status = "New" if order.status == "In progress" else "In progress"
        updated = self.controller.set_active_order_status(target_status)
        if not updated:
            return
        card = self.orders_list_widget.items.get(updated.id) or self.in_progress_orders_list_widget.items.get(updated.id)
        if card and hasattr(card, "update_from_order"):
            card.update_from_order(updated)
        self._place_order_card(updated, card)
        self.set_selected_order_card(updated.id)
        self.update_ticket_management_visibility()
        self.fill_order_form(updated)
        self.render_dishes(updated)
        active_dish = self.controller.get_active_dish()
        if active_dish:
            self.dish_list_widget.set_active(active_dish.id)
            self.render_products(active_dish)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.persist_active_order()

    def mark_sent_button_clicked(self):
        order = self.controller.get_active_order()
        if not order or order.status == "Closed":
            return
        self.controller.send_order_button_clicked()
        updated = self.controller.get_active_order()
        if not updated:
            return
        card = self.orders_list_widget.items.get(updated.id) or self.in_progress_orders_list_widget.items.get(updated.id)
        if card and hasattr(card, "update_from_order"):
            card.update_from_order(updated)
        self.render_dishes(updated)
        active_dish = self.controller.get_active_dish()
        if active_dish:
            self.dish_list_widget.set_active(active_dish.id)
            self.render_products(active_dish)
        else:
            self.selected_products_list.clear()
        self.update_active_dish_total_label()
        self.update_active_order_total_label()
        self.persist_active_order()

    def print_active_ticket(self):
        order = self.controller.get_active_order()
        if not order:
            QMessageBox.information(self, "No order", "There is no active order to print.")
            return

        ticket_text = TicketBody.build(order, use_print_time=True)
        if self._print_ticket_raw_windows(ticket_text):
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)

        if self.ticket_printer_name:
            printer.setPrinterName(self.ticket_printer_name)
            if not printer.isValid():
                available = ", ".join(QPrinterInfo.availablePrinterNames()) or "No printers detectadas"
                QMessageBox.warning(
                    self,
                    "Printer not available",
                    f"Printer '{self.ticket_printer_name}' was not found.\nAvailable: {available}",
                )
                return
        else:
            default_printer = QPrinterInfo.defaultPrinter()
            if default_printer.isNull():
                QMessageBox.warning(
                    self,
                    "No printer",
                    "No default printer is configured.",
                )
                return
            printer.setPrinterName(default_printer.printerName())
            if not printer.isValid():
                available = ", ".join(QPrinterInfo.availablePrinterNames()) or "No printers detectadas"
                QMessageBox.warning(
                    self,
                    "Printer not available",
                    f"The default printer is not valid.\nAvailable: {available}",
                )
                return

        document = QTextDocument()
        document.setDefaultFont(QFont("Consolas", 10))
        document.setHtml(self._ticket_html_with_logo(ticket_text))
        document.print(printer)

    def _print_ticket_raw_windows(self, ticket_text: str) -> bool:
        class DOC_INFO_1(ctypes.Structure):
            _fields_ = [
                ("pDocName", wintypes.LPWSTR),
                ("pOutputFile", wintypes.LPWSTR),
                ("pDatatype", wintypes.LPWSTR),
            ]

        printer_name = self.ticket_printer_name.strip()
        if not printer_name:
            default_printer = QPrinterInfo.defaultPrinter()
            if default_printer.isNull():
                return False
            printer_name = default_printer.printerName()

        if printer_name not in QPrinterInfo.availablePrinterNames():
            return False

        winspool = ctypes.WinDLL("winspool.drv", use_last_error=True)
        open_printer = winspool.OpenPrinterW
        open_printer.argtypes = [wintypes.LPWSTR, ctypes.POINTER(wintypes.HANDLE), wintypes.LPVOID]
        open_printer.restype = wintypes.BOOL
        close_printer = winspool.ClosePrinter
        close_printer.argtypes = [wintypes.HANDLE]
        close_printer.restype = wintypes.BOOL
        start_doc = winspool.StartDocPrinterW
        start_doc.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p]
        start_doc.restype = wintypes.DWORD
        end_doc = winspool.EndDocPrinter
        end_doc.argtypes = [wintypes.HANDLE]
        end_doc.restype = wintypes.BOOL
        start_page = winspool.StartPagePrinter
        start_page.argtypes = [wintypes.HANDLE]
        start_page.restype = wintypes.BOOL
        end_page = winspool.EndPagePrinter
        end_page.argtypes = [wintypes.HANDLE]
        end_page.restype = wintypes.BOOL
        write_printer = winspool.WritePrinter
        write_printer.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        write_printer.restype = wintypes.BOOL

        printer_handle = wintypes.HANDLE()
        payload = ticket_text.replace("\n", "\r\n").encode("cp1252", errors="replace")

        try:
            if not open_printer(printer_name, ctypes.byref(printer_handle), None):
                return False

            doc_info = DOC_INFO_1("Ticket", None, "RAW")
            if start_doc(printer_handle, 1, ctypes.byref(doc_info)) == 0:
                return False
            try:
                if not start_page(printer_handle):
                    return False
                try:
                    written = wintypes.DWORD(0)
                    if not write_printer(
                        printer_handle,
                        ctypes.c_char_p(payload),
                        len(payload),
                        ctypes.byref(written),
                    ):
                        return False
                    return written.value > 0
                finally:
                    end_page(printer_handle)
            finally:
                end_doc(printer_handle)
        except Exception:
            return False
        finally:
            if printer_handle:
                close_printer(printer_handle)
    
    
    def clear_form(self):
        self.selected_order_folio_label.setText("ID: -")
        self.order_form_name.clear()
        self._set_table_button_selected_index(0, emit=False)
        self.order_form_amount_paid.clear()
        self.order_form_to_go.setChecked(False)
        self._set_service_date_value(date.today().isoformat())
        self.order_form_additional_notes.clear()
        self.order_form_include_notes_in_ticket.setChecked(False)
        self.update_change_label()

    def amount_paid_text_changed(self, _):
        if self._loading_order_form:
            return
        if not self.is_active_order_editable():
            return
        self.register_form_data()
        self.update_change_label()

    def update_change_label(self):
        order = self.controller.get_active_order()
        if not order:
            self.change_label.setText("Change: $0.00")
            return
        amount_paid_text = self.order_form_amount_paid.text().strip()
        try:
            amount_paid = float(amount_paid_text) if amount_paid_text else 0.0
        except ValueError:
            amount_paid = 0.0
        change = max(amount_paid - float(order.total_amount), 0.0)
        self.change_label.setText(f"Change: ${change:.2f}")

    def order_to_go_toggled(self, checked):
        if self._loading_order_form:
            return
        if not self.is_active_order_editable():
            return
        # Use the same pattern as other form changes
        self.order_name_or_table_changed(None)
        # Update all dishes with the new to_go state
        order = self.controller.get_active_order()
        if order:
            self.controller.apply_order_to_go_to_all_dishes(checked)
            self.render_dishes(order)
            active_dish = self.controller.get_active_dish()
            if active_dish:
                self.dish_list_widget.set_active(active_dish.id)
                self.render_products(active_dish)
            else:
                self.selected_products_list.clear()

    def show_ticket_preview(self):
        order = self.controller.get_active_order()
        if not order:
            QMessageBox.information(self, "No order", "Select an order to preview the ticket.")
            return
        self.register_form_data()
        order = self.controller.get_active_order()

        ticket_text = TicketBody.build(order, use_print_time=True)
        dialog = QDialog(self)
        dialog.setWindowTitle("Preview ticket")
        dialog.resize(420, 620)

        layout = QVBoxLayout(dialog)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        ticket_row = QHBoxLayout()
        ticket_row.addStretch(1)
        text_area = QPlainTextEdit()
        text_area.setReadOnly(True)
        text_area.setPlainText(ticket_text)
        preview_font = QFont("Consolas", 11)
        text_area.setFont(preview_font)
        text_area.setStyleSheet("font-family: Consolas, 'Courier New', monospace; font-size: 11pt;")
        text_area.setFixedWidth(self._ticket_preview_width(preview_font))
        ticket_row.addWidget(text_area)
        ticket_row.addStretch(1)
        layout.addLayout(ticket_row)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.exec()

    def _ticket_html_with_logo(self, ticket_text: str) -> str:
        logo_html = ""
        if os.path.exists(self.ticket_logo_path):
            logo_src = self.ticket_logo_path.replace("\\", "/")
            logo_html = (
                "<div style='text-align:center; margin-bottom:8px;'>"
                f"<img src='{logo_src}' style='max-width:220px;' />"
                "</div>"
            )
        rendered_lines = []
        for raw_line in ticket_text.splitlines():
            escaped_line = html.escape(raw_line)
            normalized = raw_line.strip().upper()
            is_brand = normalized == "TAQUERIA EL PADRINO"
            is_total = normalized.startswith("TOTAL:")
            weight = "700" if (is_brand or is_total) else "400"
            rendered_lines.append(
                f"<div style='white-space:pre; font-weight:{weight};'>{escaped_line}</div>"
            )
        rendered_ticket = "".join(rendered_lines)
        return (
            "<html><body style='font-family:Consolas, \"Courier New\", monospace; font-size:10pt;'>"
            f"{logo_html}<div>{rendered_ticket}</div>"
            "</body></html>"
        )

    def _ticket_preview_width(self, font: QFont) -> int:
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance("M" * TicketBody.WIDTH)
        # Frame + scrollbar gutter + inner padding
        return text_width + 36

    def order_name_or_table_changed(self, _):
        if self._loading_order_form:
            return
        if not self.is_active_order_editable():
            return
        if self._order_form_table_signals_blocked:
            return
        self.register_form_data()

    def update_ticket_management_visibility(self):
        has_active_order = self.controller.get_active_order() is not None
        self.ticket_stack.setCurrentIndex(1 if has_active_order else 0)
        self.apply_order_edit_mode()

    def register_form_data(self):
        if self._loading_order_form:
            return
        if not self.is_active_order_editable():
            # Even if not editable, we may still need to capture status change in modal mode
            if self.show_orders_panel:
                return
        name = self.order_form_name.text().strip()
        table = self._current_table_button_text().strip()
        to_go = self.order_form_to_go.isChecked()
        amount_paid_text = self.order_form_amount_paid.text().strip()
        service_date = self.order_form_service_date.date().toString("yyyy-MM-dd")
        additional_notes = self.order_form_additional_notes.text().strip()
        include_notes_in_ticket = self.order_form_include_notes_in_ticket.isChecked()
        try:
            amount_paid = float(amount_paid_text) if amount_paid_text else 0.0
        except ValueError:
            amount_paid = 0.0
        self.controller.register_form_data(
            name,
            table,
            to_go,
            amount_paid,
            additional_notes,
            include_notes_in_ticket,
            service_date,
        )
        # Capture status from dropdown in modal mode
        if not self.show_orders_panel and hasattr(self, "order_status_dropdown"):
            order = self.controller.get_active_order()
            if order:
                new_status = self.order_status_dropdown.currentText()
                if new_status and new_status != order.status:
                    order.set_status(new_status)
        self.refresh_active_order_card()
        self.schedule_autosave()

    def schedule_autosave(self):
        if self.controller.get_active_order():
            self.autosave_timer.start()

    def persist_active_order(self):
        try:
            self.controller.persist_active_order()
            # Notify CRUD view to refresh table if linked
            if hasattr(self, "order_crud_view") and self.order_crud_view:
                if hasattr(self.order_crud_view, "refresh_all_orders"):
                    self.order_crud_view.refresh_all_orders()
        except Exception:
            pass

    def refresh_active_order_card(self):
        order = self.controller.get_active_order()
        if not order:
            return
        card = self.orders_list_widget.items.get(order.id) or self.in_progress_orders_list_widget.items.get(order.id)
        if card and hasattr(card, "update_from_order"):
            card.update_from_order(order)
        self._place_order_card(order, card)

    def set_selected_order_card(self, order_id: str):
        if order_id in self.orders_list_widget.items:
            self.orders_list_widget.set_active(order_id)
            self.in_progress_orders_list_widget.set_active(None)
            return
        if order_id in self.in_progress_orders_list_widget.items:
            self.in_progress_orders_list_widget.set_active(order_id)
            self.orders_list_widget.set_active(None)
            return
        self.orders_list_widget.set_active(None)
        self.in_progress_orders_list_widget.set_active(None)

    def _place_order_card(self, order, card):
        if not order:
            return
        if card is None:
            card = self.orders_list_widget.items.get(order.id) or self.in_progress_orders_list_widget.items.get(order.id)
        if card is None:
            return

        target_list = self._target_list_for_order(order)
        in_active = order.id in self.orders_list_widget.items
        in_progress = order.id in self.in_progress_orders_list_widget.items

        if order.status == "Closed":
            self.orders_list_widget.take_item(order.id)
            self.in_progress_orders_list_widget.take_item(order.id)
            return

        # Keep stable order: avoid removing/re-adding when card is already
        # in the correct list.
        already_in_target = (
            (target_list is self.orders_list_widget and in_active and not in_progress) or
            (target_list is self.in_progress_orders_list_widget and in_progress and not in_active)
        )
        if already_in_target:
            # Re-sort even if the card stays in the same list, because
            # to_go changes can alter group position.
            self._sort_items_list_by_created_at(target_list)
            return

        self.orders_list_widget.take_item(order.id)
        self.in_progress_orders_list_widget.take_item(order.id)
        target_list.add_item(order.id, card)
        self._sort_items_list_by_created_at(target_list)

    def _target_list_for_order(self, order):
        if order.status == "In progress":
            return self.in_progress_orders_list_widget
        return self.orders_list_widget

    def _sort_items_list_by_created_at(self, items_list):
        if not getattr(items_list, "items", None):
            return
        ordered = sorted(
            items_list.items.items(),
            key=lambda pair: (
                1 if bool(getattr(getattr(pair[1], "order", None), "to_go", False)) else 0,
                getattr(getattr(pair[1], "order", None), "created_at", None),
            ),
        )
        # Rebuild layout and dict in sorted order.
        items_list.items = dict(ordered)
        while items_list.layout.count():
            layout_item = items_list.layout.takeAt(0)
            widget = layout_item.widget()
            if widget is not None:
                widget.setParent(None)
        inserted_separator = False
        has_non_to_go = any(not bool(getattr(getattr(w, "order", None), "to_go", False)) for _, w in ordered)
        has_to_go = any(bool(getattr(getattr(w, "order", None), "to_go", False)) for _, w in ordered)
        for _, widget in ordered:
            is_to_go = bool(getattr(getattr(widget, "order", None), "to_go", False))
            if has_to_go and is_to_go and not inserted_separator:
                items_list.layout.addWidget(self._build_to_go_separator())
                inserted_separator = True
            items_list.layout.addWidget(widget)
        if not inserted_separator:
            items_list.layout.addWidget(self._build_to_go_separator())

    def _build_to_go_separator(self):
        separator_container = QWidget()
        separator_layout = QHBoxLayout(separator_container)
        separator_layout.setContentsMargins(6, 8, 6, 8)
        separator_layout.setSpacing(8)

        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Sunken)

        label = QLabel("To go")
        label.setStyleSheet("color: #6b7280; font-size: 9pt;")

        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Sunken)

        separator_layout.addWidget(left_line, 1)
        separator_layout.addWidget(label)
        separator_layout.addWidget(right_line, 1)
        return separator_container

    def _build_section_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #e5e7eb;")
        return line

    def is_active_order_editable(self):
        order = self.controller.get_active_order()
        return self.controller.is_order_editable(order, self.unlocked_closed_order_ids)

    def apply_order_edit_mode(self):
        editable = self.is_active_order_editable()
        order = self.controller.get_active_order()
        is_closed = bool(order and order.status == "Closed")
        is_closed_unlocked = bool(order and order.id in self.unlocked_closed_order_ids)
        if hasattr(self, "order_form_name"):
            self.order_form_name.setEnabled(editable)
        if hasattr(self, "order_form_table_buttons"):
            for button in self.order_form_table_buttons:
                button.setEnabled(editable)
        if hasattr(self, "order_form_amount_paid"):
            self.order_form_amount_paid.setEnabled(editable)
        if hasattr(self, "order_form_to_go"):
            self.order_form_to_go.setEnabled(editable)
        if hasattr(self, "order_form_service_date"):
            self.order_form_service_date.setEnabled(editable)
        if hasattr(self, "order_form_additional_notes"):
            self.order_form_additional_notes.setEnabled(editable)
        if hasattr(self, "order_form_include_notes_in_ticket"):
            self.order_form_include_notes_in_ticket.setEnabled(editable)
        if hasattr(self, "new_dish_button"):
            self.new_dish_button.setEnabled(editable)
        if hasattr(self, "send_order_button"):
            self.send_order_button.setEnabled(bool(order))
        if hasattr(self, "mark_sent_button"):
            self.mark_sent_button.setEnabled(bool(order and not is_closed))
        if hasattr(self, "change_status_button"):
            self.change_status_button.setEnabled(bool(order and not is_closed))
            self.change_status_button.setText(
                "Move to active" if (order and order.status == "In progress") else "Mark in progress"
            )
        if hasattr(self, "close_order_button"):
            self.close_order_button.setEnabled(bool(order and not is_closed))
        if hasattr(self, "reopen_ticket_button"):
            self.reopen_ticket_button.setEnabled(is_closed)
        if hasattr(self, "toggle_ticket_edit_button"):
            self.toggle_ticket_edit_button.setEnabled(is_closed)
            self.toggle_ticket_edit_button.setText(
                "Disable ticket edit" if is_closed_unlocked else "Enable ticket edit"
            )
        # Synchronize status dropdown in modal mode
        if not self.show_orders_panel and hasattr(self, "order_status_dropdown"):
            self._loading_order_form = True
            if order:
                self.order_status_dropdown.setCurrentText(order.status)
                self.order_status_dropdown.setEnabled(editable)
            else:
                self.order_status_dropdown.setEnabled(False)
            self._loading_order_form = False
        if hasattr(self, "products_grid"):
            self.set_products_grid_enabled(editable)
        if hasattr(self, "dish_list_widget"):
            for card in self.dish_list_widget.items.values():
                if hasattr(card, "set_interaction_enabled"):
                    card.set_interaction_enabled(editable)
        if hasattr(self, "selected_products_list"):
            for card in self.selected_products_list.items.values():
                if hasattr(card, "set_interaction_enabled"):
                    card.set_interaction_enabled(editable)

    def set_products_grid_enabled(self, enabled: bool):
        for i in range(self.products_grid.grid.count()):
            item = self.products_grid.grid.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setEnabled(enabled)

    def load_products_from_menu_database(self):
        self._clear_products_grid()
        for data in self.controller.get_menu_products_for_view("orders.db"):
            product = ProductCard(data)
            product.add_button_signal.connect(self.product_add_button_clicked)
            self.products_grid.add_card(product)

    def _clear_products_grid(self):
        grid = self.products_grid.grid
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def load_tables_from_database(self):
        current_value = ""
        if hasattr(self, "order_form_table_items"):
            current_value = self._current_table_button_text().strip()

        self._order_form_table_signals_blocked = True
        self._clear_table_buttons()
        self._add_table_button("")

        for table_name in self.controller.get_active_table_names_for_view("orders.db"):
            self._add_table_button(table_name)

        if current_value:
            table_index = self._find_table_button_index(current_value)
            if table_index < 0:
                self._add_table_button(current_value)
                table_index = self._find_table_button_index(current_value)
            self._set_table_button_selected_index(max(table_index, 0), emit=False)
        else:
            self._set_table_button_selected_index(0, emit=False)

        self._order_form_table_signals_blocked = False

    def refresh_orders_from_database(self):
        """Reload all open orders from the database and update the view"""
        try:
            # Get the currently active order ID before refresh
            active_order_id = self.controller.active_order_id
            
            # Load all open orders from database
            open_orders = self.controller.order_repository.load_open_orders()
            self.controller.set_orders(open_orders)
            
            # Re-render all orders
            self.render_orders()
            
            # If there was an active order, reload it from the fresh data
            if active_order_id and active_order_id in open_orders:
                refreshed_order = open_orders[active_order_id]
                self.order_selected(active_order_id)
            else:
                # Clear the form if the active order no longer exists (was deleted)
                self.clear_form()
                self.update_ticket_management_visibility()
        except Exception as e:
            # Silently fail if unable to refresh
            pass

    def _clear_table_buttons(self):
        while self.order_form_table_layout.count():
            item = self.order_form_table_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.order_form_table_items = []
        self.order_form_table_buttons = []
        self._order_form_table_selected_index = -1

    def _add_table_button(self, value):
        value = str(value)
        label = value if value else "No table"
        button = QPushButton(label)
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(24)
        button.setStyleSheet(
            "QPushButton {"
            "  padding: 1px 8px;"
            "  border: 1px solid #d1d5db;"
            "  border-radius: 10px;"
            "  background: #f3f4f6;"
            "  color: #1f2937;"
            "  font-size: 9pt;"
            "}"
            "QPushButton:hover {"
            "  background: #e5e7eb;"
            "  border-color: #9ca3af;"
            "}"
            "QPushButton:checked {"
            "  background: #374151;"
            "  color: #f9fafb;"
            "  border-color: #374151;"
            "}"
            "QPushButton:disabled {"
            "  background: #f9fafb;"
            "  color: #9ca3af;"
            "  border-color: #e5e7eb;"
            "}"
        )
        idx = len(self.order_form_table_items)
        button.clicked.connect(lambda _: self._set_table_button_selected_index(idx, emit=True))
        self.order_form_table_items.append(value)
        self.order_form_table_buttons.append(button)
        self.order_form_table_layout.addWidget(button)

    def _find_table_button_index(self, text):
        target = str(text)
        for idx, value in enumerate(self.order_form_table_items):
            if value == target:
                return idx
        return -1

    def _set_table_button_selected_index(self, index, emit):
        try:
            index = int(index)
        except (TypeError, ValueError):
            index = -1
        if index < 0 or index >= len(self.order_form_table_items):
            index = -1
        self._order_form_table_selected_index = index
        for idx, button in enumerate(self.order_form_table_buttons):
            button.blockSignals(True)
            button.setChecked(idx == self._order_form_table_selected_index)
            button.blockSignals(False)
        if emit and not self._order_form_table_signals_blocked:
            self.order_name_or_table_changed(self._current_table_button_text())

    def _current_table_button_text(self):
        if 0 <= self._order_form_table_selected_index < len(self.order_form_table_items):
            return self.order_form_table_items[self._order_form_table_selected_index]
        return ""

    def _set_service_date_value(self, value):
        text = str(value or "").strip() or date.today().isoformat()
        parsed = QDate.fromString(text, "yyyy-MM-dd")
        self.order_form_service_date.setDate(parsed if parsed.isValid() else QDate.currentDate())










