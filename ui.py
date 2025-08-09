from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtCore import QCoreApplication
from interface import Ui_ParsioApp
from parser import parse_with_gemini
import os
from data_manager import save_to_excel, fetch_url_content
import sys


class ParsioApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize the UI from the auto-generated file
        self.ui = Ui_ParsioApp()
        self.ui.setupUi(self)
        
        self.pending_changes = []  # List of dicts
        
        # Connect button signals to custom methods
        self.connect_signals()

    def connect_signals(self):
        """Connect UI elements to custom logic"""
        # Connect buttons
        self.ui.btn_paste.clicked.connect(self.handle_paste)
        self.ui.btn_commit.clicked.connect(self.commit_changes)
        
        # Connect menu actions
        self.ui.actionNew.triggered.connect(self.new_file)
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave_As.triggered.connect(self.save_as_file)
        self.ui.actionExit.triggered.connect(self.close)
        
        self.ui.actionCut.triggered.connect(self.cut_text)
        self.ui.actionCopy.triggered.connect(self.copy_text)
        self.ui.actionPaste.triggered.connect(self.paste_text)
        self.ui.actionClear_Log.triggered.connect(self.clear_log)
        
        self.ui.actionRefresh.triggered.connect(self.refresh_view)
        self.ui.actionFull_Screen.triggered.connect(self.toggle_fullscreen)
        
        self.ui.actionSettings.triggered.connect(self.show_settings)
        self.ui.actionExport_Data.triggered.connect(self.export_data)
        self.ui.actionImport_Data.triggered.connect(self.import_data)
        
        self.ui.actionAbout.triggered.connect(self.show_about)
        self.ui.actionUser_Guide.triggered.connect(self.show_user_guide)

    def handle_paste(self):
        """Handle paste button click"""
        clipboard_text = QGuiApplication.clipboard().text().strip()
        if not clipboard_text:
            self.log("Clipboard is empty.")
            return

        # Use URL or raw text directly
        if clipboard_text.lower().startswith("http"):
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
        """Handle commit button click"""
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
        """Add message to log board"""
        self.ui.log_board.append(message)
    
    # Menu action handlers
    def new_file(self):
        """Handle New file action"""
        self.pending_changes.clear()
        self.clear_log()
        self.log("New session started.")

    def open_file(self):
        """Handle Open file action"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Excel files (*.xlsx);;All Files (*)")
        if file_path:
            self.log(f"Opening file: {file_path}")
            # Add your file opening logic here

    def save_file(self):
        """Handle Save file action"""
        if self.pending_changes:
            self.commit_changes()
        else:
            self.log("No changes to save.")

    def save_as_file(self):
        """Handle Save As action"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "Excel files (*.xlsx);;All Files (*)")
        if file_path:
            self.log(f"Saving to: {file_path}")
            # Add your save as logic here

    def cut_text(self):
        """Handle Cut action"""
        if self.ui.log_board.textCursor().hasSelection():
            self.ui.log_board.cut()

    def copy_text(self):
        """Handle Copy action"""
        if self.ui.log_board.textCursor().hasSelection():
            self.ui.log_board.copy()

    def paste_text(self):
        """Handle menu Paste action (different from paste button)"""
        self.handle_paste()

    def clear_log(self):
        """Handle Clear Log action"""
        self.ui.log_board.clear()
        self.log("Log cleared.")

    def refresh_view(self):
        """Handle Refresh action"""
        self.log("View refreshed.")

    def toggle_fullscreen(self):
        """Handle Full Screen action"""
        if self.isFullScreen():
            self.showNormal()
            self.log("Exited full screen mode.")
        else:
            self.showFullScreen()
            self.log("Entered full screen mode.")

    def show_settings(self):
        """Handle Settings action"""
        self.log("Settings dialog would open here.")
        # Add your settings dialog logic here

    def export_data(self):
        """Handle Export Data action"""
        if self.pending_changes:
            self.commit_changes()
        self.log("Data export completed.")

    def import_data(self):
        """Handle Import Data action"""
        from PyQt5.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Data", "", "Excel files (*.xlsx);;All Files (*)")
        if file_path:
            self.log(f"Importing data from: {file_path}")
            # Add your import logic here

    def show_about(self):
        """Handle About action"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "About Parsio", 
                         "Parsio - AI Job Application Tracker\n\n"
                         "Version 1.0\n"
                         "A tool for tracking job applications using AI parsing.")

    def show_user_guide(self):
        """Handle User Guide action"""
        self.log("User guide would open here.")
        # Add your user guide logic here


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParsioApp()
    window.show()
    sys.exit(app.exec_())