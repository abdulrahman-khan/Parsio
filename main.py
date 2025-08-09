import os
import sys
from PyQt5.QtWidgets import QApplication
from ui import ParsioApp

def ensure_env_file():
    env_path = ".env"
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write('GEMINI_API_KEY = ""\n')

def main():
    ensure_env_file()
    app = QApplication(sys.argv)
    window = ParsioApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
