from bs4 import BeautifulSoup
import requests
import csv

parsed_sessions = []

def scrape_html(url: str, headers: dict):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    div = soup.find(class_="popup_content")

    title = div.find("h1").text


    date = div.find(class_="pres-tidbit").text.strip()
    time = div.find("span", class_="tipsytip").text
    start_time = time.split(" - ")[0] + " CT"
    end_time = time.split(" - ")[1]

    try:
        location = div.find_all("span")[1].text.split("Location: ")[1]
    except Exception as e:
        location = ""

    presenters = ""
    professional_titles = ""
    institutions = ""

    for speaker in soup.find_all(class_="speakerrow"):
        name = speaker.find(class_="speaker-name").text
        professional_info = speaker.find("p", "text-muted").get_text(separator="\n").split("\n")
        professional_title = professional_info[0]
        institution = professional_info[1]

        presenters += f"{name} | "
        professional_titles += f"{professional_title} | "
        institutions += f"{institution} | "

    presenters = presenters[:-3]
    professional_titles = professional_titles[:-3]
    institutions = institutions[:-3]

    try:
        description = soup.find(class_="PresentationAbstractText").get_text(separator="\n")
    except Exception as e:
        description = ""

    # Append info to the sessions list 
    parsed_sessions.append({
    'Title': title,
    'Date': date,
    'Start Time': start_time,
    'End Time': end_time,
    'Location': location,
    'Preregistration': "",
    'Presenters': presenters,
    'Professional Titles': professional_titles,
    'Institutions': institutions,
    'Sponsors': "",
    'Description': description
    })


def main():
    # Headers to simulate a real browser request
    headers = {
        "accept": "application/json",
        "origin": "https://2025chiandexpo.eventscribe.net/",
        "referer": "https://2025chiandexpo.eventscribe.net/agenda.asp?BCFO=&pfp=BrowsebyDay&fa=&fb=&fc=&fd=&all=1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    main_url = "https://2025chiandexpo.eventscribe.net/agenda.asp?BCFO=&pfp=BrowsebyDay&fa=&fb=&fc=&fd=&all=1"
    # Request session data
    page = requests.get(main_url, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')

    #Fetching session IDS and calling scrape_html
    for li in soup.find_all("li", class_="list-group-item"):
        id = li.get("data-presid")
        if id:
            try:
                scrape_html(f"https://2025chiandexpo.eventscribe.net/fsPopup.asp?PresentationID={id}&mode=presInfo", headers)
            except Exception as e:
                print(f"Error scraping session {id}: {e}, \nhttps://2025chiandexpo.eventscribe.net/fsPopup.asp?PresentationID={id}&mode=presInfo \n\n")


    # Save to CSV
    with open("chiexpo2025_sessions.csv", mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ['Title', 'Date', 'Start Time', 'End Time', 'Location', 'Preregistration', 'Presenters', 'Professional Titles', 'Institutions', 'Sponsors', 'Description']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(parsed_sessions)

    print(f"✅ Saved {len(parsed_sessions)} sessions to 'apha2025_sessions.csv'")

if __name__ == "__main__":
    main()
    
    
    # scrape_html(
    #     url="https://2025chiandexpo.eventscribe.net/fsPopup.asp?PresentationID=1595430&mode=presInfo",
    #     headers = {
    #         "accept": "application/json",
    #         "origin": "https://2025chiandexpo.eventscribe.net/",
    #         "referer": "https://2025chiandexpo.eventscribe.net/agenda.asp?BCFO=&pfp=BrowsebyDay&fa=&fb=&fc=&fd=&all=1",
    #         "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    #     }
    # )