import requests
import re
import json
import tkinter as tk
from tkinter import filedialog
from bs4 import BeautifulSoup

def get_events(url):
    urlf, urlb = url.split("/regatta")
    url = urlf + "/regatta/entries" + urlb
    event_page = requests.get(url)  # get page from http request
    soup = BeautifulSoup(event_page.content, 'html.parser')  # parse response

    table = soup.table.tbody#.next_sibling.next_sibling  # navigate to table row of the first event

    events = []
    for link in table.find_all('a'):
        event = {
            "title": link.string,
            "link": link.get('href')
        }
        events.append(event)

    return events

def get_entries(url):
    event_page = requests.get("https://www.regattacentral.com" + url)  # get page from http request
    soup = BeautifulSoup(event_page.content, 'html.parser')  # parse response

    table = soup.table.tbody#.next_sibling.next_sibling  # navigate to table row of the first event
    lineups = table.find_all(class_="lineupTooltip")
    result = []

    for lineup in lineups:
        arr = lineup["title"].split("<br>")
        result.append(arr[0][3:])

    return result

def create_file(entries, title):
    duration = re.search("\([0-9]?[0-9][0-9][0-9]m", title)
    if duration:
        duration = duration.group()
        duration = int(re.search("[0-9]?[0-9][0-9][0-9]", duration).group())
    else:
        duration = 2000

    race = {
        "race_definition": {
            "boats": [],
            "c2_race_id": "",
            "duration": duration,
            "duration_type": "meters",
            "event_name": "erg sprints", # todo
            "handicap_enabled": False,
            "name_long": title,
            "name_short": "short name",
            "race_id": "",
            "race_type": "individual",
            "split_value": 500,
            "team_size": 1,
            "time_cap": 0
        }
    }

    if "relay" in title or "Relay" in title:
        race["display_prompt_at_splits"] = True
        race["race_type"] = "relay"
        race["sound_horn_at_splits"] = True
        race["team_size"] = 4

    lane = 1
    for competitor in entries:
        boat = {
            "affiliation": "",
            "class_name": "",
            "lane_number": lane,
            "name": competitor,
            "participants": [
                {
                    "name": ""
                }
            ]
        }
        race["race_definition"]["boats"].append(boat)
        lane = lane + 1

    race_name = title.replace(":", "")
    file_location = directory_path + "/" + race_name + ".rac2"
    with open(file_location, 'w', encoding='utf-8') as f:
        json.dump(race, f, ensure_ascii=False, indent=4)

regatta_url = input("url to regatta home page: ")

root = tk.Tk()
root.withdraw()

directory_path = filedialog.askdirectory()

events = get_events(regatta_url)

for event in events:
    entries = get_entries(event["link"])
    if len(entries) > 0:
        create_file(entries, event["title"])
    print(event["title"], len(entries))