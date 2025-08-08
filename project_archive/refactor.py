import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
SHEET_RANGE = os.getenv("SHEET_RANGE")
CREDS_PATH = os.getenv("CREDS_PATH")
LINKS_FILE = os.getenv("LINKS_FILE")

class JobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.google_service = None
        
    def initialize_google_service(self):
        """Initialize Google Sheets service"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                CREDS_PATH, 
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            self.google_service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            raise

    def get_urls_from_file(self) -> List[str]:
        """Read all URLs from the links file"""
        if not os.path.exists(LINKS_FILE):
            logger.warning(f"Links file {LINKS_FILE} not found")
            return []
        
        try:
            with open(LINKS_FILE, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(urls)} URLs from {LINKS_FILE}")
            return urls
        except Exception as e:
            logger.error(f"Error reading links file: {e}")
            return []

    def scrape_job_page(self, url: str) -> Optional[str]:
        """Scrape job posting content from URL"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            job_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up excessive whitespace
            job_text = re.sub(r'\s+', ' ', job_text)
            
            # Limit text length to avoid API limits
            if len(job_text) > 50000:
                job_text = job_text[:50000] + "..."
                
            return job_text
            
        except requests.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            return None

    def call_gemini(self, prompt: str, max_retries: int = 3) -> Optional[Dict]:
        """Call Gemini API with improved error handling"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=payload, timeout=60)
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 429:
                    wait_time = min(60, 10 * (2 ** attempt))  # Exponential backoff
                    logger.warning(f"Rate limited. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                elif response.status_code >= 500:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Server error {response.status_code}. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP error {response.status_code}: {e}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    
        logger.error(f"Failed to call Gemini API after {max_retries} attempts")
        return None

    def extract_job_info(self, job_text: str) -> Optional[Dict]:
        """Extract job information using Gemini API"""
        prompt = f"""
        You are an information extraction AI. Extract the following information from this job posting text and return it as valid JSON:

        Job posting text:
        {job_text}

        Extract these fields (use exact field names):
        - "Job Title": The job title
        - "Company Name": The company name
        - "Location": Job location (city, state/country)
        - "Industry": Industry sector (make educated guess if not explicit)
        - "Experience Level": Entry/Mid/Senior level (analyze requirements)
        - "Salary Range": Salary if mentioned (format: $X-$Y or $X/hour)
        - "Posted Date": Job posting date in YYYY-MM-DD format
        - "Skills": Main technical and soft skills, separated by " - "

        Rules:
        - Use "Not mentioned" for missing information
        - Capitalize job title and company name properly
        - Return only valid JSON, no extra text or markdown
        - Be concise and accurate

        Example format:
        {{
            "Job Title": "Software Engineer",
            "Company Name": "Tech Corp",
            "Location": "San Francisco, CA",
            "Industry": "Technology",
            "Experience Level": "Mid",
            "Salary Range": "$80,000-$120,000",
            "Posted Date": "2024-01-15",
            "Skills": "Python - JavaScript - React - Problem Solving - Communication"
        }}
        """

        gemini_response = self.call_gemini(prompt)
        if not gemini_response:
            return None

        try:
            extracted_text = gemini_response['candidates'][0]['content']['parts'][0]['text']
            
            # Clean JSON response
            cleaned = extracted_text.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[len('```json'):].strip()
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].strip()
            
            data = json.loads(cleaned)
            return data
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.debug(f"Raw response: {gemini_response}")
            return None

    def format_job_data(self, url: str, job_data: Optional[Dict]) -> List[str]:
        """Format job data for Google Sheets"""
        def clean_value(val):
            if not val or str(val).strip().lower() in ["not mentioned", "n/a", ""]:
                return "-"
            return str(val).strip()

        if not job_data:
            # Return row with just URL and blanks
            return [url] + ["-"] * 9

        today = datetime.now().strftime('%Y-%m-%d')
        
        return [
            url,
            clean_value(job_data.get("Job Title")),
            clean_value(job_data.get("Company Name")),
            clean_value(job_data.get("Location")),
            clean_value(job_data.get("Industry")),
            clean_value(job_data.get("Experience Level")),
            clean_value(job_data.get("Salary Range")),
            clean_value(job_data.get("Posted Date")),
            today,  # Today's date
            clean_value(job_data.get("Skills"))
        ]

    def append_to_sheet(self, row_data: List[str]) -> bool:
        """Append data to Google Sheets"""
        try:
            if not self.google_service:
                self.initialize_google_service()
                
            body = {"values": [row_data]}
            
            self.google_service.spreadsheets().values().append(
                spreadsheetId=GOOGLE_SHEET_ID,
                range=SHEET_RANGE,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error appending to sheet: {e}")
            return False

    def process_job_url(self, url: str) -> bool:
        """Process a single job URL"""
        logger.info(f"Processing: {url}")
        
        # Scrape job page
        job_text = self.scrape_job_page(url)
        if not job_text:
            logger.warning(f"Failed to scrape content from {url}")
            row_data = self.format_job_data(url, None)
            return self.append_to_sheet(row_data)
        
        # Extract job information
        job_data = self.extract_job_info(job_text)
        if job_data:
            logger.info(f"Successfully extracted job data for {url}")
            logger.debug(f"Extracted data: {json.dumps(job_data, indent=2)}")
        else:
            logger.warning(f"Failed to extract job data for {url}")
        
        # Format and save to sheet
        row_data = self.format_job_data(url, job_data)
        success = self.append_to_sheet(row_data)
        
        if success:
            logger.info(f"Successfully saved data for {url}")
        else:
            logger.error(f"Failed to save data for {url}")
            
        # Rate limiting
        time.sleep(3)  # Reduced from 5 seconds
        
        return success

    def run(self):
        """Main execution method"""
        logger.info("Starting job scraper")
        
        # Validate environment variables
        required_vars = [GEMINI_API_KEY, GOOGLE_SHEET_ID, SHEET_RANGE, CREDS_PATH, LINKS_FILE]
        if not all(required_vars):
            logger.error("Missing required environment variables")
            return
        
        # Initialize Google Sheets service
        self.initialize_google_service()
        
        # Get URLs to process
        urls = self.get_urls_from_file()
        if not urls:
            logger.info("No URLs to process")
            return
        
        # Process each URL
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}")
            
            try:
                if self.process_job_url(url):
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Unexpected error processing {url}: {e}")
                failed += 1
        
        logger.info(f"Job scraping completed. Successful: {successful}, Failed: {failed}")

def main():
    """Entry point"""
    scraper = JobScraper()
    scraper.run()

if __name__ == "__main__":
    main()

# Uncomment to clear the links file after processing
# with open(LINKS_FILE, 'w') as f:
#     f.truncate(0)