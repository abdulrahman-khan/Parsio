# PARSIO - WIP
uses gemini LLM to parse job application information, automatically storing that information into an excel document

## potential features
- connection with email clients to automatically update application status 
- insightful dashboard view providing application statistics


---

# version 1 - OLD
`old_script.py`

application that streamlines the job application process by doing the tracking work for you!
uses gemini LLM to parse important information, storing it into a google sheet document

- pulls import job imformation from each url
- uses Gemini LLM to extract structured job data in JSON format.
- appends each job posting as a new row in your Google Sheet.

```
  - Job Title
  - Company Name
  - Location
  - Industry
  - Experience Level
  - Salary Range
  - Posted Date
  - Skills
```
