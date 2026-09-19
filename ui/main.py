import sys
import uuid
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QSize, QPointF
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QFont,
)
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QLineEdit,
    QMessageBox,
    QInputDialog,
    QSizePolicy,
)


RED = "#ff3b3b"
RED_DARK = "#c62828"
BG = "#090a0c"
SIDEBAR = "#0d0f12"
CARD = "#111317"
CARD_HOVER = "#17191e"
BORDER = "#22252b"
TEXT = "#f5f5f5"
MUTED = "#858a94"


class OrsearchCore(QWidget):

    def __init__(self, parent=None, size=110):
        super().__init__(parent)

        self.setFixedSize(size, size)

        self.angle = 0
        self.pulse = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def animate(self):
        self.angle += 1.2
        self.pulse += 0.08
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()
        cx = center.x()
        cy = center.y()

        # Outer glow
        for radius, alpha in [
            (45, 15),
            (40, 20),
            (35, 28),
        ]:

            color = QColor(255, 59, 59, alpha)

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)

            painter.drawEllipse(
                QPointF(cx, cy),
                radius,
                radius
            )

        # Outer ring
        pen = QPen(QColor(255, 59, 59, 80))
        pen.setWidth(1)

        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        painter.drawEllipse(
            QPointF(cx, cy),
            39,
            39
        )

        # Rotating arc
        pen = QPen(QColor(255, 59, 59, 230))
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)

        painter.setPen(pen)

        painter.drawArc(
            23,
            23,
            54,
            54,
            int(-self.angle * 16),
            90 * 16
        )

        # S shape
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(7)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        painter.setPen(pen)

        path_points = [
            (cx + 18, cy - 20),
            (cx + 7, cy - 27),
            (cx - 10, cy - 25),
            (cx - 19, cy - 15),
            (cx - 19, cy - 5),
            (cx - 10, cy + 2),
            (cx + 9, cy + 8),
            (cx + 18, cy + 15),
            (cx + 15, cy + 23),
            (cx + 3, cy + 28),
            (cx - 13, cy + 25),
        ]

        for i in range(len(path_points) - 1):

            x1, y1 = path_points[i]
            x2, y2 = path_points[i + 1]

            painter.drawLine(
                x1,
                y1,
                x2,
                y2
            )

        painter.end()


class ChatRow(QWidget):

    def __init__(
        self,
        chat_id,
        title,
        pinned,
        select_callback,
        pin_callback,
        rename_callback,
        delete_callback,
        parent=None
    ):

        super().__init__(parent)

        self.chat_id = chat_id

        self.setMinimumHeight(52)
        self.setMaximumHeight(52)

        self.setStyleSheet(
            f"""
            ChatRow {{
                background: transparent;
                border-radius: 9px;
            }}

            ChatRow:hover {{
                background: {CARD_HOVER};
            }}

            QLabel {{
                color: {TEXT};
                background: transparent;
            }}

            QPushButton {{
                background: transparent;
                border: none;
                color: {MUTED};
                font-size: 14px;
                border-radius: 6px;
            }}

            QPushButton:hover {{
                background: #22252b;
                color: white;
            }}
            """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 6, 4)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        self.title_label.setFont(
            QFont("Segoe UI", 9)
        )

        layout.addWidget(self.title_label)

        self.edit_button = QPushButton("✎")
        self.edit_button.setFixedSize(28, 32)

        self.edit_button.clicked.connect(
            lambda: rename_callback(self.chat_id)
        )

        layout.addWidget(self.edit_button)

        self.pin_button = QPushButton(
            "📌" if pinned else "○"
        )

        self.pin_button.setFixedSize(28, 32)

        self.pin_button.clicked.connect(
            lambda: pin_callback(self.chat_id)
        )

        layout.addWidget(self.pin_button)

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(28, 32)

        self.delete_button.clicked.connect(
            lambda: delete_callback(self.chat_id)
        )

        layout.addWidget(self.delete_button)

        self.select_callback = select_callback

    def mousePressEvent(self, event):

        if event.button() == Qt.LeftButton:
            self.select_callback(self.chat_id)

        super().mousePressEvent(event)


class OrsearchWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Orsearch")

        self.resize(1250, 780)

        self.setMinimumSize(950, 600)

        self.chats = {}

        self.current_chat = None

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {BG};
            }}

            QWidget {{
                font-family: "Segoe UI";
            }}

            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}

            QListWidget::item {{
                border: none;
                padding: 0px;
                margin: 2px 4px;
                background: transparent;
            }}

            QListWidget::item:selected {{
                background: transparent;
            }}

            QTextEdit {{
                background: transparent;
                border: none;
                color: {TEXT};
                font-size: 15px;
                selection-background-color: #343840;
            }}

            QLineEdit {{
                background: #15171b;
                border: 1px solid #292c32;
                border-radius: 14px;
                color: white;
                padding: 13px 16px;
                font-size: 14px;
            }}

            QLineEdit:focus {{
                border: 1px solid #454952;
            }}

            QPushButton {{
                border: none;
            }}
            """
        )

        self.build_ui()

        self.new_chat()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def build_ui(self):

        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)

        # =====================================================
        # SIDEBAR
        # =====================================================

        sidebar = QWidget()

        sidebar.setFixedWidth(275)

        sidebar.setStyleSheet(
            f"""
            QWidget {{
                background: {SIDEBAR};
            }}
            """
        )

        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.setContentsMargins(
            16,
            18,
            16,
            14
        )

        sidebar_layout.setSpacing(12)

        # Logo
        logo_layout = QHBoxLayout()

        core = OrsearchCore(
            size=58
        )

        logo_layout.addWidget(core)

        logo_text = QVBoxLayout()

        name = QLabel("Orsearch")

        name.setFont(
            QFont("Segoe UI", 17, QFont.Bold)
        )

        name.setStyleSheet(
            f"color: {TEXT};"
        )

        subtitle = QLabel("AI Computer Agent")

        subtitle.setFont(
            QFont("Segoe UI", 8)
        )

        subtitle.setStyleSheet(
            f"color: {MUTED};"
        )

        logo_text.addWidget(name)
        logo_text.addWidget(subtitle)

        logo_layout.addLayout(logo_text)

        logo_layout.addStretch()

        sidebar_layout.addLayout(logo_layout)

        # New Chat
        self.new_chat_button = QPushButton(
            "+  New Chat"
        )

        self.new_chat_button.setFixedHeight(44)

        self.new_chat_button.setCursor(
            Qt.PointingHandCursor
        )

        self.new_chat_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {RED};
                color: white;
                border-radius: 10px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
                padding-left: 16px;
            }}

            QPushButton:hover {{
                background: #ff5050;
            }}

            QPushButton:pressed {{
                background: {RED_DARK};
            }}
            """
        )

        self.new_chat_button.clicked.connect(
            self.new_chat
        )

        sidebar_layout.addWidget(
            self.new_chat_button
        )

        # Section
        section = QLabel("YOUR CHATS")

        section.setFont(
            QFont("Segoe UI", 8, QFont.Bold)
        )

        section.setStyleSheet(
            f"""
            color: {MUTED};
            padding: 8px 4px 2px 4px;
            letter-spacing: 1px;
            """
        )

        sidebar_layout.addWidget(section)

        # Chat list
        self.chat_list = QListWidget()

        self.chat_list.setSpacing(2)

        sidebar_layout.addWidget(
            self.chat_list
        )

        # Bottom
        bottom = QVBoxLayout()

        line = QFrameLine()

        bottom.addWidget(line)

        status_layout = QHBoxLayout()

        status_dot = QLabel("●")

        status_dot.setStyleSheet(
            "color: #38d996; font-size: 11px;"
        )

        status = QLabel("System Ready")

        status.setStyleSheet(
            f"color: {MUTED}; font-size: 11px;"
        )

        status_layout.addWidget(
            status_dot
        )

        status_layout.addWidget(
            status
        )

        status_layout.addStretch()

        bottom.addLayout(
            status_layout
        )

        sidebar_layout.addLayout(
            bottom
        )

        main_layout.addWidget(
            sidebar
        )

        # =====================================================
        # MAIN CONTENT
        # =====================================================

        content = QWidget()

        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        content_layout.setSpacing(0)

        # Header
        header = QWidget()

        header.setFixedHeight(68)

        header_layout = QHBoxLayout(header)

        header_layout.setContentsMargins(
            28,
            0,
            28,
            0
        )

        title = QLabel("Orsearch")

        title.setFont(
            QFont("Segoe UI", 14, QFont.Bold)
        )

        title.setStyleSheet(
            f"color: {TEXT};"
        )

        header_layout.addWidget(
            title
        )

        header_layout.addStretch()

        ready = QLabel("●  READY")

        ready.setFont(
            QFont("Segoe UI", 8, QFont.Bold)
        )

        ready.setStyleSheet(
            "color: #38d996;"
        )

        header_layout.addWidget(
            ready
        )

        content_layout.addWidget(
            header
        )

        # Separator
        separator = QFrameLine()

        content_layout.addWidget(
            separator
        )

        # Chat
        self.chat_view = QTextEdit()

        self.chat_view.setReadOnly(True)

        self.chat_view.setAcceptRichText(True)

        content_layout.addWidget(
            self.chat_view
        )

        # Input section
        input_container = QWidget()

        input_layout = QVBoxLayout(
            input_container
        )

        input_layout.setContentsMargins(
            24,
            12,
            24,
            22
        )

        # Quick buttons
        quick_layout = QHBoxLayout()

        quick_layout.setSpacing(8)

        self.create_quick_button(
            quick_layout,
            "Browse Web",
            "Chrome kholo aur web browse karo"
        )

        self.create_quick_button(
            quick_layout,
            "Control PC",
            "Notepad kholo"
        )

        self.create_quick_button(
            quick_layout,
            "Screenshot",
            "Take a screenshot"
        )

        quick_layout.addStretch()

        input_layout.addLayout(
            quick_layout
        )

        # Input row
        row = QHBoxLayout()

        row.setSpacing(10)

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Ask Orsearch to do something..."
        )

        self.input.setMinimumHeight(48)

        self.input.returnPressed.connect(
            self.send_message
        )

        row.addWidget(
            self.input
        )

        self.send_button = QPushButton(
            "➤"
        )

        self.send_button.setFixedSize(
            48,
            48
        )

        self.send_button.setCursor(
            Qt.PointingHandCursor
        )

        self.send_button.setStyleSheet(
            f"""
            QPushButton {{
                background: {RED};
                color: white;
                border-radius: 13px;
                font-size: 18px;
            }}

            QPushButton:hover {{
                background: #ff5050;
            }}
            """
        )

        self.send_button.clicked.connect(
            self.send_message
        )

        row.addWidget(
            self.send_button
        )

        input_layout.addLayout(
            row
        )

        content_layout.addWidget(
            input_container
        )

        main_layout.addWidget(
            content
        )

    # ---------------------------------------------------------
    # QUICK BUTTON
    # ---------------------------------------------------------

    def create_quick_button(
        self,
        layout,
        text,
        command
    ):

        button = QPushButton(text)

        button.setFixedHeight(32)

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setStyleSheet(
            f"""
            QPushButton {{
                background: #131519;
                color: #a7abb4;
                border: 1px solid #24272d;
                border-radius: 9px;
                padding: 0px 13px;
                font-size: 11px;
            }}

            QPushButton:hover {{
                background: #1b1d22;
                color: white;
                border-color: #363a42;
            }}
            """
        )

        button.clicked.connect(
            lambda: self.set_input(command)
        )

        layout.addWidget(
            button
        )

    # ---------------------------------------------------------
    # NEW CHAT
    # ---------------------------------------------------------

    def new_chat(self):

        chat_id = str(
            uuid.uuid4()
        )

        self.chats[chat_id] = {
            "title": "New Chat",
            "pinned": False,
            "messages": [],
            "created": datetime.now()
        }

        self.current_chat = chat_id

        self.rebuild_chat_list()

        self.show_welcome()

        self.input.clear()

        self.input.setFocus()

    # ---------------------------------------------------------
    # CHAT LIST
    # ---------------------------------------------------------

    def rebuild_chat_list(self):

        self.chat_list.clear()

        # Pinned chats first
        chat_items = sorted(
            self.chats.items(),
            key=lambda item: (
                not item[1]["pinned"],
                item[1]["created"]
            )
        )

        for chat_id, chat in chat_items:

            item = QListWidgetItem()

            # IMPORTANT:
            # setSizeHint needs QSize, not int
            item.setSizeHint(
                QSize(0, 52)
            )

            row = ChatRow(
                chat_id,
                chat["title"],
                chat["pinned"],
                self.select_chat,
                self.toggle_pin,
                self.rename_chat,
                self.delete_chat
            )

            self.chat_list.addItem(
                item
            )

            self.chat_list.setItemWidget(
                item,
                row
            )

            if chat_id == self.current_chat:

                item.setSelected(True)

                self.chat_list.setCurrentItem(
                    item
                )

                row.setStyleSheet(
                    f"""
                    ChatRow {{
                        background: #191a1f;
                        border-left: 2px solid {RED};
                        border-radius: 9px;
                    }}

                    QLabel {{
                        color: {TEXT};
                        background: transparent;
                    }}

                    QPushButton {{
                        background: transparent;
                        border: none;
                        color: {MUTED};
                        border-radius: 6px;
                    }}

                    QPushButton:hover {{
                        background: #292c32;
                        color: white;
                    }}
                    """
                )

    # ---------------------------------------------------------
    # SELECT CHAT
    # ---------------------------------------------------------

    def select_chat(self, chat_id):

        if chat_id not in self.chats:
            return

        self.current_chat = chat_id

        self.rebuild_chat_list()

        self.show_chat(
            chat_id
        )

        self.input.clear()

        self.input.setFocus()

    # ---------------------------------------------------------
    # SHOW CHAT
    # ---------------------------------------------------------

    def show_chat(self, chat_id):

        self.chat_view.clear()

        chat = self.chats.get(
            chat_id
        )

        if not chat:
            return

        if not chat["messages"]:

            self.show_welcome()

            return

        for message in chat["messages"]:

            self.add_message_to_view(
                message["role"],
                message["text"]
            )

        self.chat_view.verticalScrollBar().setValue(
            self.chat_view.verticalScrollBar().maximum()
        )

    # ---------------------------------------------------------
    # PIN
    # ---------------------------------------------------------

    def toggle_pin(self, chat_id):

        if chat_id not in self.chats:
            return

        self.chats[chat_id]["pinned"] = not self.chats[chat_id]["pinned"]

        self.rebuild_chat_list()

    # ---------------------------------------------------------
    # RENAME
    # ---------------------------------------------------------

    def rename_chat(self, chat_id):

        if chat_id not in self.chats:
            return

        old_title = self.chats[chat_id]["title"]

        title, ok = QInputDialog.getText(
            self,
            "Rename Chat",
            "Enter new chat name:",
            QLineEdit.Normal,
            old_title
        )

        if ok and title.strip():

            self.chats[chat_id]["title"] = title.strip()

            self.rebuild_chat_list()

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------

    def delete_chat(self, chat_id):

        if chat_id not in self.chats:
            return

        title = self.chats[chat_id]["title"]

        answer = QMessageBox.question(
            self,
            "Delete Chat",
            f'Delete "{title}"?\n\nThis action cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        del self.chats[chat_id]

        if chat_id == self.current_chat:

            self.current_chat = None

            if self.chats:

                # Open first available chat
                first_chat = next(
                    iter(self.chats)
                )

                self.current_chat = first_chat

                self.rebuild_chat_list()

                self.show_chat(
                    first_chat
                )

            else:

                self.new_chat()

        else:

            self.rebuild_chat_list()

    # ---------------------------------------------------------
    # WELCOME
    # ---------------------------------------------------------

    def show_welcome(self):

        self.chat_view.clear()

        html = f"""
        <div style="
            text-align:center;
            margin-top:90px;
        ">

            <div style="
                color:{TEXT};
                font-size:28px;
                font-weight:700;
            ">
                What can I do for you?
            </div>

            <div style="
                color:{MUTED};
                font-size:13px;
                margin-top:10px;
            ">
                Control your computer, browse the web,
                or ask me anything.
            </div>

        </div>
        """

        self.chat_view.setHtml(
            html
        )

    # ---------------------------------------------------------
    # INPUT
    # ---------------------------------------------------------

    def set_input(self, text):

        self.input.setText(
            text
        )

        self.input.setFocus()

    # ---------------------------------------------------------
    # SEND
    # ---------------------------------------------------------

    def send_message(self):

        text = self.input.text().strip()

        if not text:
            return

        if not self.current_chat:
            self.new_chat()

        chat = self.chats[
            self.current_chat
        ]

        # First message becomes title
        if (
            chat["title"] == "New Chat"
            and not chat["messages"]
        ):

            clean_title = text.replace(
                "\n",
                " "
            ).strip()

            if len(clean_title) > 30:
                clean_title = (
                    clean_title[:30] + "..."
                )

            chat["title"] = clean_title

            self.rebuild_chat_list()

        chat["messages"].append(
            {
                "role": "user",
                "text": text
            }
        )

        self.add_message_to_view(
            "user",
            text
        )

        self.input.clear()

        self.chat_view.verticalScrollBar().setValue(
            self.chat_view.verticalScrollBar().maximum()
        )

        # AI response
        QTimer.singleShot(
            400,
            lambda: self.ai_response(text)
        )

    # ---------------------------------------------------------
    # AI RESPONSE
    # ---------------------------------------------------------

    def ai_response(self, user_text):

        response = self.generate_response(
            user_text
        )

        if self.current_chat not in self.chats:
            return

        self.chats[
            self.current_chat
        ]["messages"].append(
            {
                "role": "assistant",
                "text": response
            }
        )

        self.add_message_to_view(
            "assistant",
            response
        )

        self.chat_view.verticalScrollBar().setValue(
            self.chat_view.verticalScrollBar().maximum()
        )

    # ---------------------------------------------------------
    # TEMP RESPONSE
    # ---------------------------------------------------------

    def generate_response(self, text):

        lower = text.lower()

        if (
            "hello" in lower
            or "hi" in lower
            or "hey" in lower
        ):

            return (
                "Hello! I'm Orsearch. "
                "Tell me what you want me to do on your computer."
            )

        if "chrome" in lower:

            return (
                "I understand. The next step is to connect "
                "this UI with the Orsearch computer agent so "
                "I can actually control Chrome."
            )

        if "notepad" in lower:

            return (
                "Notepad control is ready to be connected "
                "with the PyAutoGUI agent."
            )

        if (
            "screenshot" in lower
            or "screen" in lower
        ):

            return (
                "Screenshot functionality is already available "
                "in the Orsearch agent. Vision analysis will be "
                "connected here next."
            )

        if (
            "web" in lower
            or "search" in lower
        ):

            return (
                "Web browsing will be handled through the "
                "computer-control agent using Chrome."
            )

        return (
            "Got it. I can understand this request, but my "
            "computer-control agent is not connected to the UI yet. "
            "Once connected, Orsearch will be able to plan the task "
            "and execute allowed actions on your PC."
        )

    # ---------------------------------------------------------
    # MESSAGE VIEW
    # ---------------------------------------------------------

    def add_message_to_view(
        self,
        role,
        text
    ):

        if role == "user":

            html = f"""
            <div style="
                margin:14px 10px;
                padding:13px 16px;
                background:#1b1d22;
                border-radius:12px;
            ">

                <div style="
                    color:#ffffff;
                    font-size:14px;
                    font-weight:600;
                    margin-bottom:5px;
                ">
                    You
                </div>

                <div style="
                    color:#e5e7eb;
                    font-size:14px;
                ">
                    {self.escape_html(text)}
                </div>

            </div>
            """

        else:

            html = f"""
            <div style="
                margin:14px 10px;
                padding:13px 16px;
                background:#101216;
                border:1px solid #20232a;
                border-radius:12px;
            ">

                <div style="
                    color:{RED};
                    font-size:14px;
                    font-weight:700;
                    margin-bottom:5px;
                ">
                    Orsearch
                </div>

                <div style="
                    color:#d7d9de;
                    font-size:14px;
                    line-height:1.5;
                ">
                    {self.escape_html(text)}
                </div>

            </div>
            """

        cursor = self.chat_view.textCursor()

        cursor.movePosition(
            cursor.MoveOperation.End
        )

        cursor.insertHtml(
            html
        )

        cursor.insertBlock()

        self.chat_view.setTextCursor(
            cursor
        )

    # ---------------------------------------------------------
    # HTML ESCAPE
    # ---------------------------------------------------------

    def escape_html(self, text):

        return (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )


class QFrameLine(QWidget):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setFixedHeight(1)

        self.setStyleSheet(
            "background:#202329;"
        )


def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Orsearch"
    )

    window = OrsearchWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()