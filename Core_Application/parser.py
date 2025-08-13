import json
import google.generativeai as genai
import os

from utils import extract_json  

def parse_with_gemini(text, api_key: str):
    """Parses info into json"""
    if not api_key:
        raise ValueError("Gemini API key is required")
    
    # Configure Gemini with the provided API key
    genai.configure(api_key=api_key)
    
    # TODO: error handling
    prompt = (
            "Extract the following fields from the job posting text below: "
            "job_title, company, location, salary. "
            "ALWAYS return a valid JSON object with these exact keys: "
            '{"job_title": "", "company": "", "location": "", "salary": ""}. '
            "Do not include any text outside of the JSON object.\n\n"
            f"Job Posting:\n{text}\n\n"
        )
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)

    raw_output = response.candidates[0].content.parts[0].text.strip()

    json_text = extract_json(raw_output)
    parsed_data = json.loads(json_text)
    required_fields = ["job_title", "company", "location", "salary"]
    
    for field in required_fields:
        if field not in parsed_data:
            parsed_data[field] = ""


    return parsed_data
