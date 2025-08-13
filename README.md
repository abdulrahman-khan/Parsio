# PARSIO - AI Job Application Tracker
A desktop application that streamlines the job application tracking process by automatically parsing job postings using Google's Gemini LLM and storing structured data in a local SQLite database.

<div align="center">
  <img width="512" height="512" alt="icon" src="https://github.com/user-attachments/assets/b2d4a5af-0042-4b3c-a761-f346cfe7d14e" />
</div>


## Project Purpose

PARSIO helps job seekers efficiently track their applications by:
- **Automatically extracting** key information from job postings (URLs or raw text)
- **Using AI-powered parsing** via Google Gemini LLM for accurate data extraction
- **Storing structured data** in a local SQLite database for easy tracking

## 🏗️ Project Structure

```
Parsio/
├── Core_Application/         # Main application code
│   ├── main.py               # Application entry point
│   ├── ui.py                 # Main UI logic and event handling
│   ├── interface.py          # PyQt5 UI definitions (auto-generated)
│   ├── parser.py             # Gemini LLM integration and parsing logic
│   ├── database_context.py   # SQLite database operations and settings
│   ├── utils.py              # Utility functions
│   └── ui.ui                 # Qt Designer UI file
├── Data/                     # Application data storage
│   ├── job_postings.db       # SQLite database
│   ├── parsio_settings.json  # User settings and API keys
│   ├── error.txt             # Error logs
│   └── images/               # Application icons
├── requirements.txt          # Python dependencies
└── run_parsio.py             # Alternative entry point
```


### Extracted Data Fields
- Job Title
- Company Name
- Location
- Salary Information
- Creation Timestamp

## Setup

### Prerequisites
- Python 3.7+
- Google Gemini API key - https://aistudio.google.com/app/apikey

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/abdulrahman-khan/Parsio.git
   cd Parsio
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Gemini API key**
   - The application will automatically create `Data/parsio_settings.json` on first run
   - Edit the file and add your API key: `"gemini_api_key": "your_api_key_here"`

```json
{
    "table_name": "job_postings",
    "gemini_api_key": "your_api_key_here"
}
```

5. **Running the Application**
```bash
python run_parsio.py
```


## Technical Details

### Dependencies
- **PyQt5**: Desktop GUI framework
- **google-generativeai**: Gemini LLM 
- **sqlite3**: Local database 
- **requests + BeautifulSoup**: Web scraping 



## Dev Status

### In Progress
- Settings menu for API key configuration
- Multiple profile support with setting menu for Table/Profiles configuration
- Stats reporting
- Async LLM calls 
- Cleaner UI with buttons to clear view

### Planned Features 
- Email client integration for automatic status updates
- Application status tracking
