import requests
import csv
from bs4 import BeautifulSoup

def main():
    # API endpoint
    url = "https://pheedloop.com/api/site/APhA2025/sessions/"

    # Headers to simulate a real browser request
    headers = {
        "accept": "application/json",
        "origin": "https://site.pheedloop.com",
        "referer": "https://site.pheedloop.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    # Request session data
    response = requests.get(url, headers=headers)
    sessions = response.json()  # response is already a list

    parsed_sessions = []

    for session in sessions:
        title = session.get('title', '')
        date = session.get('sessionDate', '')
        start_time = session.get('startTime', '')
        end_time = session.get('endTime', '')

        # Handle optional location
        location = ''
        if isinstance(session.get('location'), dict):
            location = session['location'].get('title', '')

        # Strip HTML from description
        html_description = session.get('description', '')
        soup = BeautifulSoup(html_description, 'html.parser')
        plain_description = soup.get_text(separator=' ', strip=True)

        parsed_sessions.append({
            'Title': title,
            'Date': date,
            'Start Time': start_time,
            'End Time': end_time,
            'Location': location,
            'Description': plain_description
        })

    # Save to CSV
    with open("apha2025_sessions.csv", mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ['Title', 'Date', 'Start Time', 'End Time', 'Location', 'Description']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parsed_sessions)

    print(f"✅ Saved {len(parsed_sessions)} sessions to 'apha2025_sessions.csv'")
