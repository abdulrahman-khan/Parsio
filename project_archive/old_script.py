"""
verion 1 - 2024-10-03
uses gemini api to parse job posting urls stored in a text file
stores parsed data onto a google sheet
"""


import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import time

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_RANGE = os.getenv("SHEET_RANGE")
CREDS_PATH = os.getenv("CREDS_PATH")
LINKS_FILE = os.getenv("LINKS_FILE")

# Function to get the next job link from the file and remove it from the list
def get_next_link():
    if not os.path.exists(LINKS_FILE):
        return None
    with open(LINKS_FILE, 'r') as f:
        links = f.readlines()
    if not links:
        return None
    next_link = links[0].strip()
    with open(LINKS_FILE, 'w') as f:
        f.writelines(links[1:])
    
    return next_link

# Function to call Gemini API with retry logic
def call_gemini(prompt, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429 and attempt < max_retries - 1:
                time.sleep(2 + attempt)
            else:
                raise

# parse job posting url
def process_job_posting(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    job_text = soup.get_text(separator=' ', strip=True)
    

    # gemini prompt
    prompt = f"""
    you are an information extractor AI. Your objective is to take this job posting text:
    
    -START OF JOB POSTING TEXT-
    {job_text}
    -END OF JOB POSTING TEXT-
    
    You will extract the following information:
    - Job Title
    - Company Name
    - Location
    - Industry (if mentioned, you can make an educated guess based on the contents of the job posting. Write only the industry you think it is and nothing else)
    - Required Experience Level (e.g., Entry, Mid, Senior) if not mentioned, write "Not mentioned"
    - Salary Range (if mentioned, write only the range in the format: $X - $Y, or $X /h) if not mentioned, write "Not mentioned"
    - The Job posting date if mentioned in the page in format YYYY-MM-DD, if not mentioned, write "Not mentioned"
    - Extract the main technical skills and tools required, separated by "-", ordered by Technical Skills, then Soft Skills. if not mentioned, write "Not mentioned"

    If you are unable to fill any of the fields, leave them blank with a simple "-"

    Capitalize the company name and job title. Do not include any extra text, headers, or explanations. Only output the CSV line.

    Return the output in json format - in the following order:
    Job Title: 
    Company Name:
    Location: 
    Industry: 
    Experience Level: 
    Salary Range: 
    Posted Date: 
    Skills: 

    """

    gemini_response = call_gemini(prompt)
    time.sleep(5) 
    extracted = gemini_response['candidates'][0]['content']['parts'][0]['text']

    print("\n" + "=============================================================================")
    print(f"Processing URL: {url}")


    # response
    import json
    if cleaned.startswith('```json'):
        cleaned = cleaned[len('```json'):].strip()
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3].strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print("[ERROR] Could not parse Gemini response as JSON. Raw response:")
        print(extracted)
        return None

    def blank_if_not_mentioned(val):
        return "-" if str(val).strip().lower() == "not mentioned" else val

    fields = [
        url,
        blank_if_not_mentioned(data.get("Job Title", "")),
        blank_if_not_mentioned(data.get("Company Name", "")),
        blank_if_not_mentioned(data.get("Location", "")),
        blank_if_not_mentioned(data.get("Industry", "")),
        blank_if_not_mentioned(data.get("Experience Level", "")),
        blank_if_not_mentioned(data.get("Salary Range", "")),
        blank_if_not_mentioned(data.get("Posted Date", "")),
    ]
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    fields.append(today)
    fields.append(blank_if_not_mentioned(data.get("Skills", "")))

    import json
    print("Parsed fields as JSON:")
    print(json.dumps({
        "Job Link": fields[0],
        "Job Title": fields[1],
        "Company Name": fields[2],
        "Location": fields[3],
        "Industry": fields[4],
        "Experience Level": fields[5],
        "Salary Range": fields[6],
        "Posted Date": fields[7],
        "Today's Date": fields[8],
        "Skills": fields[9],
    }, indent=2, ensure_ascii=False))
    print("="*40 + "\n")
    return fields

# Main function to process all job links and append results to Google Sheets
def main():
    urls = []
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        try:
            # Extract job info
            lines = process_job_posting(url)
            if not lines:
                print(f"[ERROR] No data extracted for {url}, sending only URL to sheet.")
                # Send only the URL and blanks for other columns
                lines = [url] + ["-" for _ in range(9)]
            body = {"values": [lines]}
            print(f"BODY: {body}")
            # Always create creds/service/sheet for each row
            creds = service_account.Credentials.from_service_account_file(
                CREDS_PATH, 
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()
            sheet.values().append(
                spreadsheetId=GOOGLE_SHEET_ID, 
                range=SHEET_RANGE,
                valueInputOption="USER_ENTERED", 
                body=body
            ).execute()
            print(f"[SUCCESS] Added job posting to sheet: {url}")
        except Exception as e:
            # If there's an error, send only the URL and blanks for other columns
            print(f"[ERROR] Error processing {url}: {str(e)}. Sending only URL to sheet.")
            lines = [url] + ["-" for _ in range(9)]
            body = {"values": [lines]}
            try:
                creds = service_account.Credentials.from_service_account_file(
                    CREDS_PATH, 
                    scopes=["https://www.googleapis.com/auth/spreadsheets"]
                )
                service = build('sheets', 'v4', credentials=creds)
                sheet = service.spreadsheets()
                sheet.values().append(
                    spreadsheetId=GOOGLE_SHEET_ID, 
                    range=SHEET_RANGE,
                    valueInputOption="USER_ENTERED", 
                    body=body
                ).execute()
                print(f"[SUCCESS] Added failed URL to sheet: {url}")
            except Exception as e2:
                print(f"[ERROR] Could not add failed URL to sheet: {url}. Error: {str(e2)}")

# Run the main function if this script is executed directly
if __name__ == "__main__":
    main()


# with open(LINKS_FILE, 'w') as f:
#     f.truncate(0)


