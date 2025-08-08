import requests
import csv
import bs4
from bs4 import BeautifulSoup 
    
url = "https://hiring.cafe/job/YmFtYm9vaHJfX19tb3J0Z2FnZWF1dG9tYXRvcl9fXzUy"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
job_text = soup.get_text(separator=' ', strip=True)


print(f"JOB TEXT - {job_text}")