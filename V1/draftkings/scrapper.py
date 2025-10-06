"""DraftKings Sports Odds Scraper (CLI)

This module scrapes sports odds from DraftKings and posts the data to a FastAPI
backend. It supports multiple sports (NFL, NBA, WNBA) and tournament types
(championship, conference, division). Designed for CLI/cron usage.

Functions:
    scrape_odds: Main scraping function that handles different event types
    scrape_championship_odds: Scrapes flat list of teams for championships
    scrape_conference_odds: Scrapes teams grouped by conference
    scrape_division_odds: Scrapes teams grouped by division
    scrape_simple_odds: Fallback scraper for unknown event types
    run_scraper: Iterate CONFIG and send results to API
"""

import os
import json
import logging
from typing import Dict, List, Any

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime

# Initialize logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("draftkings_scraper")

load_dotenv()

# Base URL for API, configurable via env var
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Configuration for sports, tournaments, URLs, and endpoints
CONFIG = {
    "NFL": {
        "Super Bowl": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl",
            "endpoint": f"{API_BASE_URL}/api/draftkings/nfl/super-bowl",
            "event_type": "championship"
        },
        "Conference Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=conference-winner",
            "endpoint": f"{API_BASE_URL}/api/draftkings/nfl/conference-winner",
            "event_type": "conference"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=division-winner",
            "endpoint": f"{API_BASE_URL}/api/draftkings/nfl/division-winner",
            "event_type": "division"
        }
    },
    
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
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        # Explicit wait for odds buttons to appear
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="button-odds-market-board"]'))
        )
        page_source = driver.page_source
    finally:
        driver.quit()

    soup = BeautifulSoup(page_source, "html.parser")

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

def _post_with_retries(endpoint: str, payload: Dict[str, Any], max_retries: int = 3) -> requests.Response:
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(endpoint, json=payload, timeout=20)
            if response.status_code < 500:
                return response
            logger.warning("Server error %s on attempt %s for %s", response.status_code, attempt, endpoint)
        except Exception as exc:
            last_exc = exc
            logger.warning("Request failed on attempt %s for %s: %s", attempt, endpoint, exc)
    if last_exc:
        raise last_exc
    return response  # type: ignore[name-defined]


def run_scraper() -> None:
    """Loop through all CONFIG items, scrape, and send to API."""
    for sport, tournaments in CONFIG.items():
        for tournament, conf in tournaments.items():
            url = conf["url"]
            endpoint = conf["endpoint"]
            event_type = conf["event_type"]
            logger.info("Scraping %s - %s", sport, tournament)
            try:
                results = scrape_odds(url, event_type)
                logger.info("Scraped %s items for %s - %s", (
                    len(results.get("teams", []))
                    if event_type == "championship"
                    else sum(len(c.get("teams", [])) for c in results.get("conferences", []))
                    if event_type == "conference"
                    else sum(len(d.get("teams", [])) for d in results.get("divisions", []))
                ), sport, tournament)

                # Save to JSON for inspection
                save_dir = os.path.join(os.getcwd(), "scrapes")
                os.makedirs(save_dir, exist_ok=True)
                timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                safe_sport = sport.lower().replace(" ", "-")
                safe_tournament = tournament.lower().replace(" ", "-")
                file_path = os.path.join(save_dir, f"draftkings_{safe_sport}_{safe_tournament}_{timestamp}.json")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "provider": "draftkings",
                        "sport": sport,
                        "tournament": tournament,
                        "event_type": event_type,
                        "data": results
                    }, f, ensure_ascii=False, indent=2)
                logger.info("Saved scrape to %s", file_path)

                response = _post_with_retries(endpoint, results)
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Posted to %s | event=%s total_teams=%s", endpoint, data.get("event_type"), data.get("total_teams"))
                else:
                    logger.error("Failed POST to %s | status=%s body=%s", endpoint, response.status_code, response.text)
            except Exception as exc:
                logger.exception("Failed processing %s - %s: %s", sport, tournament, exc)


if __name__ == "__main__":
    run_scraper()