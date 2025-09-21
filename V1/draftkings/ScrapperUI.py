import tkinter as tk
from tkinter import ttk, messagebox
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Configuration for sports, tournaments, URLs, and endpoints
CONFIG = {
    "NFL": {
        "Super Bowl": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl",
            "endpoint": "http://localhost:8000/api/nfl/superbowl"
        },
        "Conference Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=conference-winner",
            "endpoint": "http://localhost:8000/api/nfl/conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=division-winner",
            "endpoint": "http://localhost:8000/api/nfl/division"
        }
    },
    "NBA": {
        "Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=champion",
            "endpoint": "http://localhost:8000/api/nba/championship"
        },
        "Conference": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=conference-winner",
            "endpoint": "http://localhost:8000/api/nba/conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=division-winner",
            "endpoint": "http://localhost:8000/api/nba/division"
        }
    },
    "WNBA": {
        "Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/wnba?category=team-futures&subcategory=championship-winner",
            "endpoint": "http://localhost:8000/api/wnba/championship"
        }
    }
}

def scrape_odds(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)  # Adjust based on page load time; consider WebDriverWait

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    results = []
    # Find all conference title blocks
    conference_titles = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    
    for title in conference_titles:
        conference_text = title.get_text(strip=True)
        # Extract conference (e.g., "NFC" or "AFC" from "NFL 2025/26 - NFC")
        conference = conference_text.split(" - ")[-1]  # Gets "NFC" or "AFC"
        
        # Find all team and odds spans following this title
        next_elements = title.find_all_next(["span"], limit=None)
        teams = []
        odds = []
        collecting = False
        
        for element in next_elements:
            if element.get("data-testid") == "button-title-market-board":
                teams.append(element.get_text(strip=True))
                collecting = True
            elif element.get("data-testid") == "button-odds-market-board" and collecting:
                odds.append(element.get_text(strip=True))
                collecting = False  # Reset after finding an odd to ensure proper pairing
            
            # Stop if we hit the next conference title or end of relevant data
            if element.find_parent("div", class_="cb-title__simple-title cb-title__nav-title") and element != title:
                break
        
        # Pair teams and odds (assuming they are in order and match in number)
        for team, odd in zip(teams, odds):
            results.append({"team": team, "odds": odd, "conference": conference, "division": None})

    return results

class ScraperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Sports Odds Scraper")
        self.root.geometry("400x300")

        # Sport selection
        tk.Label(root, text="Select Sport:").pack(pady=5)
        self.sport_var = tk.StringVar()
        self.sport_dropdown = ttk.Combobox(root, textvariable=self.sport_var, state="readonly")
        self.sport_dropdown["values"] = list(CONFIG.keys())
        self.sport_dropdown.pack(pady=5)
        self.sport_dropdown.bind("<<ComboboxSelected>>", self.update_tournaments)

        # Tournament selection
        tk.Label(root, text="Select Tournament:").pack(pady=5)
        self.tournament_var = tk.StringVar()
        self.tournament_dropdown = ttk.Combobox(root, textvariable=self.tournament_var, state="readonly")
        self.tournament_dropdown.pack(pady=5)

        # Go button
        self.go_button = tk.Button(root, text="Go", command=self.scrape_and_send)
        self.go_button.pack(pady=10)

        # Status display
        self.status_label = tk.Label(root, text="", wraplength=350)
        self.status_label.pack(pady=10)

    def update_tournaments(self, event):
        sport = self.sport_var.get()
        if sport in CONFIG:
            self.tournament_dropdown["values"] = list(CONFIG[sport].keys())
            self.tournament_var.set("")  # Reset tournament selection

    def scrape_and_send(self):
        sport = self.sport_var.get()
        tournament = self.tournament_var.get()

        if not sport or not tournament:
            messagebox.showerror("Error", "Please select a sport and tournament.")
            return

        try:
            url = CONFIG[sport][tournament]["url"]
            endpoint = CONFIG[sport][tournament]["endpoint"]

            # Scrape data
            self.status_label.config(text="Scraping data...")
            self.root.update()
            results = scrape_odds(url)

            # Send to endpoint
            response = requests.post(endpoint, json=results)
            if response.status_code == 200:
                self.status_label.config(text=f"Success! Data sent to {endpoint}\nResults: {len(results)} teams scraped.")
            else:
                self.status_label.config(text=f"Error: Failed to send data to {endpoint} - {response.text}")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to scrape or send data: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperUI(root)
    root.mainloop()