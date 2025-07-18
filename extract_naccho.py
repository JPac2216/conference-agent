from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import requests
import csv

parsed_sessions = []

def scrape_html(url: str):
    # Headers to simulate a real browser request
    headers = {
        "accept": "application/json",
        "origin": "https://www.mapyourshow.com/",
        "referer": "https://www.mapyourshow.com/",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    # Request session data
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    # Fetching title
    title = soup.find(class_="exhibitorsession-name").get_text(separator=' ', strip=True)

    # Fetching date & time
    tag = soup.find("span", class_="f2")
    if tag:
        html = str(tag)
        split = html.split('<span class="f2">', 1)[1].strip(" ")
        if "On Demand" in split:
            date = split.split("</span>")[0]
            start_time = ""
            end_time = ""
        else:
            day = split.split("<span>")[1].split("</span>")[0]
            date = day + " " + split.split(f'<span>{day}</span> <span class="nowrap">')[1].split('</span>\n</span>')[0]
            time = soup.find("span", class_="b").string.split(" - ")
            start_time = time[0]
            end_time = time[1]
    
    # Fetching speaker info
    speakers = soup.find_all("div", class_="bio-wrapper")

    presenters = ""
    professional_titles = ""
    institutions = ""

    for speaker in speakers:
        name = speaker.find(class_="name").get_text(separator=' ', strip=True).split(", ")[1] + " " + speaker.find(class_="name").get_text(separator=' ', strip=True).split(", ")[0]
        
        info = speaker.find(class_="job-title").get_text(separator=' ', strip=True) if speaker.find(class_="job-title") else ""
        if info and " at " in info:
            professional_title = info.split(" at ")[0]
            institution = info.split(" at ")[1]
        else:
            professional_title = ""
            institution = info

        presenters += f"{name} | "
        professional_titles += f"{professional_title} | "
        institutions += f"{institution} | "

    presenters = presenters[:-3]
    professional_titles = professional_titles[:-3]
    institutions = institutions[:-3]

    
    # Fetching description from JS  
    description = None
    for script in soup.find_all("script"):
        if script.string and "Vue.component" in script.string and "description:" in script.string:
            lines = script.string.splitlines()
            for line in lines:
                if "description:" in line:
                    desc_part = line.split("description:", 1)[1]
                    description = desc_part.strip().strip('",')
                    break

    # Append info to the sessions list 
    parsed_sessions.append({
    'Title': title,
    'Date': date,
    'Start Time': start_time,
    'End Time': end_time,
    'Location': "",
    'Preregistration': "",
    'Presenters': presenters,
    'Professional Titles': professional_titles,
    'Institutions': institutions,
    'Sponsors': "",
    'Description': description
    })

def main():
    service = Service(executable_path="chromedriver.exe")
    driver = webdriver.Chrome(service=service)

    driver.get("https://naccho2025.mapyourshow.com/8_0/explore/session-fulllist.cfm#/")

    # List all results on the page
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".result-heading.mb0.pb4"))
    )

    num_results = int(driver.find_element(By.CSS_SELECTOR, "h1.f1.ma0.mb3.mb0-l.normal > span > span:nth-of-type(1)").text)

    wait_time = int(num_results // 3.34)

    all_results = driver.find_element(By.CSS_SELECTOR, ".result-heading.mb0.pb4 .btn-tertiary.btn-tertiary_small")
    all_results.click()

    time.sleep(1)

    print(wait_time)

    body = driver.find_element(By.TAG_NAME, "body")
    for _ in range(wait_time):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.005)

    # Store all of the session links into an array
    link_elements = driver.find_elements(By.CSS_SELECTOR, ".card-Title.break-word.f2.mb0.mt0 a")
    session_links = [el.get_attribute("href") for el in link_elements]
    print(f"Found {len(session_links)} sessions for NACCHO360 2025.")

    driver.quit()

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scrape_html, link) for link in session_links]

    for i, future in enumerate(as_completed(futures)):
        try:
            future.result()
        except Exception as e:
            print(f"Error scraping session {i + 1}: {e}, \n{session_links[i]}")

    # Save to CSV
    with open("naccho2025_sessions.csv", mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ['Title', 'Date', 'Start Time', 'End Time', 'Location', 'Preregistration', 'Presenters', 'Professional Titles', 'Institutions', 'Sponsors', 'Description']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parsed_sessions)

    print(f"✅ Saved {len(parsed_sessions)} sessions to 'apha2025_sessions.csv'")


if __name__ == "__main__":
    main()

    #Errored session
    # scrape_html("https://naccho2025.mapyourshow.com/8_0/sessions/session-details.cfm?scheduleid=1311")