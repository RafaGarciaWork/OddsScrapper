"""DraftKings Sports Odds Scraper with GUI Interface

This module provides a comprehensive solution for scraping sports odds from DraftKings
and sending the data to a FastAPI backend. It supports multiple sports (NFL, NBA, WNBA)
and different tournament types (championship, conference, division).

Classes:
    ScraperUI: Main GUI application for selecting and scraping odds

Functions:
    scrape_odds: Main scraping function that handles different event types
    scrape_championship_odds: Scrapes flat list of teams for championships
    scrape_conference_odds: Scrapes teams grouped by conference
    scrape_division_odds: Scrapes teams grouped by division
    scrape_simple_odds: Fallback scraper for unknown event types
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Any

# Configuration for sports, tournaments, URLs, and endpoints
CONFIG = {
    "NFL": {
        "Super Bowl": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl",
            "endpoint": "http://localhost:8000/api/draftkings/nfl/super-bowl",
            "event_type": "championship"
        },
        "Conference Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=conference-winner",
            "endpoint": "http://localhost:8000/api/draftkings/nfl/conference-winner",
            "event_type": "conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=division-winner",
            "endpoint": "http://localhost:8000/api/draftkings/nfl/division-winner",
            "event_type": "division"
        }
    },
    "NBA": {
        "Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=champion",
            "endpoint": "http://localhost:8000/api/draftkings/nba/championship",
            "event_type": "championship"
        },
        "Conference": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=conference-winner",
            "endpoint": "http://localhost:8000/api/draftkings/nba/conference-winner",
            "event_type": "conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=team-futures&subcategory=division-winner",
            "endpoint": "http://localhost:8000/api/draftkings/nba/division-winner",
            "event_type": "division"
        }
    },
    "WNBA": {
        "Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/wnba?category=team-futures&subcategory=championship-winner",
            "endpoint": "http://localhost:8000/api/draftkings/wnba/championship",
            "event_type": "championship"
        }
    }
}

def scrape_odds(url: str, event_type: str = "championship") -> Dict[str, Any]:
    """Main scraping function that handles different event types.
    
    Args:
        url: The DraftKings URL to scrape
        event_type: Type of event ('championship', 'conference', 'division')
        
    Returns:
        Dictionary containing scraped odds data structured by event type
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(5)  # Wait for JavaScript to load content

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # Route to appropriate scraper based on event type
    scrapers = {
        "championship": scrape_championship_odds,
        "conference": scrape_conference_odds,
        "division": scrape_division_odds
    }
    
    return scrapers.get(event_type, scrape_simple_odds)(soup)

def scrape_championship_odds(soup: BeautifulSoup) -> Dict[str, Any]:
    """Scrape championship odds as a flat list of all teams.
    
    Args:
        soup: BeautifulSoup object of the scraped page
        
    Returns:
        Dictionary with event_type and teams list
    """
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    teams = [
        {"team": team.get_text(strip=True), "odds": odd.get_text(strip=True)}
        for team, odd in zip(team_elements, odds_elements)
    ]
    
    return {"event_type": "championship", "teams": teams}

def scrape_conference_odds(soup: BeautifulSoup) -> Dict[str, Any]:
    """Scrape conference odds with teams grouped by conference.
    
    Args:
        soup: BeautifulSoup object of the scraped page
        
    Returns:
        Dictionary with event_type, conferences list, and validation data
    """
    team_spans = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_spans = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    # Create teams list with bounds checking
    teams = [
        {"team": team_span.get_text(strip=True), "odds": odds_spans[i].get_text(strip=True)}
        for i, team_span in enumerate(team_spans)
        if i < len(odds_spans)
    ]
    
    # Split teams into conferences (first half = NFC, second half = AFC)
    total_teams = len(teams)
    mid_point = total_teams // 2
    
    conferences = [
        {"conference": "NFC", "teams": teams[:mid_point]},
        {"conference": "AFC", "teams": teams[mid_point:]}
    ]
    
    return {
        "event_type": "conference",
        "conferences": conferences,
        "validation": {
            "expected_conferences": 2,
            "found_conferences": len(conferences),
            "expected_teams_per_conference": 16,
            "total_teams": total_teams
        }
    }

