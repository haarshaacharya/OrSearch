import sys
import os
import html
import re
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QThread, Signal, QSize
from PySide6.QtGui import (
    QPainter,
    QColor,
    QPen,
    QFont,
    QBrush,
    QLinearGradient,
    QTextCursor,
    QKeySequence,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QFrame,
    QMessageBox,
    QInputDialog,
    QSizePolicy,
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agent import run_agent


# =========================================================
# ULTRA-PREMIUM COLOR PALETTE & DESIGN TOKENS
# =========================================================

BG_MAIN = "#090B0E"
BG_SIDEBAR = "#0C0F15"
BG_CONTENT = "#090B0E"
BG_PANEL = "#11151F"
BG_CARD = "#141924"
BG_CARD_HOVER = "#1B2232"
BG_CARD_ACTIVE = "#15222E"

BORDER_SUBTLE = "#1C2333"
BORDER_CARD = "#232C3F"
BORDER_HOVER = "#323F5A"
BORDER_EMERALD = "#10B981"

TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#E2E8F0"
TEXT_MUTED = "#94A3B8"
TEXT_SUBTLE = "#64748B"

EMERALD = "#10B981"
EMERALD_MINT = "#34D399"
EMERALD_DARK = "#059669"
EMERALD_BG = "#06261A"
EMERALD_BORDER = "#0F5132"

AMBER = "#F59E0B"
AMBER_BG = "#291B05"
AMBER_BORDER = "#613E09"

RED = "#EF4444"
RED_BG = "#2B0B0B"
RED_BORDER = "#5C1D1D"

CYAN = "#06B6D4"


# =========================================================
# MARKDOWN & RICH FORMATTING ENGINE
# =========================================================

def render_markdown(text: str) -> str:
    """
    Zero-dependency Markdown to HTML parser tailored for PySide6 QTextEdit.
    Supports code blocks, inline code, bold, italic, headers, bullet lists,
    numbered lists, blockquotes, and paragraph line breaks.
    """
    if not text:
        return ""

    # 1. Extract and preserve fenced code blocks ```lang ... ```
    code_blocks = []

    def replace_code_block(match):
        lang = (match.group(1) or "").strip().upper()
        code = match.group(2)
        escaped_code = html.escape(code.strip("\r\n"))
        lang_label = lang if lang else "CODE"

        block_html = f"""
        <div style="margin: 10px 0; background: #080A0F; border: 1px solid #1E2738; border-radius: 8px; overflow: hidden; font-family: 'Consolas', 'Courier New', monospace;">
            <div style="background: #111622; padding: 5px 12px; font-size: 11px; color: #8B98A5; border-bottom: 1px solid #1E2738; font-weight: 700; letter-spacing: 0.5px;">
                ⚡ {lang_label}
            </div>
            <div style="padding: 12px 14px; font-size: 13px; color: #E2E8F0; white-space: pre-wrap; line-height: 1.5;">{escaped_code}</div>
        </div>
        """
        idx = len(code_blocks)
        code_blocks.append(block_html)
        return f"__CODE_BLOCK_{idx}__"

    # Match triple backtick code blocks
    pattern_code = r"```([a-zA-Z0-9_\-\+]*)\n?(.*?)```"
    text = re.sub(pattern_code, replace_code_block, text, flags=re.DOTALL)

    # 2. Escape standard HTML in the remaining text
    text = html.escape(text)

    # 3. Inline code `text`
    text = re.sub(
        r"`([^`\n]+)`",
        r'<code style="background: #19202E; color: #34D399; padding: 2px 6px; border-radius: 4px; font-family: Consolas, monospace; font-size: 12px; border: 1px solid #28354A;">\1</code>',
        text,
    )

    # 4. Bold **text**
    text = re.sub(
        r"\*\*([^\*\n]+)\*\*",
        r'<strong style="color: #FFFFFF; font-weight: 700;">\1</strong>',
        text,
    )

    # 5. Italic *text*
    text = re.sub(
        r"(?<!\*)\*([^\*\n]+)\*(?!\*)",
        r'<em style="color: #CBD5E1;">\1</em>',
        text,
    )

    # 6. Line by line processing for headers, lists, and quotes
    lines = text.split("\n")
    formatted_lines = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("### "):
            header_text = stripped[4:]
            formatted_lines.append(
                f'<div style="font-size: 15px; font-weight: 700; color: {EMERALD_MINT}; margin: 10px 0 4px 0;">{header_text}</div>'
            )
        elif stripped.startswith("## "):
            header_text = stripped[3:]
            formatted_lines.append(
                f'<div style="font-size: 17px; font-weight: 700; color: #FFFFFF; margin: 12px 0 6px 0;">{header_text}</div>'
            )
        elif stripped.startswith("# "):
            header_text = stripped[2:]
            formatted_lines.append(
                f'<div style="font-size: 20px; font-weight: 800; color: #FFFFFF; margin: 14px 0 8px 0; border-bottom: 1px solid #232C3F; padding-bottom: 4px;">{header_text}</div>'
            )
        elif stripped.startswith("- ") or stripped.startswith("* "):
            item_text = stripped[2:]
            formatted_lines.append(
                f'<div style="margin: 3px 0 3px 14px; color: #E2E8F0;"><span style="color: {EMERALD}; font-weight: bold; margin-right: 6px;">•</span>{item_text}</div>'
            )
        elif re.match(r"^\d+\.\s+", stripped):
            match = re.match(r"^(\d+)\.\s+(.*)", stripped)
            num = match.group(1)
            content = match.group(2)
            formatted_lines.append(
                f'<div style="margin: 3px 0 3px 14px; color: #E2E8F0;"><span style="color: {EMERALD_MINT}; font-weight: bold; margin-right: 6px;">{num}.</span>{content}</div>'
            )
        elif stripped.startswith("&gt; ") or stripped.startswith("> "):
            quote_text = stripped[5:] if stripped.startswith("&gt; ") else stripped[2:]
            formatted_lines.append(
                f'<div style="border-left: 3px solid {EMERALD}; padding: 6px 12px; margin: 8px 0; color: #94A3B8; background: #101520; border-radius: 0 6px 6px 0; font-style: italic;">{quote_text}</div>'
            )
        else:
            if stripped:
                formatted_lines.append(f'<div style="margin: 2px 0; line-height: 1.6;">{line}</div>')
            else:
                formatted_lines.append('<div style="height: 6px;"></div>')

    final_html = "".join(formatted_lines)

    # 7. Restore code blocks
    for idx, block in enumerate(code_blocks):
        final_html = final_html.replace(f"__CODE_BLOCK_{idx}__", block)

    return final_html


def render_actions_summary(actions: list) -> str:
    """
    Renders an elegant timeline card summarizing computer actions executed by the agent.
    """
    if not actions:
        return ""

    rows = []
    for item in actions:
        act = item.get("action", {}) if isinstance(item, dict) else {}
        res = item.get("result", {}) if isinstance(item, dict) else {}
        act_type = act.get("type", "action")
        success = res.get("success", True) if isinstance(res, dict) else True

        icon = "✓" if success else "✗"
        icon_color = EMERALD if success else RED

        details = []
        for k, v in act.items():
            if k != "type":
                details.append(
                    f"<span style='color: #64748B;'>{html.escape(k)}:</span> <span style='color: #E2E8F0;'>{html.escape(str(v))}</span>"
                )
        params_str = f" ({', '.join(details)})" if details else ""

        rows.append(
            f"""
            <div style="margin: 3px 0; font-size: 12px; display: flex; align-items: center;">
                <span style="color: {icon_color}; font-weight: 800; margin-right: 8px;">{icon}</span>
                <span style="color: #38BDF8; font-family: 'Consolas', monospace; font-weight: 600;">{html.escape(act_type)}</span>
                <span style="font-size: 11px; margin-left: 4px;">{params_str}</span>
            </div>
            """
        )

    rows_html = "".join(rows)
    count = len(actions)

    return f"""
    <div style="margin: 10px 0 12px 0; background: #0A0D14; border: 1px solid #1E283A; border-radius: 9px; padding: 10px 14px;">
        <div style="font-size: 11px; font-weight: 800; color: {EMERALD_MINT}; letter-spacing: 0.8px; margin-bottom: 7px;">
            ⚡ EXECUTED ACTIONS ({count})
        </div>
        {rows_html}
    </div>
    """


# =========================================================
# AGENT WORKER THREAD
# =========================================================

class AgentWorker(QThread):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, message):
        super().__init__()
        self.message = message

    def run(self):
        try:
            result = run_agent(self.message)
            self.finished.emit(result)
        except Exception as e:
            self.failed.emit(str(e))


