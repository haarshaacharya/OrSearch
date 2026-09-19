import sys
import os
import html

from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QFrame,
    QMessageBox,
    QInputDialog,
    QSizePolicy,
)

ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from agent import run_agent


# =========================================================
# COLORS
# =========================================================

BLACK = "#050505"
SIDEBAR = "#0A0A0A"
PANEL = "#0E0E0E"
CARD = "#121212"
CARD_HOVER = "#191919"
BORDER = "#242424"

WHITE = "#FFFFFF"
TEXT = "#E8E8E8"
MUTED = "#777777"

GREEN = "#00FF88"
GREEN_DARK = "#00C96B"
GREEN_SOFT = "#73FFB2"


# =========================================================
# AGENT THREAD
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
# ORSEARCH CORE
# =========================================================

class OrsearchCore(QWidget):

    def __init__(self, size=110, parent=None):
        super().__init__(parent)

        self.size = size
        self.angle = 0

        self.setFixedSize(size, size)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    def animate(self):
        self.angle = (self.angle + 2) % 360
        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        s = self.size

        for width, alpha in [
            (16, 12),
            (11, 22),
            (7, 35),
        ]:

            pen = QPen(
                QColor(0, 255, 136, alpha)
            )

            pen.setWidth(width)
            painter.setPen(pen)

            painter.drawEllipse(
                width // 2,
                width // 2,
                s - width,
                s - width
            )

        pen = QPen(
            QColor(GREEN)
        )

        pen.setWidth(2)
        painter.setPen(pen)

        painter.drawEllipse(
            10,
            10,
            s - 20,
            s - 20
        )

        pen = QPen(
            QColor(WHITE)
        )

        pen.setWidth(3)
        painter.setPen(pen)

        painter.drawArc(
            14,
            14,
            s - 28,
            s - 28,
            self.angle * 16,
            85 * 16
        )

        painter.setPen(
            QColor(WHITE)
        )

        font = QFont(
            "Segoe UI",
            max(12, int(s * 0.40))
        )

        font.setBold(True)
        painter.setFont(font)

        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "S"
        )


# =========================================================
# CHAT ITEM
# =========================================================

class ChatItem(QWidget):

    def __init__(
        self,
        chat_id,
        title,
        pinned,
        select_callback,
        rename_callback,
        pin_callback,
        delete_callback,
    ):

        super().__init__()

        self.chat_id = chat_id

        self.layout = QHBoxLayout(self)

        self.layout.setContentsMargins(
            8,
            3,
            5,
            3
        )

        self.layout.setSpacing(2)

        self.chat_button = QPushButton(
            title
        )

        self.chat_button.setCursor(
            Qt.PointingHandCursor
        )

        self.chat_button.setMinimumHeight(
            38
        )

        self.chat_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        self.chat_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT};
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 0 8px;
                font-size: 13px;
            }}

            QPushButton:hover {{
                background: {CARD_HOVER};
                color: {WHITE};
            }}
        """)

        self.chat_button.clicked.connect(
            lambda: select_callback(
                self.chat_id
            )
        )

        self.rename_button = QPushButton("✎")
        self.rename_button.setFixedSize(
            28,
            34
        )

        self.pin_button = QPushButton(
            "●" if pinned else "○"
        )

        self.pin_button.setFixedSize(
            28,
            34
        )

        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(
            28,
            34
        )

        normal_style = f"""
            QPushButton {{
                background: transparent;
                color: {MUTED};
                border: none;
                border-radius: 7px;
                font-size: 14px;
            }}

            QPushButton:hover {{
                background: {CARD_HOVER};
                color: {WHITE};
            }}
        """

        self.rename_button.setStyleSheet(
            normal_style
        )

        self.delete_button.setStyleSheet(
            normal_style
        )

        self.pin_button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {GREEN if pinned else MUTED};
                border: none;
                border-radius: 7px;
                font-size: 11px;
            }}

            QPushButton:hover {{
                background: {CARD_HOVER};
                color: {GREEN};
            }}
        """)

        self.rename_button.clicked.connect(
            lambda: rename_callback(
                self.chat_id
            )
        )

        self.pin_button.clicked.connect(
            lambda: pin_callback(
                self.chat_id
            )
        )

        self.delete_button.clicked.connect(
            lambda: delete_callback(
                self.chat_id
            )
        )

        self.layout.addWidget(
            self.chat_button,
            1
        )

        self.layout.addWidget(
            self.rename_button
        )

        self.layout.addWidget(
            self.pin_button
        )

        self.layout.addWidget(
            self.delete_button
        )

        self.setStyleSheet(f"""
            ChatItem {{
                background: transparent;
                border-radius: 9px;
            }}

            ChatItem:hover {{
                background: {CARD};
            }}
        """)