def scrape_division_odds(soup: BeautifulSoup) -> Dict[str, Any]:
    """Scrape division odds with teams grouped by division.
    
    Args:
        soup: BeautifulSoup object of the scraped page
        
    Returns:
        Dictionary with event_type, divisions list, and validation data
    """
    division_titles = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    team_spans = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_spans = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    # Create teams list with bounds checking
    teams = [
        {"team": team_span.get_text(strip=True), "odds": odds_spans[i].get_text(strip=True)}
        for i, team_span in enumerate(team_spans)
        if i < len(odds_spans)
    ]
    
    # Extract division names and create divisions
    divisions = []
    teams_per_division = len(teams) // len(division_titles) if division_titles else 0
    
    for i, title in enumerate(division_titles):
        division_text = title.get_text(strip=True)
        full_division = division_text.split(" - ")[-1]  # Extract "NFC East" from full title
        
        # Parse conference and division
        parts = full_division.split()
        conference = parts[0] if len(parts) >= 2 else full_division
        division = " ".join(parts[1:]) if len(parts) >= 2 else "Unknown"
        
        # Get teams for this division
        start_idx = i * teams_per_division
        end_idx = start_idx + teams_per_division if i < len(division_titles) - 1 else len(teams)
        
        division_teams = teams[start_idx:end_idx]
        if division_teams:
            divisions.append({
                "division": division,
                "conference": conference,
                "teams": division_teams
            })
    
    return {
        "event_type": "division",
        "divisions": divisions,
        "validation": {
            "expected_divisions": 8,
            "found_divisions": len(divisions),
            "expected_teams_per_division": 4,
            "total_teams": len(teams)
        }
    }

def scrape_simple_odds(soup: BeautifulSoup) -> Dict[str, Any]:
    """Fallback scraper for unknown event types.
    
    Args:
        soup: BeautifulSoup object of the scraped page
        
    Returns:
        Dictionary with event_type and teams list (defaults to championship format)
    """
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    teams = [
        {"team": team.get_text(strip=True), "odds": odd.get_text(strip=True)}
        for team, odd in zip(team_elements, odds_elements)
    ]
    
    return {"event_type": "championship", "teams": teams}

class ScraperUI:
    """Main GUI application for selecting and scraping DraftKings odds.
    
    This class provides a simple interface for users to select a sport and tournament,
    scrape the corresponding odds data, and send it to the FastAPI backend.
    
    Attributes:
        root: The main Tkinter window
        sport_var: StringVar for selected sport
        tournament_var: StringVar for selected tournament
        status_label: Label for displaying operation status
    """
    
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the ScraperUI application.
        
        Args:
            root: The main Tkinter window
        """
        self.root = root
        self.root.title("DraftKings Sports Odds Scraper")
        self.root.geometry("400x300")
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Sport selection
        tk.Label(self.root, text="Select Sport:").pack(pady=5)
        self.sport_var = tk.StringVar()
        self.sport_dropdown = ttk.Combobox(
            self.root, textvariable=self.sport_var, state="readonly"
        )
        self.sport_dropdown["values"] = list(CONFIG.keys())
        self.sport_dropdown.pack(pady=5)
        self.sport_dropdown.bind("<<ComboboxSelected>>", self.update_tournaments)

        # Tournament selection
        tk.Label(self.root, text="Select Tournament:").pack(pady=5)
        self.tournament_var = tk.StringVar()
        self.tournament_dropdown = ttk.Combobox(
            self.root, textvariable=self.tournament_var, state="readonly"
        )
        self.tournament_dropdown.pack(pady=5)

        # Action button
        self.go_button = tk.Button(self.root, text="Scrape & Send", command=self.scrape_and_send)
        self.go_button.pack(pady=10)

        # Status display
        self.status_label = tk.Label(self.root, text="", wraplength=350)
        self.status_label.pack(pady=10)

    def update_tournaments(self, event: tk.Event) -> None:
        """Update tournament dropdown when sport selection changes.
        
        Args:
            event: Tkinter event object (unused but required by bind)
        """
        sport = self.sport_var.get()
        if sport in CONFIG:
            self.tournament_dropdown["values"] = list(CONFIG[sport].keys())
            self.tournament_var.set("")  # Reset tournament selection

    def scrape_and_send(self) -> None:
        """Scrape odds data and send to the FastAPI backend.
        
        Handles the complete workflow: validation, scraping, and API communication.
        Updates the UI with progress and results.
        """
        sport = self.sport_var.get()
        tournament = self.tournament_var.get()

        if not sport or not tournament:
            messagebox.showerror("Error", "Please select a sport and tournament.")
            return

        try:
            config = CONFIG[sport][tournament]
            url = config["url"]
            endpoint = config["endpoint"]
            event_type = config["event_type"]

            # Scrape data
            self.status_label.config(text="Scraping data...")
            self.root.update()
            results = scrape_odds(url, event_type)
            
            print(f"Scraped {event_type} data: {results}")

            # Send to endpoint
            response = requests.post(endpoint, json=results)
            if response.status_code == 200:
                response_data = response.json()
                total_teams = response_data.get("total_teams", 0)
                event_type = response_data.get("event_type", "unknown")
                self.status_label.config(
                    text=f"Success! Data sent to {endpoint}\n"
                         f"Event Type: {event_type}\nTotal Teams: {total_teams}"
                )
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                print(f"API Error: {error_msg}")
                self.status_label.config(
                    text=f"Error: Failed to send data to {endpoint}\n{error_msg}"
                )
        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to scrape or send data: {str(e)}")

def main() -> None:
    """Main entry point for the application."""
    root = tk.Tk()
    app = ScraperUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()