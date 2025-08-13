import re
import os
from typing import Dict

def extract_json(text):
    """Extract the first JSON object substring from a string."""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
    except Exception:
        pass
    return text

def save_error(error_message: str, error_file: str = None):
    """
    Save error messages to a log file for debugging.
    """
    if error_file is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        error_file = os.path.join(project_root, "Data", "error.txt")
    
    try:
        os.makedirs(os.path.dirname(error_file), exist_ok=True)
        
        with open(error_file, 'a', encoding='utf-8') as f:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {error_message}\n")
    except Exception as e:
        print(f"Failed to save error: {e}")
