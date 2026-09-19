import sys
import uuid

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
)


# ============================================================
# COLORS
# ============================================================

BG = "#09090b"
SIDEBAR = "#0d0d10"
CARD = "#111114"
CARD_HOVER = "#18181d"
BORDER = "#24242a"

WHITE = "#f5f5f5"
TEXT = "#d4d4d8"
MUTED = "#77777f"

RED = "#ff3b3b"


# ============================================================
# ORSEARCH ANIMATED CORE
# ============================================================

class OrsearchCore(QWidget):

    def __init__(self):
        super().__init__()

        self.angle = 0
        self.pulse = 0
        self.direction = 1

        self.setFixedSize(190, 190)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(35)

    def animate(self):

        self.angle += 1.5

        self.pulse += self.direction * 0.5

        if self.pulse >= 7:
            self.direction = -1

        if self.pulse <= 0:
            self.direction = 1

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        center = self.rect().center()

        radius = 45 + self.pulse

        # ----------------------------------------
        # Glow
        # ----------------------------------------

        for i in range(18, 0, -1):

            alpha = int(2 + (18 - i) * 1.5)

            painter.setPen(Qt.NoPen)

            painter.setBrush(
                QColor(255, 40, 40, alpha)
            )

            r = radius + i * 3

            painter.drawEllipse(
                center.x() - r,
                center.y() - r,
                r * 2,
                r * 2
            )

        # ----------------------------------------
        # Outer Ring
        # ----------------------------------------

        painter.setBrush(Qt.NoBrush)

        painter.setPen(
            QPen(
                QColor(255, 60, 60, 110),
                2
            )
        )

        painter.drawEllipse(
            center.x() - radius - 10,
            center.y() - radius - 10,
            (radius + 10) * 2,
            (radius + 10) * 2
        )

        # ----------------------------------------
        # Rotating Arc
        # ----------------------------------------

        painter.save()

        painter.translate(center)

        painter.rotate(self.angle)

        painter.setPen(
            QPen(
                QColor(255, 70, 70, 230),
                3
            )
        )

        painter.drawArc(
            -radius - 15,
            -radius - 15,
            (radius + 15) * 2,
            (radius + 15) * 2,
            20 * 16,
            105 * 16
        )

        painter.restore()

        # ----------------------------------------
        # Main Circle
        # ----------------------------------------

        painter.setBrush(
            QColor("#151518")
        )

        painter.setPen(
            QPen(
                QColor("#ff4545"),
                2
            )
        )

        painter.drawEllipse(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )

        # ----------------------------------------
        # S
        # ----------------------------------------

        painter.setPen(
            QColor("#ffffff")
        )

        painter.setFont(
            QFont(
                "Segoe UI",
                38,
                QFont.Bold
            )
        )

        painter.drawText(
            center.x() - 30,
            center.y() - 30,
            60,
            60,
            Qt.AlignCenter,
            "S"
        )


# ============================================================
# MAIN WINDOW
# ============================================================

class OrsearchWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Orsearch"
        )

        self.resize(
            1200,
            760
        )

        self.setMinimumSize(
            900,
            600
        )

        self.chats = {}

        self.current_chat = None

        self.setup_style()

        self.setup_ui()

        self.new_chat()


    # ========================================================
    # STYLE
    # ========================================================

    def setup_style(self):

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background: {BG};
            }}

            QWidget {{
                background: {BG};
                color: {TEXT};
                font-family: "Segoe UI";
            }}

            QFrame#sidebar {{
                background: {SIDEBAR};
                border-right: 1px solid {BORDER};
            }}

            QLabel#logoS {{
                color: {RED};
                font-size: 25px;
                font-weight: 800;
            }}

            QLabel#logo {{
                color: {WHITE};
                font-size: 20px;
                font-weight: 700;
            }}

            QPushButton {{
                background: transparent;
                color: {TEXT};
                border: none;
                border-radius: 9px;
                padding: 10px;
                font-size: 13px;
            }}

            QPushButton:hover {{
                background: {CARD_HOVER};
                color: {WHITE};
            }}

            QPushButton#newChat {{
                background: {RED};
                color: white;
                font-weight: 600;
                padding: 11px;
            }}

            QPushButton#newChat:hover {{
                background: #ff5050;
            }}

            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}

            QListWidget::item {{
                color: {MUTED};
                padding: 11px;
                border-radius: 8px;
                margin: 2px 0;
            }}

            QListWidget::item:hover {{
                background: {CARD_HOVER};
                color: {TEXT};
            }}

            QListWidget::item:selected {{
                background: #19191e;
                color: {WHITE};
                border-left: 2px solid {RED};
            }}

            QLabel#welcomeTitle {{
                color: {WHITE};
                font-size: 28px;
                font-weight: 650;
            }}

            QLabel#welcomeSub {{
                color: {MUTED};
                font-size: 14px;
            }}

            QFrame#inputBox {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 17px;
            }}

            QLineEdit {{
                background: transparent;
                border: none;
                color: {WHITE};
                font-size: 14px;
                padding: 6px;
            }}

            QPushButton#send {{
                background: {RED};
                color: white;
                border-radius: 10px;
                font-size: 17px;
                font-weight: 700;
            }}

            QPushButton#send:hover {{
                background: #ff5555;
            }}

            QPushButton#chip {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
                padding: 8px 13px;
                color: {TEXT};
            }}

            QPushButton#chip:hover {{
                background: {CARD_HOVER};
                border: 1px solid #5b2525;
                color: white;
            }}
            """
        )


    # ========================================================
    # UI
    # ========================================================

    def setup_ui(self):

        root = QWidget()

        root_layout = QHBoxLayout(
            root
        )

        root_layout.setContentsMargins(
            0, 0, 0, 0
        )

        root_layout.setSpacing(0)

        self.setCentralWidget(root)

        # ====================================================
        # SIDEBAR
        # ====================================================

        sidebar = QFrame()

        sidebar.setObjectName(
            "sidebar"
        )

        sidebar.setFixedWidth(
            245
        )

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            14,
            18,
            14,
            14
        )

        sidebar_layout.setSpacing(10)

        # Logo

        logo_layout = QHBoxLayout()

        logo_s = QLabel("S")

        logo_s.setObjectName(
            "logoS"
        )

        logo = QLabel(
            "ORSEARCH"
        )

        logo.setObjectName(
            "logo"
        )

        logo_layout.addWidget(
            logo_s
        )

        logo_layout.addWidget(
            logo
        )

        logo_layout.addStretch()

        sidebar_layout.addLayout(
            logo_layout
        )

        # New Chat

        self.new_chat_button = QPushButton(
            "+   New Chat"
        )

        self.new_chat_button.setObjectName(
            "newChat"
        )

        self.new_chat_button.clicked.connect(
            self.new_chat
        )

        sidebar_layout.addWidget(
            self.new_chat_button
        )

        # Recent chats

        recent = QLabel(
            "RECENT CHATS"
        )

        recent.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 10px;
                font-weight: 600;
                padding: 10px 5px 3px;
            }}
            """
        )

        sidebar_layout.addWidget(
            recent
        )

        self.chat_list = QListWidget()

        self.chat_list.itemClicked.connect(
            self.switch_chat
        )

        sidebar_layout.addWidget(
            self.chat_list
        )

        # Status

        line = QFrame()

        line.setFixedHeight(1)

        line.setStyleSheet(
            f"background: {BORDER};"
        )

        sidebar_layout.addWidget(
            line
        )

        self.status = QLabel(
            "●  Orsearch ready"
        )

        self.status.setStyleSheet(
            f"""
            QLabel {{
                color: {MUTED};
                font-size: 11px;
                padding: 5px;
            }}
            """
        )

        sidebar_layout.addWidget(
            self.status
        )

        root_layout.addWidget(
            sidebar
        )

        # ====================================================
        # MAIN
        # ====================================================

        main = QWidget()

        main_layout = QVBoxLayout(
            main
        )

        main_layout.setContentsMargins(
            32,
            20,
            32,
            24
        )

        main_layout.setSpacing(12)

        root_layout.addWidget(
            main
        )

        # Header

        header = QHBoxLayout()

        page_title = QLabel(
            "Orsearch"
        )

        page_title.setStyleSheet(
            f"""
            QLabel {{
                color: {WHITE};
                font-size: 15px;
                font-weight: 600;
            }}
            """
        )

        header.addWidget(
            page_title
        )

        header.addStretch()

        ready = QLabel(
            "●  READY"
        )

        ready.setStyleSheet(
            f"""
            QLabel {{
                color: #77777f;
                font-size: 10px;
                letter-spacing: 1px;
            }}
            """
        )

        header.addWidget(
            ready
        )

        main_layout.addLayout(
            header
        )

        # ====================================================
        # WELCOME
        # ====================================================

        self.welcome = QWidget()

        welcome_layout = QVBoxLayout(
            self.welcome
        )

        welcome_layout.setAlignment(
            Qt.AlignCenter
        )

        welcome_layout.setSpacing(
            8
        )

        self.core = OrsearchCore()

        welcome_layout.addWidget(
            self.core,
            alignment=Qt.AlignCenter
        )

        welcome_title = QLabel(
            "What can I do for you?"
        )

        welcome_title.setObjectName(
            "welcomeTitle"
        )

        welcome_title.setAlignment(
            Qt.AlignCenter
        )

        welcome_layout.addWidget(
            welcome_title
        )

        welcome_sub = QLabel(
            "Search, control and automate your computer."
        )

        welcome_sub.setObjectName(
            "welcomeSub"
        )

        welcome_sub.setAlignment(
            Qt.AlignCenter
        )

        welcome_layout.addWidget(
            welcome_sub
        )

        # Quick buttons

        chips = QHBoxLayout()

        chips.setAlignment(
            Qt.AlignCenter
        )

        commands = [
            (
                "🌐  Browse Web",
                "Open Chrome"
            ),
            (
                "🖥  Control PC",
                "Open Notepad"
            ),
            (
                "⚡  Screenshot",
                "Take a screenshot"
            ),
        ]

        for label, command in commands:

            button = QPushButton(
                label
            )

            button.setObjectName(
                "chip"
            )

            button.clicked.connect(
                lambda checked=False,
                value=command:
                self.set_input(value)
            )

            chips.addWidget(
                button
            )

        welcome_layout.addSpacing(
            10
        )

        welcome_layout.addLayout(
            chips
        )

        main_layout.addWidget(
            self.welcome,
            1
        )

        # ====================================================
        # CHAT AREA
        # ====================================================

        self.chat_area = QTextEdit()

        self.chat_area.setReadOnly(
            True
        )

        self.chat_area.setFrameShape(
            QFrame.NoFrame
        )

        self.chat_area.setStyleSheet(
            """
            QTextEdit {
                background: transparent;
                border: none;
                padding: 10px;
            }
            """
        )

        self.chat_area.hide()

        main_layout.addWidget(
            self.chat_area,
            1
        )

        # ====================================================
        # INPUT
        # ====================================================

        input_box = QFrame()

        input_box.setObjectName(
            "inputBox"
        )

        input_layout = QHBoxLayout(
            input_box
        )

        input_layout.setContentsMargins(
            13,
            8,
            8,
            8
        )

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Ask Orsearch anything..."
        )

        self.input.returnPressed.connect(
            self.send_message
        )

        input_layout.addWidget(
            self.input
        )

        self.send_button = QPushButton(
            "➤"
        )

        self.send_button.setObjectName(
            "send"
        )

        self.send_button.setFixedSize(
            42,
            38
        )

        self.send_button.clicked.connect(
            self.send_message
        )

        input_layout.addWidget(
            self.send_button
        )

        main_layout.addWidget(
            input_box
        )

        # Footer

        footer = QLabel(
            "Orsearch"
        )

        footer.setAlignment(
            Qt.AlignCenter
        )

        footer.setStyleSheet(
            """
            QLabel {
                color: #444449;
                font-size: 10px;
            }
            """
        )

        main_layout.addWidget(
            footer
        )


    # ========================================================
    # NEW CHAT
    # ========================================================

    def new_chat(self):

        chat_id = str(
            uuid.uuid4()
        )

        self.chats[chat_id] = {
            "title": "New Chat",
            "messages": []
        }

        self.current_chat = chat_id

        item = QListWidgetItem(
            "New Chat"
        )

        item.setData(
            Qt.UserRole,
            chat_id
        )

        self.chat_list.insertItem(
            0,
            item
        )

        self.chat_list.setCurrentItem(
            item
        )

        self.show_welcome()

        self.input.clear()

        self.input.setFocus()


    # ========================================================
    # SWITCH CHAT
    # ========================================================

    def switch_chat(self, item):

        chat_id = item.data(
            Qt.UserRole
        )

        if chat_id not in self.chats:
            return

        self.current_chat = chat_id

        messages = self.chats[
            chat_id
        ]["messages"]

        if not messages:

            self.show_welcome()

            return

        self.welcome.hide()

        self.chat_area.show()

        self.chat_area.clear()

        for message in messages:

            self.add_message_to_view(
                message["text"],
                message["user"]
            )


    # ========================================================
    # SHOW WELCOME
    # ========================================================

    def show_welcome(self):

        self.chat_area.clear()

        self.chat_area.hide()

        self.welcome.show()

        self.status.setText(
            "●  Orsearch ready"
        )


    # ========================================================
    # SET INPUT
    # ========================================================

    def set_input(self, text):

        self.input.setText(
            text
        )

        self.input.setFocus()


    # ========================================================
    # SEND MESSAGE
    # ========================================================

    def send_message(self):

        text = self.input.text().strip()

        if not text:
            return

        if not self.current_chat:
            self.new_chat()

        chat = self.chats[
            self.current_chat
        ]

        # First message becomes chat title

        if len(chat["messages"]) == 0:

            title = text[:28]

            if len(text) > 28:
                title += "..."

            chat["title"] = title

            item = self.chat_list.currentItem()

            if item:
                item.setText(
                    title
                )

        # Save message

        chat["messages"].append(
            {
                "text": text,
                "user": True
            }
        )

        self.welcome.hide()

        self.chat_area.show()

        self.add_message_to_view(
            text,
            True
        )

        self.input.clear()

        self.status.setText(
            "●  Thinking..."
        )

        # Simulated response for now

        QTimer.singleShot(
            700,
            lambda:
            self.ai_response(text)
        )


    # ========================================================
    # AI RESPONSE
    # ========================================================

    def ai_response(self, text):

        if self.current_chat not in self.chats:
            return

        response = self.generate_response(
            text
        )

        self.chats[
            self.current_chat
        ]["messages"].append(
            {
                "text": response,
                "user": False
            }
        )

        self.add_message_to_view(
            response,
            False
        )

        self.status.setText(
            "●  Orsearch ready"
        )


    # ========================================================
    # SIMPLE RESPONSE
    # ========================================================

    def generate_response(self, text):

        command = text.lower().strip()

        if command in [
            "hello",
            "hi",
            "hey",
            "hello orsearch",
            "hi orsearch"
        ]:

            return (
                "Hello! 👋\n\n"
                "I'm Orsearch. What would you "
                "like me to do?"
            )

        if "how are you" in command:

            return (
                "I'm ready to help. 🚀\n\n"
                "Give me a task and I'll get started."
            )

        if "chrome" in command:

            return (
                "Got it.\n\n"
                "I can open Chrome and perform "
                "the requested browser task."
            )

        if "notepad" in command:

            return (
                "Got it.\n\n"
                "I can open Notepad and type "
                "the requested text."
            )

        if "screenshot" in command:

            return (
                "Screenshot task received.\n\n"
                "The computer-control system can "
                "capture and analyze your screen."
            )

        return (
            "I received your request:\n\n"
            f"“{text}”\n\n"
            "I'm ready to execute this through "
            "the Orsearch computer agent."
        )


    # ========================================================
    # ADD MESSAGE
    # ========================================================

    def add_message_to_view(
        self,
        text,
        user
    ):

        html = (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )

        if user:

            block = f"""
            <div style="
                margin: 12px 5px;
                padding: 13px 16px;
                background: #19191e;
                border: 1px solid #29292f;
                border-radius: 15px;
            ">
                <span style="
                    color: #f5f5f5;
                    font-size: 14px;
                ">
                    {html}
                </span>
            </div>
            """

        else:

            block = f"""
            <div style="
                margin: 12px 5px;
                padding: 12px 5px;
            ">
                <span style="
                    color: #d4d4d8;
                    font-size: 14px;
                ">
                    <b style="
                        color: #ff4545;
                        font-size: 16px;
                    ">S</b>
                    &nbsp;&nbsp;
                    {html}
                </span>
            </div>
            """

        self.chat_area.insertHtml(
            block
        )

        self.chat_area.insertPlainText(
            "\n"
        )

        scrollbar = (
            self.chat_area
            .verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )


# ============================================================
# START APPLICATION
# ============================================================

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