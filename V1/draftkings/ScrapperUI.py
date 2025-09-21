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
            "endpoint": "http://localhost:8000/api/nfl/superbowl",
            "event_type": "championship"
        },
        "Conference Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=conference-winner",
            "endpoint": "http://localhost:8000/api/nfl/conference",
            "event_type": "conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=division-winner",
            "endpoint": "http://localhost:8000/api/nfl/division",
            "event_type": "division"
        }
    },
    "NBA": {
        "Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=champion",
            "endpoint": "http://localhost:8000/api/nba/championship",
            "event_type": "championship"
        },
        "Conference": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=conference-winner",
            "endpoint": "http://localhost:8000/api/nba/conference",
            "event_type": "conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=division-winner",
            "endpoint": "http://localhost:8000/api/nba/division",
            "event_type": "division"
        }
    },
    "WNBA": {
        "Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/wnba?category=team-futures&subcategory=championship-winner",
            "endpoint": "http://localhost:8000/api/wnba/championship",
            "event_type": "championship"
        }
    }
}

def scrape_odds(url, event_type="championship"):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)  # Adjust based on page load time; consider WebDriverWait

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    if event_type == "championship":
        return scrape_championship_odds(soup)
    elif event_type == "conference":
        return scrape_conference_odds(soup)
    elif event_type == "division":
        return scrape_division_odds(soup)
    else:
        # Fallback to simple scraping
        return scrape_simple_odds(soup)

def scrape_championship_odds(soup):
    """Scrape championship odds - flat list of all teams"""
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    teams = []
    for team, odd in zip(team_elements, odds_elements):
        teams.append({
            "team": team.get_text(strip=True),
            "odds": odd.get_text(strip=True)
        })
    
    return {
        "event_type": "championship",
        "teams": teams
    }

def scrape_conference_odds(soup):
    """Scrape conference odds - teams grouped by conference"""
    conference_titles = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    conferences = []
    
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
        
        # Pair teams and odds
        team_odds = []
        for team, odd in zip(teams, odds):
            team_odds.append({
                "team": team,
                "odds": odd
            })
        
        if team_odds:  # Only add if we found teams
            conferences.append({
                "conference": conference,
                "teams": team_odds
            })
    
    return {
        "event_type": "conference",
        "conferences": conferences
    }

def scrape_division_odds(soup):
    """Scrape division odds - teams grouped by division"""
    # Look for division titles (e.g., "NFC East", "AFC West")
    division_titles = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    divisions = []
    
    for title in division_titles:
        division_text = title.get_text(strip=True)
        # Extract division info (e.g., "NFC East" from "NFL 2025/26 - NFC East")
        full_division = division_text.split(" - ")[-1]  # Gets "NFC East" or "AFC West"
        
        # Split into conference and division
        parts = full_division.split()
        if len(parts) >= 2:
            conference = parts[0]  # "NFC" or "AFC"
            division = " ".join(parts[1:])  # "East", "West", "South", "North"
        else:
            conference = full_division
            division = "Unknown"
        
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
                collecting = False
            
            # Stop if we hit the next division title or end of relevant data
            if element.find_parent("div", class_="cb-title__simple-title cb-title__nav-title") and element != title:
                break
        
        # Pair teams and odds
        team_odds = []
        for team, odd in zip(teams, odds):
            team_odds.append({
                "team": team,
                "odds": odd
            })
        
        if team_odds:  # Only add if we found teams
            divisions.append({
                "division": division,
                "conference": conference,
                "teams": team_odds
            })
    
    return {
        "event_type": "division",
        "divisions": divisions
    }

def scrape_simple_odds(soup):
    """Fallback simple scraping for unknown event types"""
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    teams = []
    for team, odd in zip(team_elements, odds_elements):
        teams.append({
            "team": team.get_text(strip=True),
            "odds": odd.get_text(strip=True)
        })
    
    return {
        "event_type": "championship",
        "teams": teams
    }

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
            event_type = CONFIG[sport][tournament]["event_type"]

            # Scrape data
            self.status_label.config(text="Scraping data...")
            self.root.update()
            results = scrape_odds(url, event_type)
            
            # Debug: Print what we scraped
            print(f"Scraped {event_type} data: {results}")

            # Send to endpoint
            response = requests.post(endpoint, json=results)
            if response.status_code == 200:
                response_data = response.json()
                total_teams = response_data.get("total_teams", 0)
                event_type = response_data.get("event_type", "unknown")
                self.status_label.config(text=f"Success! Data sent to {endpoint}\nEvent Type: {event_type}\nTotal Teams: {total_teams}")
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                print(f"API Error: {error_msg}")
                self.status_label.config(text=f"Error: Failed to send data to {endpoint}\n{error_msg}")
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to scrape or send data: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperUI(root)
    root.mainloop()