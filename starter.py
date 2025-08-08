import os
import sys
import json
import pandas as pd
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit
from PyQt5.QtGui import QGuiApplication

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

EXCEL_FILE = "job_postings.xlsx"

class ParsioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.pending_changes = []  # List of dicts
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Parsio")
        self.resize(800, 400)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # Left Info Board
        self.log_board = QTextEdit()
        self.log_board.setReadOnly(True)
        layout.addWidget(self.log_board, stretch=2)

        # Right Sidebar
        right_panel = QVBoxLayout()

        btn_paste = QPushButton("Click Here To Paste")
        btn_paste.clicked.connect(self.handle_paste)
        right_panel.addWidget(btn_paste)

        btn_commit = QPushButton("Commit Changes")
        btn_commit.clicked.connect(self.commit_changes)
        right_panel.addWidget(btn_commit)

        layout.addLayout(right_panel, stretch=1)

    def handle_paste(self):
        clipboard_text = QGuiApplication.clipboard().text().strip()
        if not clipboard_text:
            self.log("Clipboard is empty.")
            return

        if clipboard_text.lower().startswith("http"):
            content = self.fetch_url_content(clipboard_text)
            original_source = clipboard_text
        else:
            content = clipboard_text
            original_source = clipboard_text[:200] + "..." if len(clipboard_text) > 200 else clipboard_text

        if content:
            parsed_data = self.parse_with_gemini(content, original_source)
            if parsed_data:
                self.pending_changes.append(parsed_data)
                self.log(f"Pending Add: {parsed_data}")
            else:
                self.log("Gemini parsing failed.")

    def fetch_url_content(self, url):
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except Exception as e:
            self.log(f"Error fetching URL: {e}")
            return None

    def parse_with_gemini(self, text, original_source):
        try:
            prompt = (
                "Extract the following fields from the job posting text below: "
                "job_title, company, location, salary, description. "
                "ALWAYS return a valid JSON object with these exact keys: "
                '{"job_title": "", "company": "", "location": "", "salary": "", "description": "", "original_source": ""}. '
                "Fill 'original_source' with the original URL or pasted text. "
                "Do not include any text outside of the JSON object.\n\n"
                f"Job Posting:\n{text}\n\n"
                f"Original Source: {original_source}"
            )

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)

            raw_output = response.candidates[0].content.parts[0].text.strip()

            # Try parsing as JSON
            parsed_data = json.loads(raw_output)

            # Ensure all fields exist
            required_fields = ["job_title", "company", "location", "salary", "description", "original_source"]
            for field in required_fields:
                if field not in parsed_data:
                    parsed_data[field] = ""

            return parsed_data

        except json.JSONDecodeError:
            self.log(f"Gemini returned invalid JSON: {raw_output}")
            return None
        except Exception as e:
            self.log(f"Gemini error: {e}")
            return None

    def commit_changes(self):
        if not self.pending_changes:
            self.log("No changes to commit.")
            return
        try:
            df_new = pd.DataFrame(self.pending_changes)

            # Ensure consistent column order
            cols = ["job_title", "company", "location", "salary", "description", "original_source"]
            df_new = df_new[cols]

            try:
                df_existing = pd.read_excel(EXCEL_FILE)
                df_existing = df_existing[cols]  # match column order
                df_final = pd.concat([df_existing, df_new], ignore_index=True)
            except FileNotFoundError:
                df_final = df_new

            df_final.to_excel(EXCEL_FILE, index=False)
            self.log(f"Committed {len(self.pending_changes)} changes to Excel.")
            self.pending_changes.clear()
        except Exception as e:
            self.log(f"Error saving to Excel: {e}")

    def log(self, message):
        self.log_board.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ParsioApp()
    window.show()
    sys.exit(app.exec_())
