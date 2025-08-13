from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QGuiApplication
from interface import Ui_ParsioApp
from parser import parse_with_gemini
from database_context import fetch_url_content, db
import sys
import os


class ParsioApp(QMainWindow):
    def __init__(self):
        # Check for env file
        env_path = ".env"
        if not os.path.exists(env_path):
            with open(env_path, "w") as f:
                f.write('GEMINI_API_KEY = ""\n')

        super().__init__()
        
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

        # URL OR RAW TEXT %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
        if clipboard_text.lower().startswith("http"):
            content = fetch_url_content(clipboard_text)
        else:
            content = clipboard_text

        if content:
            parsed_data = parse_with_gemini(content)
            if parsed_data:
                self.pending_changes.append(parsed_data)
                self.log(f"Added to pending: {parsed_data['job_title']} at {parsed_data['company']}")
            else:
                # TODO: Improve error handling
                self.log("Unable to parse job posting. Check error.txt for details.")

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