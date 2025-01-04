import requests
import re
import json
import tkinter as tk
from tkinter import filedialog
from bs4 import BeautifulSoup
from pathlib import Path
import logging
from typing import List, Tuple, Dict, Any

# Constants
BASE_URL = "https://www.regattacentral.com"  # Base URL for constructing full URLs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_events(url: str) -> Tuple[List[Dict[str, str]], str]:
    """Fetches event data from the given regatta URL.

    Args:
        url (str): The URL of the regatta page.

    Returns:
        Tuple[List[Dict[str, str]], str]: A list of events with titles and links, and the regatta title.
    """
    try:
        # Modify the URL to point to the entries page
        urlf, urlb = url.split("/regatta")
        event_url = f"{urlf}/regatta/entries{urlb}"

        # Fetch the page content
        response = requests.get(event_url)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        title = (soup.title.string[:-10]).strip() if soup.title else "Unknown Title"

        # Find the table containing events
        table = soup.table.tbody if soup.table else None
        if not table:
            logging.error("Table or tbody not found in the page.")
            return [], title

        # Extract event titles and links from the table
        events = [
            {"title": link.string.strip(), "link": link.get('href')}
            for link in table.find_all('a')
            if link.string and link.get('href')
        ]
        return events, title

    except (ValueError, requests.exceptions.RequestException) as e:
        logging.error(f"Error fetching events: {e}")
        return [], ""

def get_entries(url: str) -> List[str]:
    """Fetches the list of entries for a specific event.

    Args:
        url (str): The URL of the event page.

    Returns:
        List[str]: A list of competitor names.
    """
    try:
        # Fetch the event page content
        response = requests.get(f"{BASE_URL}{url}")
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.table.tbody if soup.table else None
        if not table:
            logging.warning("Table or tbody not found in the page.")
            return []

        # Extract competitor names from tooltips
        lineups = table.find_all(class_="lineupTooltip")
        return [lineup["title"].split("<br>")[0][3:] for lineup in lineups if lineup.has_attr("title")]

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching entries: {e}")
        return []

def create_file(entries: List[str], title: str, regatta_title: str, directory_path: Path) -> None:
    """Creates a JSON file for the race definition.

    Args:
        entries (List[str]): List of competitor names.
        title (str): The event title.
        regatta_title (str): The overall regatta title.
        directory_path (Path): The directory to save the JSON file.
    """
    # Determine race duration from the title
    duration_match = re.search(r"\([0-9]{3,4}m", title)
    duration = int(re.search(r"[0-9]{3,4}", duration_match.group()).group()) if duration_match else 2000

    # Define the race configuration
    race = {
        "race_definition": {
            "boats": [],
            "c2_race_id": "",
            "duration": duration,
            "duration_type": "meters",
            "event_name": regatta_title,
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

    # Adjust configuration for relay events
    if "relay" in title.lower():
        race["display_prompt_at_splits"] = True
        race["race_definition"]["race_type"] = "relay"
        race["sound_horn_at_splits"] = True
        race["race_definition"]["team_size"] = 4

    # Add competitors to the race configuration
    for lane, competitor in enumerate(entries, start=1):
        boat = {
            "affiliation": "",
            "class_name": "",
            "lane_number": lane,
            "name": competitor,
            "participants": [{"name": ""}]
        }
        race["race_definition"]["boats"].append(boat)

    # Create the output file path
    race_name = title.replace(":", "")
    file_path = directory_path / f"{race_name}.rac2"

    try:
        # Write the race configuration to a JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(race, f, ensure_ascii=False, indent=4)
        logging.info(f"File created: {file_path}")
    except IOError as e:
        logging.error(f"Error writing file {file_path}: {e}")

def main():
    """Main function to execute the script."""
    # Prompt user for regatta URL
    regatta_url = input("URL to regatta home page: ").strip()
    if not regatta_url:
        logging.error("Regatta URL cannot be empty.")
        return

    # Prompt user for directory to save files
    root = tk.Tk()
    root.withdraw()
    directory_path = filedialog.askdirectory()
    if not directory_path:
        directory_path = input("Enter directory path: ").strip()
    directory_path = Path(directory_path)

    # Fetch events and process each event
    events, regatta_title = get_events(regatta_url)
    if not events:
        logging.error("No events found.")
        return

    for event in events:
        entries = get_entries(event["link"])
        if entries:
            create_file(entries, event["title"], regatta_title, directory_path)
        logging.info(f"Processed event: {event['title']} with {len(entries)} entries.")

if __name__ == "__main__":
    main()
