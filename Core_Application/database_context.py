import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import json


class database_context:
    """handles database interactions"""
    def __init__(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        self.DB_FILE = os.path.join(project_root, "Data", "job_postings.db")            # local database file
        self.TABLE_NAME = "job_postings"                                                # user defined table / profile
        self.HELPER_FILE = os.path.join(project_root, "Data", "parsio_settings.json")   # parsio_settings.json
        self.ERROR_FILE = os.path.join(project_root, "Data", "error.txt")               # error file
        self.data_dir = os.path.join(project_root, "Data")                              # project data root


        # read default table name and API key - create helper if first launch
        try: 
            os.makedirs(os.path.dirname(self.HELPER_FILE), exist_ok=True)
            if os.path.exists(self.HELPER_FILE):
                with open(self.HELPER_FILE, 'r') as file:
                    settings = json.load(file)
                    self.TABLE_NAME = settings.get("table_name", "job_postings")
                    self.GEMINI_API_KEY = settings.get("gemini_api_key", "")
            else:
                with open(self.HELPER_FILE, 'w') as file:
                    settings = {
                        "table_name": "job_postings",
                        "gemini_api_key": ""
                    }
                    json.dump(settings, file, indent=4)
                    self.TABLE_NAME = "job_postings"
                    self.GEMINI_API_KEY = ""
        except Exception as e:
            print(f"Settings file error: {e}")
            self.TABLE_NAME = "job_postings"
            self.GEMINI_API_KEY = ""

    def get_gemini_api_key(self) -> str:
        """Get the Gemini API key from settings"""
        return self.GEMINI_API_KEY

    def set_gemini_api_key(self, api_key: str) -> bool:
        """Set the Gemini API key in settings"""
        try:
            if os.path.exists(self.HELPER_FILE):
                with open(self.HELPER_FILE, 'r') as file:
                    settings = json.load(file)
            else:
                settings = {"table_name": self.TABLE_NAME}
            
            settings["gemini_api_key"] = api_key
            
            with open(self.HELPER_FILE, 'w') as file:
                json.dump(settings, file, indent=4)
            
            self.GEMINI_API_KEY = api_key
            return True
        except Exception as e:
            print(f"Failed to save API key: {e}")
            return False

    def init_database(self):
        """Inits the database and table on App startup"""
        try: 
            os.makedirs(os.path.dirname(self.DB_FILE), exist_ok=True)
            print(f"Database directory created at {self.DB_FILE}")
        except Exception as e:
            print(f"Database directory creation error: {e}")
            return False

        # connect to user defined table
        try:
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            
            # TODO: user defined table names
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_title TEXT NOT NULL,
                    company TEXT NOT NULL,
                    location TEXT,
                    salary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"Database ready at {self.DB_FILE}")
            return True
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            return False


    def save_job_postings(self, job_list: List[Dict]) -> bool:
        if not job_list:
            return False
        
        try:
            self.init_database()  # Ensure database exists
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            # DONE: 
            insert_sql = f'''
                INSERT INTO {self.TABLE_NAME} (job_title, company, location, salary, created_at)
                VALUES (?, ?, ?, ?, ?)
            '''
            
            current_time = datetime.now().isoformat()
            data_to_insert = []
            
            # Validate and prepare data
            for job in job_list:
                job_title = job.get('job_title', '').strip()
                company = job.get('company', '').strip()
                location = job.get('location', '').strip()
                salary = job.get('salary', '').strip()
                
                if job_title and company:  # Only insert if required fields exist
                    data_to_insert.append((
                        job_title, company, location, salary, current_time
                    ))
            
            if data_to_insert:
                cursor.executemany(insert_sql, data_to_insert)
                conn.commit()
                print(f"Saved {len(data_to_insert)} job postings to database")
                return True
            else:
                print("No valid data to save")
                return False
                
        except Exception as e:
            print(f"Database save error: {e}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()




#  %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


    
    def get_database_stats(self, recent_limit: int = 5) -> str:
        """Get comprehensive database statistics as a formatted string"""
        try:
            self.init_database()
            conn = sqlite3.connect(self.DB_FILE)
            cursor = conn.cursor()
            
            # Get total job count
            cursor.execute(f'SELECT COUNT(*) FROM {self.TABLE_NAME}')
            total_jobs = cursor.fetchone()[0]
            
            # Get unique company count
            cursor.execute(f'SELECT COUNT(DISTINCT company) FROM {self.TABLE_NAME}')
            unique_companies = cursor.fetchone()[0]
            
            # Get recent jobs
            cursor.execute(f'''
                SELECT job_title, company, location, salary, created_at
                FROM {self.TABLE_NAME} 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (recent_limit,))
            
            recent_jobs = cursor.fetchall()
            conn.close()
            
            # Format the output
            stats = f"=== Database Status ===\n"
            stats += f"Total Jobs: {total_jobs}\n"
            stats += f"Companies: {unique_companies}\n"
            
            if recent_jobs:
                stats += f"\nRecent Jobs:\n"
                for job in recent_jobs:
                    job_title, company, location, salary, created_at = job
                    stats += f"  • {job_title} at {company}\n"
                    if location:
                        stats += f"    Location: {location}\n"
                    if salary:
                        stats += f"    Salary: {salary}\n"
                    stats += f"    Added: {created_at}\n"
            else:
                stats += "\nNo jobs found in database."
            
            return stats
            
        except Exception as e:
            return f"Error getting database stats: {e}"

    





def fetch_url_content(url: str) -> Optional[str]:
    """Fetch webpage content and return visible text"""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"URL fetch failed: {e}")
        return None


# Global database context instance
db = database_context()

