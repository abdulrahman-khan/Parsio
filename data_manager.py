import os
import pandas as pd
import requests
from bs4 import BeautifulSoup

EXCEL_FILE = "job_postings.xlsx"
ERROR_FILE = "error.txt"

def fetch_url_content(url):
    """
    Fetch the webpage content and return the visible text.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        # Since this is called from UI, log messages should be handled there
        return None

def save_to_excel(data_list):
    """
    Save a list of dicts to the Excel file, appending if the file exists.
    Ensures consistent column order.
    """
    cols = ["job_title", "company", "location", "salary"]

    df_new = pd.DataFrame(data_list)[cols]

    try:
        df_existing = pd.read_excel(EXCEL_FILE)
        df_existing = df_existing[cols]  # match column order
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    except FileNotFoundError:
        df_final = df_new

    df_final.to_excel(EXCEL_FILE, index=False)

def save_error(content):
    """
    Append error content to error.txt for manual review.
    """
    try:
        with open(ERROR_FILE, "a", encoding="utf-8") as f:
            f.write("\n--- Gemini Output Error ---\n")
            f.write(content + "\n")
    except Exception:
        # If logging fails, ignore to avoid crashes
        pass
