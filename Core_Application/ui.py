from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QGuiApplication, QIcon
from interface import Ui_ParsioApp
from parser import parse_with_gemini
from database_context import fetch_url_content, db
import sys
import os


class ParsioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # icon_path = os.path.join(os.path.dirname(__file__), "..", "Data", "icon2.png")
        # self.setWindowIcon(QIcon(icon_path))
        
        self.ui = Ui_ParsioApp()
        self.ui.setupUi(self)
        
        self.pending_changes = []  # List of job postings to save
        
        # button events
        self.connect_signals()

    def connect_signals(self):
        self.ui.btn_paste.clicked.connect(self.handle_paste)
        self.ui.btn_commit.clicked.connect(self.commit_changes)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionClear_Log.triggered.connect(self.clear_log)

    def handle_paste(self):
        """Handles paste button event"""
        clipboard_text = QGuiApplication.clipboard().text().strip()
        if not clipboard_text:
            self.log("Clipboard is empty.")
            return

        # Check if API key is configured
        api_key = db.get_gemini_api_key()
        if not api_key:
            self.log("Error: Gemini API key not configured. Please set your API key in the settings.")
            return

        # URL OR RAW TEXT %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if clipboard_text.lower().startswith("http"):
            content = fetch_url_content(clipboard_text)
        else:
            content = clipboard_text

        if content:
            try:
                parsed_data = parse_with_gemini(content, api_key)
                if parsed_data:
                    self.pending_changes.append(parsed_data)
                    self.log(f"Added to pending: {parsed_data['job_title']} at {parsed_data['company']}")
                else:
                    self.log("Unable to parse job posting. Check error.txt for details.")
            except ValueError as e:
                self.log(f"API Key Error: {e}")
            except Exception as e:
                self.log(f"Parsing Error: {e}")

    def commit_changes(self):
        """Save pending changes to database"""
        if not self.pending_changes:
            self.log("No changes to commit.")
            return

        try:
            self.log(f"Saving {len(self.pending_changes)} job postings...")
            
            success = db.save_job_postings(self.pending_changes)
            if success:
                self.log(f"Successfully saved {len(self.pending_changes)} job postings!")
                self.pending_changes.clear()
                self.show_database_stats()
            else:
                self.log("Failed to save to database.")
                
        except Exception as e:
            self.log(f"Error: {e}")

    def log(self, message):
        """Add message to log board"""
        self.ui.log_board.append(message)
    
    def clear_log(self):
        """Clear the log board"""
        self.ui.log_board.clear()
        self.log("Log cleared.")

    def show_database_stats(self):
        """Show basic database statistics"""
        try:
            stats = db.get_database_stats(3)  
            for line in stats.split('\n'):
                if line.strip():  
                    self.log(line)
        except Exception as e:
            self.log(f"Could not get stats: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParsioApp()
    window.show()
    sys.exit(app.exec_())