# =========================================================
# ORSEARCH CORE LOGO (REFINED EMERALD ORB)
# =========================================================

class OrsearchCore(QWidget):
    def __init__(self, size=110, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.pulse = 0
        self.pulse_dir = 1
        self.setFixedSize(size, size)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(25)

    def animate(self):
        self.angle = (self.angle + 2) % 360
        self.pulse += 0.04 * self.pulse_dir
        if self.pulse > 1.0:
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse < 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        s = self.size
        center = s / 2

        # Multi-layer ambient radial glow
        for width, base_alpha in [(18, 8), (12, 16), (7, 28)]:
            alpha = int(base_alpha + 8 * self.pulse)
            pen = QPen(QColor(16, 185, 129, alpha))
            pen.setWidth(width)
            painter.setPen(pen)
            painter.drawEllipse(width // 2, width // 2, s - width, s - width)

        # Outer ring
        pen = QPen(QColor(16, 185, 129, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(8, 8, s - 16, s - 16)

        # Rotating energy arc
        gradient_pen = QPen(QColor(52, 211, 153, 240))
        gradient_pen.setWidth(3)
        painter.setPen(gradient_pen)
        painter.drawArc(11, 11, s - 22, s - 22, self.angle * 16, 95 * 16)

        # Counter-rotating subtle arc
        sub_pen = QPen(QColor(6, 182, 212, 160))
        sub_pen.setWidth(2)
        painter.setPen(sub_pen)
        painter.drawArc(15, 15, s - 30, s - 30, -self.angle * 12, 60 * 16)

        # Center typography
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", max(11, int(s * 0.38)))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "S")


# =========================================================
# CHAT ITEM (SIDEBAR LIST ROW)
# =========================================================

class ChatItem(QWidget):
    def __init__(
        self,
        chat_id,
        title,
        pinned,
        is_active,
        select_callback,
        rename_callback,
        pin_callback,
        delete_callback,
    ):
        super().__init__()
        self.chat_id = chat_id
        self.is_active = is_active

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(6, 4, 6, 4)
        self.layout.setSpacing(4)

        # Active indicator bar (left accent)
        self.indicator = QFrame()
        self.indicator.setFixedWidth(3)
        self.indicator.setFixedHeight(22)
        if is_active:
            self.indicator.setStyleSheet(
                f"background: {EMERALD}; border-radius: 2px;"
            )
        else:
            self.indicator.setStyleSheet("background: transparent;")
        self.layout.addWidget(self.indicator)

        # Chat title button
        icon_prefix = "📌 " if pinned else "💬 "
        self.chat_button = QPushButton(f"{icon_prefix}{title}")
        self.chat_button.setCursor(Qt.PointingHandCursor)
        self.chat_button.setMinimumHeight(36)
        self.chat_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )

        active_bg = BG_CARD_ACTIVE if is_active else "transparent"
        active_color = EMERALD_MINT if is_active else TEXT_SECONDARY
        active_border = f"border: 1px solid {BORDER_EMERALD};" if is_active else "border: 1px solid transparent;"
        font_weight = "600" if is_active else "400"

        self.chat_button.setStyleSheet(f"""
            QPushButton {{
                background: {active_bg};
                color: {active_color};
                {active_border}
                border-radius: 8px;
                text-align: left;
                padding: 0 10px;
                font-size: 13px;
                font-weight: {font_weight};
            }}
            QPushButton:hover {{
                background: {BG_CARD_HOVER};
                color: {TEXT_PRIMARY};
            }}
        """)

        self.chat_button.clicked.connect(lambda: select_callback(self.chat_id))
        self.layout.addWidget(self.chat_button, 1)

        # Rename button
        self.rename_button = QPushButton("✎")
        self.rename_button.setToolTip("Rename conversation")
        self.rename_button.setFixedSize(26, 28)
        self.rename_button.setCursor(Qt.PointingHandCursor)

        # Pin button
        self.pin_button = QPushButton("📌" if pinned else "○")
        self.pin_button.setToolTip("Unpin" if pinned else "Pin to top")
        self.pin_button.setFixedSize(26, 28)
        self.pin_button.setCursor(Qt.PointingHandCursor)

        # Delete button
        self.delete_button = QPushButton("✕")
        self.delete_button.setToolTip("Delete conversation")
        self.delete_button.setFixedSize(26, 28)
        self.delete_button.setCursor(Qt.PointingHandCursor)

        btn_style = f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SUBTLE};
                border: none;
                border-radius: 6px;
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: {BG_CARD_HOVER};
                color: {TEXT_PRIMARY};
            }}
        """
        self.rename_button.setStyleSheet(btn_style)
        self.delete_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SUBTLE};
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {RED_BG};
                color: {RED};
            }}
        """)

        pin_color = EMERALD_MINT if pinned else TEXT_SUBTLE
        self.pin_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {pin_color};
                border: none;
                border-radius: 6px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {BG_CARD_HOVER};
                color: {EMERALD_MINT};
            }}
        """)

        self.rename_button.clicked.connect(lambda: rename_callback(self.chat_id))
        self.pin_button.clicked.connect(lambda: pin_callback(self.chat_id))
        self.delete_button.clicked.connect(lambda: delete_callback(self.chat_id))

        self.layout.addWidget(self.rename_button)
        self.layout.addWidget(self.pin_button)
        self.layout.addWidget(self.delete_button)

        self.setStyleSheet(f"""
            ChatItem {{
                background: transparent;
                border-radius: 9px;
            }}
            ChatItem:hover {{
                background: {BG_CARD};
            }}
        """)


# =========================================================
# MULTI-LINE AUTO-EXPANDING PROMPT INPUT
# =========================================================

class ChatPromptInput(QTextEdit):
    send_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Message Orsearch... (Enter to send, Shift+Enter for new line)")
        self.setFixedHeight(46)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textChanged.connect(self.auto_adjust_height)

        self.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {TEXT_PRIMARY};
                border: none;
                font-size: 14px;
                line-height: 1.4;
                padding: 4px 6px;
                selection-background-color: {EMERALD_BG};
                selection-color: {EMERALD_MINT};
            }}
        """)

    def auto_adjust_height(self):
        doc_height = int(self.document().size().height())
        new_height = max(46, min(140, doc_height + 12))
        if self.height() != new_height:
            self.setFixedHeight(new_height)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier):
                super().keyPressEvent(event)
            else:
                text = self.toPlainText().strip()
                if text:
                    self.send_requested.emit(text)
                    self.clear()
                    self.setFixedHeight(46)
                event.accept()
        else:
            super().keyPressEvent(event)