# =========================================================
# MAIN WINDOW
# =========================================================

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
        self.chat_counter = 0
        self.worker = None

        self.build_ui()

        self.new_chat()


    # =====================================================
    # BUILD UI
    # =====================================================

    def build_ui(self):

        self.setStyleSheet(f"""
            QMainWindow {{
                background: {BLACK};
            }}

            QWidget {{
                font-family: "Segoe UI";
            }}

            QLineEdit {{
                background: {CARD};
                color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 13px;
                padding: 13px 15px;
                font-size: 14px;
            }}

            QLineEdit:focus {{
                border: 1px solid {GREEN_DARK};
            }}

            QScrollBar:vertical {{
                background: {BLACK};
                width: 7px;
            }}

            QScrollBar::handle:vertical {{
                background: #292929;
                border-radius: 4px;
            }}
        """)

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QHBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        main_layout.setSpacing(0)


        # =================================================
        # SIDEBAR
        # =================================================

        sidebar = QFrame()

        sidebar.setFixedWidth(
            285
        )

        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {SIDEBAR};
                border-right: 1px solid {BORDER};
            }}
        """)

        sidebar_layout = QVBoxLayout(
            sidebar
        )

        sidebar_layout.setContentsMargins(
            16,
            18,
            16,
            16
        )

        sidebar_layout.setSpacing(
            12
        )


        # LOGO

        logo_layout = QHBoxLayout()

        logo_layout.setSpacing(
            10
        )

        logo_core = OrsearchCore(
            43
        )

        logo_text = QLabel(
            "Orsearch"
        )

        logo_text.setStyleSheet(f"""
            QLabel {{
                color: {WHITE};
                font-size: 21px;
                font-weight: 700;
            }}
        """)

        logo_layout.addWidget(
            logo_core
        )

        logo_layout.addWidget(
            logo_text
        )

        logo_layout.addStretch()

        sidebar_layout.addLayout(
            logo_layout
        )


        # NEW CHAT

        self.new_chat_button = QPushButton(
            "+  New Chat"
        )

        self.new_chat_button.setFixedHeight(
            44
        )

        self.new_chat_button.setCursor(
            Qt.PointingHandCursor
        )

        self.new_chat_button.setStyleSheet(f"""
            QPushButton {{
                background: {CARD};
                color: {WHITE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                text-align: left;
                padding-left: 15px;
                font-size: 13px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {CARD_HOVER};
                border: 1px solid {GREEN_DARK};
                color: {GREEN_SOFT};
            }}
        """)

        self.new_chat_button.clicked.connect(
            self.new_chat
        )

        sidebar_layout.addWidget(
            self.new_chat_button
        )


        # YOUR CHATS

        chats_label = QLabel(
            "YOUR CHATS"
        )

        chats_label.setStyleSheet(f"""
            QLabel {{
                color: #686868;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 1px;
                padding: 5px 3px;
            }}
        """)

        sidebar_layout.addWidget(
            chats_label
        )


        # CHAT CONTAINER
        #
        # Important:
        # Simple QWidget + QVBoxLayout
        # No QListWidget/custom item problem.

        self.chat_container = QWidget()

        self.chat_container.setStyleSheet(
            f"""
            QWidget {{
                background: transparent;
            }}
            """
        )

        self.chat_layout = QVBoxLayout(
            self.chat_container
        )

        self.chat_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.chat_layout.setSpacing(
            3
        )

        self.chat_layout.setAlignment(
            Qt.AlignTop
        )

        sidebar_layout.addWidget(
            self.chat_container,
            1
        )


        # STATUS

        sidebar_status = QLabel(
            "●  SYSTEM READY"
        )

        sidebar_status.setStyleSheet(f"""
            QLabel {{
                color: {MUTED};
                font-size: 10px;
                padding: 5px;
            }}
        """)

        sidebar_layout.addWidget(
            sidebar_status
        )


        # =================================================
        # MAIN CONTENT
        # =================================================

        content = QFrame()

        content.setStyleSheet(f"""
            QFrame {{
                background: {BLACK};
            }}
        """)

        content_layout = QVBoxLayout(
            content
        )

        content_layout.setContentsMargins(
            30,
            22,
            30,
            24
        )

        content_layout.setSpacing(
            12
        )


        # HEADER

        header = QHBoxLayout()

        self.page_title = QLabel(
            "Orsearch"
        )

        self.page_title.setStyleSheet(f"""
            QLabel {{
                color: {WHITE};
                font-size: 18px;
                font-weight: 700;
            }}
        """)

        self.status_label = QLabel(
            "READY"
        )

        header.addWidget(
            self.page_title
        )

        header.addSpacing(
            10
        )

        header.addWidget(
            self.status_label
        )

        header.addStretch()

        content_layout.addLayout(
            header
        )


        # WELCOME

        self.welcome = QWidget()

        welcome_layout = QVBoxLayout(
            self.welcome
        )

        welcome_layout.setAlignment(
            Qt.AlignCenter
        )

        welcome_layout.setSpacing(
            5
        )

        core = OrsearchCore(
            125
        )

        welcome_title = QLabel(
            "What can I do for you?"
        )

        welcome_title.setAlignment(
            Qt.AlignCenter
        )

        welcome_title.setStyleSheet(f"""
            QLabel {{
                color: {WHITE};
                font-size: 25px;
                font-weight: 600;
                margin-top: 8px;
            }}
        """)

        welcome_subtitle = QLabel(
            "Search the web, control your computer, or execute tasks."
        )

        welcome_subtitle.setAlignment(
            Qt.AlignCenter
        )

        welcome_subtitle.setStyleSheet(f"""
            QLabel {{
                color: {MUTED};
                font-size: 13px;
            }}
        """)

        welcome_layout.addWidget(
            core
        )

        welcome_layout.addWidget(
            welcome_title
        )

        welcome_layout.addWidget(
            welcome_subtitle
        )

        content_layout.addWidget(
            self.welcome
        )


        # CHAT VIEW

        self.chat_view = QTextEdit()

        self.chat_view.setReadOnly(
            True
        )

        self.chat_view.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {TEXT};
                border: none;
                padding: 8px;
                font-size: 14px;
            }}
        """)

        content_layout.addWidget(
            self.chat_view,
            1
        )


        # QUICK ACTIONS

        quick_layout = QHBoxLayout()

        quick_layout.setSpacing(
            8
        )

        self.add_quick_button(
            quick_layout,
            "Open Chrome",
            "Open Chrome"
        )

        self.add_quick_button(
            quick_layout,
            "Search Web",
            "Search Google for "
        )

        self.add_quick_button(
            quick_layout,
            "Open Notepad",
            "Open Notepad"
        )

        self.add_quick_button(
            quick_layout,
            "Screenshot",
            "Take a screenshot"
        )

        quick_layout.addStretch()

        content_layout.addLayout(
            quick_layout
        )


        # INPUT

        input_layout = QHBoxLayout()

        input_layout.setSpacing(
            8
        )

        self.input = QLineEdit()

        self.input.setPlaceholderText(
            "Message Orsearch..."
        )

        self.input.returnPressed.connect(
            self.send_message
        )

        self.send_button = QPushButton(
            "➤"
        )

        self.send_button.setFixedSize(
            51,
            48
        )

        self.send_button.setCursor(
            Qt.PointingHandCursor
        )

        self.send_button.setStyleSheet(f"""
            QPushButton {{
                background: {GREEN};
                color: #00170B;
                border: none;
                border-radius: 12px;
                font-size: 20px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: {GREEN_SOFT};
            }}

            QPushButton:pressed {{
                background: {GREEN_DARK};
            }}
        """)

        self.send_button.clicked.connect(
            self.send_message
        )

        input_layout.addWidget(
            self.input,
            1
        )

        input_layout.addWidget(
            self.send_button
        )

        content_layout.addLayout(
            input_layout
        )


        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            content
        )

        self.set_status(
            "READY"
        )


    # =====================================================
    # QUICK BUTTON
    # =====================================================

    def add_quick_button(
        self,
        layout,
        title,
        command
    ):

        button = QPushButton(
            title
        )

        button.setFixedHeight(
            32
        )

        button.setCursor(
            Qt.PointingHandCursor
        )

        button.setStyleSheet(f"""
            QPushButton {{
                background: {PANEL};
                color: #999999;
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 0 12px;
                font-size: 11px;
            }}

            QPushButton:hover {{
                color: {WHITE};
                border: 1px solid {GREEN_DARK};
            }}
        """)

        button.clicked.connect(
            lambda: self.set_input(command)
        )

        layout.addWidget(
            button
        )


    # =====================================================
    # STATUS
    # =====================================================

    def set_status(
        self,
        status
    ):

        self.status_label.setText(
            status
        )

        if status == "READY":

            color = MUTED
            bg = PANEL
            border = BORDER

        elif status in [
            "THINKING",
            "EXECUTING"
        ]:

            color = GREEN_SOFT
            bg = "#0B1C13"
            border = "#174D32"

        elif status == "DONE":

            color = GREEN
            bg = "#0B2116"
            border = "#174D32"

        else:

            color = WHITE
            bg = "#1C1C1C"
            border = "#333333"

        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background: {bg};
                border: 1px solid {border};
                border-radius: 7px;
                padding: 5px 9px;
                font-size: 9px;
                font-weight: 700;
            }}
        """)


    # =====================================================
    # CHAT LIST
    # =====================================================

    def rebuild_chat_list(self):

        while self.chat_layout.count():

            item = self.chat_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

        sorted_chats = sorted(
            self.chats.items(),
            key=lambda item: (
                not item[1]["pinned"],
                item[0]
            )
        )

        for chat_id, chat in sorted_chats:

            row = ChatItem(
                chat_id=chat_id,
                title=chat["title"],
                pinned=chat["pinned"],
                select_callback=self.select_chat,
                rename_callback=self.rename_chat,
                pin_callback=self.toggle_pin,
                delete_callback=self.delete_chat,
            )

            if chat_id == self.current_chat:

                row.chat_button.setStyleSheet(f"""
                    QPushButton {{
                        background: #13241B;
                        color: {GREEN_SOFT};
                        border: 1px solid #1A4931;
                        border-radius: 8px;
                        text-align: left;
                        padding: 0 8px;
                        font-size: 13px;
                        font-weight: 600;
                    }}
                """)

            self.chat_layout.addWidget(
                row
            )


    # =====================================================
    # NEW CHAT
    # =====================================================

    def new_chat(self):

        self.chat_counter += 1

        chat_id = (
            f"chat_{self.chat_counter}"
        )

        self.chats[chat_id] = {
            "title": f"New Chat {self.chat_counter}",
            "pinned": False,
            "messages": []
        }

        self.current_chat = chat_id

        self.rebuild_chat_list()

        self.show_chat()

        self.input.setFocus()


    # =====================================================
    # SELECT CHAT
    # =====================================================

    def select_chat(
        self,
        chat_id
    ):

        if chat_id not in self.chats:
            return

        self.current_chat = chat_id

        self.rebuild_chat_list()

        self.show_chat()


    # =====================================================
    # SHOW CHAT
    # =====================================================

    def show_chat(self):

        if not self.current_chat:
            return

        chat = self.chats[
            self.current_chat
        ]

        self.page_title.setText(
            chat["title"]
        )

        self.chat_view.clear()

        if not chat["messages"]:

            self.chat_view.hide()

            self.welcome.show()

            return

        self.welcome.hide()

        self.chat_view.show()

        for message in chat["messages"]:

            self.render_message(
                message["role"],
                message["text"]
            )


    # =====================================================
    # RENDER MESSAGE
    # =====================================================

    def render_message(
        self,
        role,
        text
    ):

        safe = html.escape(
            str(text)
        ).replace(
            "\n",
            "<br>"
        )

        if role == "user":

            content = f"""
            <div style="
                margin: 12px 5px;
                padding: 14px 16px;
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 13px;
            ">

                <div style="
                    color: {GREEN};
                    font-size: 10px;
                    font-weight: 700;
                    margin-bottom: 6px;
                ">
                    YOU
                </div>

                <div style="
                    color: {TEXT};
                    font-size: 14px;
                ">
                    {safe}
                </div>

            </div>
            """

        elif role == "system":

            content = f"""
            <div style="
                margin: 10px 8px;
                color: {MUTED};
                font-size: 11px;
            ">
                {safe}
            </div>
            """

        else:

            content = f"""
            <div style="
                margin: 12px 5px;
                padding: 14px 16px;
                background: {PANEL};
                border: 1px solid {BORDER};
                border-left: 2px solid {GREEN};
                border-radius: 13px;
            ">

                <div style="
                    color: {WHITE};
                    font-size: 10px;
                    font-weight: 700;
                    margin-bottom: 6px;
                ">
                    ORSEARCH
                </div>

                <div style="
                    color: #D7D7D7;
                    font-size: 14px;
                    line-height: 1.6;
                ">
                    {safe}
                </div>

            </div>
            """

        self.chat_view.moveCursor(
            self.chat_view.textCursor().End
        )

        self.chat_view.insertHtml(
            content
        )

        self.chat_view.insertPlainText(
            "\n"
        )

        self.chat_view.verticalScrollBar().setValue(
            self.chat_view.verticalScrollBar().maximum()
        )


    # =====================================================
    # INPUT
    # =====================================================

    def set_input(
        self,
        text
    ):

        self.input.setText(
            text
        )

        self.input.setFocus()

        self.input.setCursorPosition(
            len(text)
        )


    # =====================================================
    # SEND MESSAGE
    # =====================================================

    def send_message(self):

        text = self.input.text().strip()

        if not text:
            return

        if self.worker and self.worker.isRunning():
            return

        self.input.clear()

        self.welcome.hide()

        self.chat_view.show()

        self.chats[
            self.current_chat
        ]["messages"].append({
            "role": "user",
            "text": text
        })

        self.render_message(
            "user",
            text
        )

        self.set_status(
            "THINKING"
        )

        self.send_button.setDisabled(
            True
        )

        self.input.setDisabled(
            True
        )

        self.render_message(
            "system",
            "Orsearch is thinking..."
        )

        self.worker = AgentWorker(
            text
        )

        self.worker.finished.connect(
            self.agent_finished
        )

        self.worker.failed.connect(
            self.agent_failed
        )

        self.worker.start()


    # =====================================================
    # AGENT FINISHED
    # =====================================================

    def agent_finished(
        self,
        result
    ):

        self.remove_thinking()

        if isinstance(result, dict):

            message = result.get(
                "message",
                "Task completed."
            )

            success = result.get(
                "success",
                True
            )

        else:

            message = str(
                result
            )

            success = True

        if success:

            self.set_status(
                "DONE"
            )

        else:

            self.set_status(
                "FAILED"
            )

        self.chats[
            self.current_chat
        ]["messages"].append({
            "role": "assistant",
            "text": message
        })

        self.render_message(
            "assistant",
            message
        )

        self.send_button.setDisabled(
            False
        )

        self.input.setDisabled(
            False
        )

        self.input.setFocus()

        self.rebuild_chat_list()

        self.worker = None


    # =====================================================
    # AGENT ERROR
    # =====================================================

    def agent_failed(
        self,
        error
    ):

        self.remove_thinking()

        self.set_status(
            "ERROR"
        )

        message = (
            f"Agent error: {error}"
        )

        self.chats[
            self.current_chat
        ]["messages"].append({
            "role": "assistant",
            "text": message
        })

        self.render_message(
            "assistant",
            message
        )

        self.send_button.setDisabled(
            False
        )

        self.input.setDisabled(
            False
        )

        self.input.setFocus()

        self.worker = None


    # =====================================================
    # REMOVE THINKING
    # =====================================================

    def remove_thinking(self):

        cursor = self.chat_view.textCursor()

        cursor.movePosition(
            cursor.End
        )

        cursor.select(
            cursor.BlockUnderCursor
        )

        if "Orsearch is thinking..." in cursor.selectedText():

            cursor.removeSelectedText()

            cursor.deletePreviousChar()

        self.chat_view.setTextCursor(
            cursor
        )


    # =====================================================
    # RENAME CHAT
    # =====================================================

    def rename_chat(
        self,
        chat_id
    ):

        if chat_id not in self.chats:
            return

        old_title = self.chats[
            chat_id
        ]["title"]

        title, ok = QInputDialog.getText(
            self,
            "Rename Chat",
            "Chat name:",
            text=old_title
        )

        if ok and title.strip():

            self.chats[
                chat_id
            ]["title"] = title.strip()

            self.rebuild_chat_list()

            if chat_id == self.current_chat:

                self.page_title.setText(
                    title.strip()
                )


    # =====================================================
    # PIN CHAT
    # =====================================================

    def toggle_pin(
        self,
        chat_id
    ):

        if chat_id not in self.chats:
            return

        self.chats[
            chat_id
        ]["pinned"] = not self.chats[
            chat_id
        ]["pinned"]

        self.rebuild_chat_list()


    # =====================================================
    # DELETE CHAT
    # =====================================================

    def delete_chat(
        self,
        chat_id
    ):

        if chat_id not in self.chats:
            return

        if len(self.chats) == 1:

            QMessageBox.information(
                self,
                "Delete Chat",
                "At least one chat must remain."
            )

            return

        answer = QMessageBox.question(
            self,
            "Delete Chat",
            "Delete this conversation?",
            QMessageBox.Yes |
            QMessageBox.No
        )

        if answer != QMessageBox.Yes:
            return

        del self.chats[
            chat_id
        ]

        if self.current_chat == chat_id:

            self.current_chat = next(
                iter(self.chats)
            )

        self.rebuild_chat_list()

        self.show_chat()


# =========================================================
# START
# =========================================================

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