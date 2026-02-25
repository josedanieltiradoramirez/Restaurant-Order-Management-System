from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QGraphicsOpacityEffect

class ProductCard(QWidget):
    add_button_signal = pyqtSignal(object)

    def __init__(self, data):
        super().__init__()
        self.name = data["name"]
        self.price = data["price"]
        self.color = data.get("color", "")
        self.shape = self._normalize_shape(data.get("shape", "Rectangle"))
        self.notes_shortcuts = data.get("notes_shortcuts", [])
        self.is_custom = data.get("is_custom", False)
        self.setMinimumWidth(160)
        self.setMinimumHeight(64)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._click_anim = None
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self.init_ui()

    def init_ui(self):
        palette = self._build_palette()
        width, height, radius = self._shape_style_values()
        self.setFixedSize(width, height)
        
        #-------------- NAME --------------
        name_label = QLabel(self.name)
        name_label.setStyleSheet(f"color: {palette['text']};")
        name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #-------------- PRICE --------------
        price_label = QLabel(f"{self.price}")
        price_label.setFont(QFont("Segoe UI", 9))
        price_label.setStyleSheet(f"color: {palette['subtext']};")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #-------------- Layout --------------
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(name_label)
        main_layout.addWidget(price_label)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(4)

        self.setLayout(main_layout)
        self.setObjectName("card")
        self.setStyleSheet("""
            QWidget#card {
                background-color: %s;
                border: 1px solid %s;
                border-radius: %spx;
            }
            QWidget#card:hover {
                background-color: %s;
                border: 1px solid %s;
            }

        """ % (
            palette["background"],
            palette["border"],
            radius,
            palette["hover"],
            palette["hover_border"],
        ))

    def _normalize_shape(self, shape):
        text = (shape or "").strip().lower()
        aliases = {
            "square": "Square",
            "circle": "Circle",
            "círculo": "Circle",
            "ellipse": "Ellipse",
            "rectangle": "Rectangle",
            "rectángulo": "Rectangle",
            "rounded rectangle": "Rounded rectangle",
            "rectángulo redondeado": "Rounded rectangle",
        }
        return aliases.get(text, "Rectangle")

    def _shape_style_values(self):
        if self.shape == "Square":
            return 112, 112, 0
        if self.shape == "Circle":
            return 112, 112, 56
        if self.shape == "Ellipse":
            return 168, 96, 48
        if self.shape == "Rounded rectangle":
            return 196, 88, 14
        return 196, 88, 0

    def _build_palette(self):
        default_palette = {
            "background": "#f9fafb",
            "hover": "#f1f5f9",
            "border": "#e5e7eb",
            "hover_border": "#cbd5e1",
            "text": "#1f1f1f",
            "subtext": "#4b5563",
        }
        color_text = (self.color or "").strip()
        if not color_text:
            return default_palette

        color = QColor(color_text)
        if not color.isValid():
            return default_palette

        lightness = color.lightness()
        background = color.name()
        hover = color.darker(108).name() if lightness > 180 else color.lighter(112).name()
        border = color.darker(122).name() if lightness > 150 else color.lighter(128).name()
        hover_border = color.darker(132).name() if lightness > 150 else color.lighter(142).name()
        text = "#111827" if lightness > 145 else "#f9fafb"
        subtext = "#1f2937" if lightness > 155 else "#e5e7eb"
        return {
            "background": background,
            "hover": hover,
            "border": border,
            "hover_border": hover_border,
            "text": text,
            "subtext": subtext,
        }

    def add_button_clicked(self):
        self.add_button_signal.emit(self)
    
    def animate_click(self):
        if self._click_anim and self._click_anim.state() == QPropertyAnimation.State.Running:
            self._click_anim.stop()

        fade_out = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        fade_out.setDuration(70)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.7)
        fade_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        fade_in = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        fade_in.setDuration(90)
        fade_in.setStartValue(0.7)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._click_anim = QSequentialAnimationGroup(self)
        self._click_anim.addAnimation(fade_out)
        self._click_anim.addAnimation(fade_in)
        self._click_anim.start()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.animate_click()
            self.add_button_clicked()
        super().mousePressEvent(event)

 
        