# =========================================================
# MAIN ORSEARCH WINDOW
# =========================================================

class OrsearchWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Orsearch AI - Autonomous Desktop Agent")
        self.resize(1240, 800)
        self.setMinimumSize(960, 640)

        self.chats = {}
        self.current_chat = None
        self.chat_counter = 0
        self.worker = None

        self.search_filter_text = ""

        # Thinking animation timer
        self.thinking_dots_count = 0
        self.thinking_timer = QTimer(self)
        self.thinking_timer.timeout.connect(self.animate_thinking)

        self.build_ui()
        self.new_chat()

    # =====================================================
    # BUILD UI
    # =====================================================

    def build_ui(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BG_MAIN};
            }}
            QWidget {{
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }}
            QScrollBar:vertical {{
                background: {BG_MAIN};
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #232B3C;
                border-radius: 3px;
                min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {EMERALD};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =================================================
        # 1. SIDEBAR
        # =================================================
        sidebar = QFrame()
        sidebar.setFixedWidth(295)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER_SUBTLE};
            }}
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 18, 16, 16)
        sidebar_layout.setSpacing(12)

        # Top Branding
        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(12)

        logo_core = OrsearchCore(38)
        logo_title = QLabel("Orsearch")
        logo_title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 20px;
                font-weight: 700;
                letter-spacing: -0.3px;
            }}
        """)

        pro_badge = QLabel("PRO v2")
        pro_badge.setStyleSheet(f"""
            QLabel {{
                background: {EMERALD_BG};
                color: {EMERALD_MINT};
                border: 1px solid {EMERALD_BORDER};
                border-radius: 5px;
                font-size: 9px;
                font-weight: 800;
                padding: 2px 6px;
                letter-spacing: 0.5px;
            }}
        """)

        logo_layout.addWidget(logo_core)
        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(pro_badge)
        logo_layout.addStretch()

        sidebar_layout.addLayout(logo_layout)

        # New Chat Button
        self.new_chat_button = QPushButton("+  New Conversation")
        self.new_chat_button.setFixedHeight(42)
        self.new_chat_button.setCursor(Qt.PointingHandCursor)
        self.new_chat_button.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_CARD};
                border-radius: 10px;
                text-align: left;
                padding-left: 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BG_CARD_HOVER};
                border: 1px solid {EMERALD};
                color: {EMERALD_MINT};
            }}
        """)
        self.new_chat_button.clicked.connect(self.new_chat)
        sidebar_layout.addWidget(self.new_chat_button)

        # Search / Filter Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search conversations...")
        self.search_input.setFixedHeight(34)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: #0F131C;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_SUBTLE};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {EMERALD};
                background: {BG_CARD};
            }}
        """)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        sidebar_layout.addWidget(self.search_input)

        # Scroll Area for Chats
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 4, 0, 4)
        self.chat_layout.setSpacing(2)
        self.chat_layout.setAlignment(Qt.AlignTop)

        self.chat_scroll.setWidget(self.chat_container)
        sidebar_layout.addWidget(self.chat_scroll, 1)

        # Sidebar Bottom Info Panel
        bottom_box = QFrame()
        bottom_box.setStyleSheet(f"""
            QFrame {{
                background: #0F131C;
                border: 1px solid {BORDER_SUBTLE};
                border-radius: 9px;
                padding: 8px 10px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_box)
        bottom_layout.setContentsMargins(4, 4, 4, 4)

        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {EMERALD}; font-size: 10px;")

        model_info = QLabel("Ollama: qwen3:4b")
        model_info.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: 500;")

        bottom_layout.addWidget(status_dot)
        bottom_layout.addWidget(model_info)
        bottom_layout.addStretch()

        sidebar_layout.addWidget(bottom_box)

        # =================================================
        # 2. MAIN CONTENT AREA
        # =================================================
        content = QFrame()
        content.setStyleSheet(f"""
            QFrame {{
                background: {BG_CONTENT};
            }}
        """)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 20, 32, 22)
        content_layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        header.setSpacing(12)

        self.page_title = QLabel("New Conversation")
        self.page_title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 18px;
                font-weight: 700;
            }}
        """)

        self.rename_current_btn = QPushButton("✎")
        self.rename_current_btn.setToolTip("Rename current conversation")
        self.rename_current_btn.setFixedSize(26, 26)
        self.rename_current_btn.setCursor(Qt.PointingHandCursor)
        self.rename_current_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SUBTLE};
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {BG_CARD};
                color: {TEXT_PRIMARY};
            }}
        """)
        self.rename_current_btn.clicked.connect(lambda: self.rename_chat(self.current_chat))

        self.status_label = QLabel("● READY")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {EMERALD_MINT};
                background: {EMERALD_BG};
                border: 1px solid {EMERALD_BORDER};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
        """)

        self.clear_chat_btn = QPushButton("🗑️ Clear")
        self.clear_chat_btn.setToolTip("Clear messages in current chat")
        self.clear_chat_btn.setFixedHeight(28)
        self.clear_chat_btn.setCursor(Qt.PointingHandCursor)
        self.clear_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                color: {TEXT_MUTED};
                border: 1px solid {BORDER_CARD};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {BG_CARD_HOVER};
                color: {TEXT_PRIMARY};
            }}
        """)
        self.clear_chat_btn.clicked.connect(self.clear_current_chat_messages)

        header.addWidget(self.page_title)
        header.addWidget(self.rename_current_btn)
        header.addWidget(self.status_label)
        header.addStretch()
        header.addWidget(self.clear_chat_btn)

        content_layout.addLayout(header)

        # Welcome / Hero Screen (When Chat Is Empty)
        self.welcome = QWidget()
        welcome_layout = QVBoxLayout(self.welcome)
        welcome_layout.setAlignment(Qt.AlignCenter)
        welcome_layout.setSpacing(14)

        core_hero = OrsearchCore(105)

        welcome_title = QLabel("What can I do for you today?")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 26px;
                font-weight: 700;
                letter-spacing: -0.4px;
                margin-top: 4px;
            }}
        """)

        welcome_subtitle = QLabel(
            "Search the web, automate desktop apps, take screenshots, or execute computer tasks."
        )
        welcome_subtitle.setAlignment(Qt.AlignCenter)
        welcome_subtitle.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MUTED};
                font-size: 14px;
                margin-bottom: 8px;
            }}
        """)

        welcome_layout.addWidget(core_hero, 0, Qt.AlignCenter)
        welcome_layout.addWidget(welcome_title)
        welcome_layout.addWidget(welcome_subtitle)

        # 4 Interactive Hero Prompt Cards (2x2 Grid)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(12)
        cards_grid.setContentsMargins(40, 10, 40, 10)

        self.add_hero_card(
            cards_grid,
            0,
            0,
            "🌐 Web Search",
            "Search Google for latest tech & AI news",
            "Search Google for latest AI news 2026",
        )
        self.add_hero_card(
            cards_grid,
            0,
            1,
            "💻 Launch Chrome",
            "Open Chrome browser and navigate",
            "Open Chrome",
        )
        self.add_hero_card(
            cards_grid,
            1,
            0,
            "📝 Quick Notepad",
            "Launch Notepad to write notes & checklist",
            "Open Notepad",
        )
        self.add_hero_card(
            cards_grid,
            1,
            1,
            "📸 Screen Vision",
            "Capture screenshot and inspect desktop",
            "Take a screenshot",
        )

        welcome_layout.addLayout(cards_grid)
        content_layout.addWidget(self.welcome)

        # Chat View (QTextEdit)
        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: none;
                padding: 4px 6px;
                font-size: 14px;
            }}
        """)
        content_layout.addWidget(self.chat_view, 1)

        # Animated Thinking Indicator Bar (Appears when waiting for agent)
        self.thinking_bar = QFrame()
        self.thinking_bar.setStyleSheet(f"""
            QFrame {{
                background: #0B1914;
                border: 1px solid {EMERALD_BORDER};
                border-radius: 9px;
                padding: 8px 14px;
            }}
        """)
        thinking_layout = QHBoxLayout(self.thinking_bar)
        thinking_layout.setContentsMargins(6, 4, 6, 4)

        self.thinking_label = QLabel("⚡ Orsearch is analyzing and planning actions...")
        self.thinking_label.setStyleSheet(f"""
            QLabel {{
                color: {EMERALD_MINT};
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        thinking_layout.addWidget(self.thinking_label)
        thinking_layout.addStretch()

        self.thinking_bar.hide()
        content_layout.addWidget(self.thinking_bar)

        # Quick Action Prompt Pills Bar
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)

        self.add_quick_pill(quick_layout, "🌐 Search Web", "Search Google for ")
        self.add_quick_pill(quick_layout, "💻 Open Chrome", "Open Chrome")
        self.add_quick_pill(quick_layout, "📝 Open Notepad", "Open Notepad")
        self.add_quick_pill(quick_layout, "📸 Screenshot", "Take a screenshot")
        quick_layout.addStretch()

        content_layout.addLayout(quick_layout)

        # Premium Expanding Input Box Container
        input_container = QFrame()
        input_container.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER_CARD};
                border-radius: 14px;
            }}
            QFrame:hover {{
                border: 1px solid {BORDER_HOVER};
            }}
        """)
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(12, 10, 12, 10)
        input_container_layout.setSpacing(6)

        self.prompt_input = ChatPromptInput()
        self.prompt_input.send_requested.connect(self.send_message)
        input_container_layout.addWidget(self.prompt_input)

        # Bottom Controls inside the Input Container
        bottom_input_bar = QHBoxLayout()
        bottom_input_bar.setSpacing(10)

        model_pill = QLabel("⚡ Qwen 3 Local Agent")
        model_pill.setStyleSheet(f"""
            QLabel {{
                background: {EMERALD_BG};
                color: {EMERALD_MINT};
                border: 1px solid {EMERALD_BORDER};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
            }}
        """)

        shortcut_hint = QLabel("Enter ↵ to send • Shift+Enter for newline")
        shortcut_hint.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SUBTLE};
                font-size: 11px;
            }}
        """)

        self.send_button = QPushButton("➤")
        self.send_button.setFixedSize(40, 36)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background: {EMERALD};
                color: #022013;
                border: none;
                border-radius: 9px;
                font-size: 16px;
                font-weight: 800;
            }}
            QPushButton:hover {{
                background: {EMERALD_MINT};
            }}
            QPushButton:pressed {{
                background: {EMERALD_DARK};
            }}
            QPushButton:disabled {{
                background: #1B2433;
                color: #4B5565;
            }}
        """)
        self.send_button.clicked.connect(self.trigger_send)

        bottom_input_bar.addWidget(model_pill)
        bottom_input_bar.addWidget(shortcut_hint)
        bottom_input_bar.addStretch()
        bottom_input_bar.addWidget(self.send_button)

        input_container_layout.addLayout(bottom_input_bar)
        content_layout.addWidget(input_container)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.set_status("READY")

    # =====================================================
    # HERO PROMPT CARDS (WELCOME SCREEN)
    # =====================================================

    def add_hero_card(self, grid, row, col, title, subtitle, command):
        card = QPushButton()
        card.setCursor(Qt.PointingHandCursor)
        card.setFixedHeight(72)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(3)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 13px;
                font-weight: 700;
                background: transparent;
            }}
        """)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_MUTED};
                font-size: 11px;
                background: transparent;
            }}
        """)

        card_layout.addWidget(title_lbl)
        card_layout.addWidget(sub_lbl)

        card.setStyleSheet(f"""
            QPushButton {{
                background: {BG_PANEL};
                border: 1px solid {BORDER_CARD};
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {BG_CARD_HOVER};
                border: 1px solid {EMERALD};
            }}
        """)

        card.clicked.connect(lambda: self.set_input_and_focus(command))
        grid.addWidget(card, row, col)

    # =====================================================
    # QUICK ACTION PILL
    # =====================================================

    def add_quick_pill(self, layout, title, command):
        button = QPushButton(title)
        button.setFixedHeight(28)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background: {BG_PANEL};
                color: {TEXT_MUTED};
                border: 1px solid {BORDER_SUBTLE};
                border-radius: 7px;
                padding: 0 12px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {TEXT_PRIMARY};
                border: 1px solid {EMERALD_BORDER};
                background: {BG_CARD};
            }}
        """)
        button.clicked.connect(lambda: self.set_input_and_focus(command))
        layout.addWidget(button)

    def set_input_and_focus(self, text):
        self.prompt_input.setPlainText(text)
        self.prompt_input.setFocus()
        cursor = self.prompt_input.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.prompt_input.setTextCursor(cursor)

    # =====================================================
    # LIVE STATUS BADGE
    # =====================================================

    def set_status(self, status):
        self.status_label.setText(f"● {status}")

        if status == "READY":
            color = EMERALD_MINT
            bg = EMERALD_BG
            border = EMERALD_BORDER
        elif status in ["THINKING", "EXECUTING"]:
            color = AMBER
            bg = AMBER_BG
            border = AMBER_BORDER
        elif status == "DONE":
            color = EMERALD_MINT
            bg = EMERALD_BG
            border = EMERALD_BORDER
        else:
            color = RED
            bg = RED_BG
            border = RED_BORDER

        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: {bg};
                border: 1px solid {border};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
        """)

    # =====================================================
    # SEARCH FILTER IN SIDEBAR
    # =====================================================

    def on_search_text_changed(self, text):
        self.search_filter_text = text.strip().lower()
        self.rebuild_chat_list()

    # =====================================================
    # REBUILD CHAT LIST (SIDEBAR)
    # =====================================================

    def rebuild_chat_list(self):
        # Clear existing items
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        filtered_chats = [
            (cid, c)
            for cid, c in self.chats.items()
            if not self.search_filter_text
            or self.search_filter_text in c["title"].lower()
        ]

        # Split into pinned and recent
        pinned_chats = [
            (cid, c) for cid, c in filtered_chats if c.get("pinned", False)
        ]
        recent_chats = [
            (cid, c) for cid, c in filtered_chats if not c.get("pinned", False)
        ]

        if pinned_chats:
            pinned_header = QLabel("📌 PINNED")
            pinned_header.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SUBTLE};
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 0.8px;
                    padding: 8px 6px 4px 6px;
                }}
            """)
            self.chat_layout.addWidget(pinned_header)

            for chat_id, chat in pinned_chats:
                is_active = chat_id == self.current_chat
                row = ChatItem(
                    chat_id=chat_id,
                    title=chat["title"],
                    pinned=True,
                    is_active=is_active,
                    select_callback=self.select_chat,
                    rename_callback=self.rename_chat,
                    pin_callback=self.toggle_pin,
                    delete_callback=self.delete_chat,
                )
                self.chat_layout.addWidget(row)

        if recent_chats:
            recent_header = QLabel("CONVERSATIONS")
            recent_header.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SUBTLE};
                    font-size: 10px;
                    font-weight: 700;
                    letter-spacing: 0.8px;
                    padding: 8px 6px 4px 6px;
                }}
            """)
            self.chat_layout.addWidget(recent_header)

            for chat_id, chat in recent_chats:
                is_active = chat_id == self.current_chat
                row = ChatItem(
                    chat_id=chat_id,
                    title=chat["title"],
                    pinned=False,
                    is_active=is_active,
                    select_callback=self.select_chat,
                    rename_callback=self.rename_chat,
                    pin_callback=self.toggle_pin,
                    delete_callback=self.delete_chat,
                )
                self.chat_layout.addWidget(row)

    # =====================================================
    # NEW CONVERSATION
    # =====================================================

    def new_chat(self):
        self.chat_counter += 1
        chat_id = f"chat_{self.chat_counter}"

        self.chats[chat_id] = {
            "title": f"Chat {self.chat_counter}",
            "pinned": False,
            "messages": [],
        }

        self.current_chat = chat_id
        self.rebuild_chat_list()
        self.show_chat()
        self.prompt_input.setFocus()

    # =====================================================
    # SELECT CONVERSATION
    # =====================================================

    def select_chat(self, chat_id):
        if chat_id not in self.chats:
            return

        self.current_chat = chat_id
        self.rebuild_chat_list()
        self.show_chat()

    # =====================================================
    # DISPLAY CURRENT CHAT
    # =====================================================

    def show_chat(self):
        if not self.current_chat:
            return

        chat = self.chats[self.current_chat]
        self.page_title.setText(chat["title"])
        self.chat_view.clear()

        messages = chat.get("messages", [])

        if not messages:
            self.chat_view.hide()
            self.welcome.show()
            return

        self.welcome.hide()
        self.chat_view.show()

        for msg in messages:
            self.render_message(
                role=msg.get("role", "assistant"),
                text=msg.get("text", ""),
                actions=msg.get("actions", []),
                timestamp=msg.get("time", ""),
            )

    # =====================================================
    # RENDER RICH MESSAGE BUBBLE
    # =====================================================

    def render_message(self, role, text, actions=None, timestamp=""):
        if not timestamp:
            timestamp = datetime.now().strftime("%H:%M")

        if role == "user":
            formatted_text = render_markdown(text)
            content = f"""
            <div style="margin: 14px 10px 14px 40px; padding: 14px 18px; background: #131A26; border: 1px solid #222E42; border-radius: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span style="color: #38BDF8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">👤 YOU</span>
                    <span style="color: {TEXT_SUBTLE}; font-size: 10px; margin-left: 10px;">{timestamp}</span>
                </div>
                <div style="color: {TEXT_PRIMARY}; font-size: 14px; line-height: 1.6;">
                    {formatted_text}
                </div>
            </div>
            """
        elif role == "system":
            safe_text = html.escape(text)
            content = f"""
            <div style="margin: 8px 12px; color: {TEXT_MUTED}; font-size: 12px; font-style: italic;">
                {safe_text}
            </div>
            """
        else:
            # Assistant message with optional executed action cards
            formatted_text = render_markdown(text)
            actions_html = render_actions_summary(actions) if actions else ""

            content = f"""
            <div style="margin: 14px 40px 14px 10px; padding: 16px 20px; background: {BG_PANEL}; border: 1px solid {BORDER_CARD}; border-left: 3px solid {EMERALD}; border-radius: 14px;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="color: {EMERALD_MINT}; font-size: 11px; font-weight: 800; letter-spacing: 0.6px;">⚡ ORSEARCH AI</span>
                    <span style="background: {EMERALD_BG}; color: {EMERALD_MINT}; border: 1px solid {EMERALD_BORDER}; border-radius: 4px; font-size: 9px; font-weight: 700; padding: 1px 5px; margin-left: 8px;">PRO AGENT</span>
                    <span style="color: {TEXT_SUBTLE}; font-size: 10px; margin-left: 10px;">{timestamp}</span>
                </div>
                {actions_html}
                <div style="color: #E2E8F0; font-size: 14px; line-height: 1.6;">
                    {formatted_text}
                </div>
            </div>
            """

        self.chat_view.moveCursor(QTextCursor.End)
        self.chat_view.insertHtml(content)
        self.chat_view.insertPlainText("\n")

        # Scroll smoothly to bottom
        sb = self.chat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def trigger_send(self):
        text = self.prompt_input.toPlainText().strip()
        if text:
            self.send_message(text)
            self.prompt_input.clear()
            self.prompt_input.setFixedHeight(46)

    def send_message(self, text):
        if not text:
            return

        if self.worker and self.worker.isRunning():
            return

        self.welcome.hide()
        self.chat_view.show()

        time_now = datetime.now().strftime("%H:%M")

        # Record user message
        self.chats[self.current_chat]["messages"].append({
            "role": "user",
            "text": text,
            "time": time_now,
        })

        self.render_message("user", text, timestamp=time_now)

        # Update chat title if it's still default
        chat_data = self.chats[self.current_chat]
        if chat_data["title"].startswith("Chat "):
            new_title = text[:26].strip()
            if len(text) > 26:
                new_title += "..."
            chat_data["title"] = new_title
            self.page_title.setText(new_title)
            self.rebuild_chat_list()

        # Update UI state to thinking
        self.set_status("THINKING")
        self.send_button.setDisabled(True)
        self.prompt_input.setDisabled(True)

        # Start thinking animation
        self.thinking_dots_count = 0
        self.thinking_label.setText("⚡ Orsearch is analyzing and planning actions...")
        self.thinking_bar.show()
        self.thinking_timer.start(400)

        # Spawn Agent Worker
        self.worker = AgentWorker(text)
        self.worker.finished.connect(self.agent_finished)
        self.worker.failed.connect(self.agent_failed)
        self.worker.start()

    def animate_thinking(self):
        self.thinking_dots_count = (self.thinking_dots_count + 1) % 4
        dots = "." * self.thinking_dots_count
        self.thinking_label.setText(f"⚡ Orsearch is executing actions{dots}")

    # =====================================================
    # AGENT RESPONSE HANDLERS
    # =====================================================

    def agent_finished(self, result):
        self.thinking_timer.stop()
        self.thinking_bar.hide()

        actions_list = []
        if isinstance(result, dict):
            message = result.get("message", "Task completed.")
            success = result.get("success", True)
            actions_list = result.get("actions", [])
        else:
            message = str(result)
            success = True

        if success:
            self.set_status("DONE")
        else:
            self.set_status("FAILED")

        time_now = datetime.now().strftime("%H:%M")

        # Save assistant response
        self.chats[self.current_chat]["messages"].append({
            "role": "assistant",
            "text": message,
            "actions": actions_list,
            "time": time_now,
        })

        self.render_message(
            role="assistant",
            text=message,
            actions=actions_list,
            timestamp=time_now,
        )

        self.send_button.setDisabled(False)
        self.prompt_input.setDisabled(False)
        self.prompt_input.setFocus()
        self.rebuild_chat_list()
        self.worker = None

    def agent_failed(self, error):
        self.thinking_timer.stop()
        self.thinking_bar.hide()
        self.set_status("ERROR")

        time_now = datetime.now().strftime("%H:%M")
        message = f"**Agent Error**: Unable to complete action.\n`{error}`"

        self.chats[self.current_chat]["messages"].append({
            "role": "assistant",
            "text": message,
            "actions": [],
            "time": time_now,
        })

        self.render_message("assistant", message, timestamp=time_now)

        self.send_button.setDisabled(False)
        self.prompt_input.setDisabled(False)
        self.prompt_input.setFocus()
        self.worker = None

    # =====================================================
    # CONVERSATION ACTIONS
    # =====================================================

    def clear_current_chat_messages(self):
        if not self.current_chat:
            return

        answer = QMessageBox.question(
            self,
            "Clear Chat",
            "Clear all messages in this conversation?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.chats[self.current_chat]["messages"] = []
            self.show_chat()

    def rename_chat(self, chat_id):
        if chat_id not in self.chats:
            return

        old_title = self.chats[chat_id]["title"]
        title, ok = QInputDialog.getText(
            self, "Rename Conversation", "Enter conversation title:", text=old_title
        )
        if ok and title.strip():
            self.chats[chat_id]["title"] = title.strip()
            self.rebuild_chat_list()
            if chat_id == self.current_chat:
                self.page_title.setText(title.strip())

    def toggle_pin(self, chat_id):
        if chat_id not in self.chats:
            return

        self.chats[chat_id]["pinned"] = not self.chats[chat_id].get("pinned", False)
        self.rebuild_chat_list()

    def delete_chat(self, chat_id):
        if chat_id not in self.chats:
            return

        if len(self.chats) == 1:
            QMessageBox.information(
                self, "Delete Conversation", "At least one conversation must remain."
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Conversation",
            "Delete this conversation permanently?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        del self.chats[chat_id]

        if self.current_chat == chat_id:
            self.current_chat = next(iter(self.chats))

        self.rebuild_chat_list()
        self.show_chat()


# =========================================================
# APPLICATION ENTRYPOINT
# =========================================================

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Orsearch")

    window = OrsearchWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()