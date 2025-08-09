from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit
from PyQt5.QtGui import QGuiApplication
from parser import parse_with_gemini
from PyQt5.QtGui import QIcon
import os
from data_manager import save_to_excel 

class ParsioApp(QWidget):
    def __init__(self):
        super().__init__()
        
        icon_path = os.path.join(os.path.dirname(__file__), "images/icon.png") 
        self.setWindowIcon(QIcon(icon_path))

        
        self.pending_changes = []  # List of dicts
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Parsio")
        self.resize(800, 400)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # Left Info Board (log)
        self.log_board = QTextEdit()
        self.log_board.setReadOnly(True)
        layout.addWidget(self.log_board, stretch=2)

        # Right Sidebar with buttons
        right_panel = QVBoxLayout()

        btn_paste = QPushButton("Click Here To Paste")
        btn_paste.clicked.connect(self.handle_paste)
        right_panel.addWidget(btn_paste)

        btn_commit = QPushButton("Commit Changes")
        btn_commit.clicked.connect(self.commit_changes)
        right_panel.addWidget(btn_commit)

        layout.addLayout(right_panel, stretch=1)
        
        self.apply_styles()

# end of init ui ==========================
        
        

    def handle_paste(self):
        clipboard_text = QGuiApplication.clipboard().text().strip()
        if not clipboard_text:
            self.log("Clipboard is empty.")
            return

        # Use URL or raw text directly
        if clipboard_text.lower().startswith("http"):
            from data_manager import fetch_url_content
            content = fetch_url_content(clipboard_text)
        else:
            content = clipboard_text

        if content:
            parsed_data = parse_with_gemini(content)
            if parsed_data:
                self.pending_changes.append(parsed_data)
                self.log(f"Pending Add: {parsed_data}")
            else:
                self.log("Gemini parsing failed. See error.txt for details.")

    def commit_changes(self):
        if not self.pending_changes:
            self.log("No changes to commit.")
            return

        try:
            save_to_excel(self.pending_changes)
            self.log(f"Committed {len(self.pending_changes)} changes to Excel.")
            self.pending_changes.clear()
        except Exception as e:
            self.log(f"Error saving to Excel: {e}")

    def log(self, message):
        self.log_board.append(message)
        
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0B1D51;  /* dark blue */
                color: black;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #D6D9E0;  /* light gray/blue */
                color: black;
                border: 1px solid #324A80;  /* medium dark blue border */
                border-radius: 5px;
            }
            QPushButton {
                background-color: #081B40;  /* darker blue */
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1A2E6B;  /* lighter blue on hover */
            }
            QPushButton:pressed {
                background-color: #050E2A;  /* darkest blue on press */
            }
        """)


