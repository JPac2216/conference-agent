import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()


# tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def linkedin_search_tool(name: str, title: str, institution: str) -> str:
    """This tool retrieves a presenter's LinkedIn profile (if available) given their full name, professional title, and institution."""

    url = "https://api.tavily.com/search"

    payload = {
        "query": f"Find {name}'s LinkedIn profile, they are the {title} at {institution}."
    }
    headers = {
        "Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    #print(response.text)
    dict = json.loads(response.text)
    raw_url = dict["results"][0]["url"]

    if "/posts/" in raw_url or "/activity/" in raw_url:
        profile = raw_url.split("linkedin.com/")[1].split("/")[1].split("_")[0]
        return f"https://www.linkedin.com/in/{profile}"
    return raw_url

linkedin_search_tool('Anandi Law', 'University of California, San Francisco', 'Assistant Professor')