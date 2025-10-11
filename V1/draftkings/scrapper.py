"""DraftKings Sports Odds Scraper (CLI)

<<<<<<< HEAD
This module scrapes sports odds from DraftKings and posts the data to the new
CLM API backend. It supports multiple sports and tournament types.
Designed for CLI/cron usage on Windows Server 2012.
=======
This module scrapes sports odds from DraftKings and posts the data to a FastAPI
backend. It supports multiple sports (NFL, NBA, WNBA) and tournament types
(championship, conference, division). Designed for CLI/cron usage.
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c

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
<<<<<<< HEAD
from typing import Dict, List, Any, Optional
from datetime import datetime
=======
from typing import Dict, List, Any
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
<<<<<<< HEAD
from selenium.webdriver.chrome.service import Service
=======
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
<<<<<<< HEAD
from pydantic import BaseModel
from webdriver_manager.chrome import ChromeDriverManager
=======
from datetime import datetime
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c

# Initialize logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("draftkings_scraper")

load_dotenv()

# Base URL for API, configurable via env var
<<<<<<< HEAD
API_BASE_URL = os.getenv("API_BASE_URL", "https://clmapi.sportsfanwagers.com")

# Pydantic models for the new API structure
class GameValuesTNT(BaseModel):
    Id: int
    TeamName: str
    Odds: str

class GameData(BaseModel):
    IdSport: str = "TNT"
    IdLeague: int
    IdGameType: int
    GameDateTime: str
    VisitorNumber: int = 1
    HomeNumber: int = 2
    VisitorTeam: str
    HomeTeam: str
    VisitorScore: int = 0
    HomeScore: int = 0
    VisitorPitcher: str = ""
    HomePitcher: str = ""
    NormalGame: int = 0
    GameStat: str = "D"
    Graded: bool = False
    Hookups: bool = False
    Local: bool = True
    Online: bool = True
    ShortGame: bool = False
    EventDate: str
    DateChanged: bool = False
    YimeChanged: bool = False
    PitcherChanged: int = 0
    Period: int = 0
    ParentGame: int = 0
    GradedDate: Optional[str] = None
    NumTeams: int
    IdEvent: int = 0
    FamilyGame: int = 0
    HasChildren: bool = False
    IdTeamVisitor: int = 0
    IdTeamHome: int = 0
    IdBannerType: int = 0
    Description: str
    AcceptAutoChanges: bool = True
    IdUser: int = 360
    Result: int = 0
    TournamentType: int = 1
    TournamentPlacestoPaid: str = "1"

# Configuration for sports, tournaments, URLs, leagues, and game types
=======
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Configuration for sports, tournaments, URLs, and endpoints
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
CONFIG = {
    "NFL": {
        "Super Bowl": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl",
<<<<<<< HEAD
            "event_type": "championship",
            "id_league": 3101,  # NFL League ID
            "id_game_type": 1,   # Championship game type
            "description": "NFL Super Bowl Championship"
        },
        "Conference Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=conference-winner",
            "event_type": "conference",
            "id_league": 3101,  # NFL League ID
            "id_game_type": 2,   # Conference winner game type
            "description": "NFL Conference Winner"
        },
        "Division Winner": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=division-winner",
            "event_type": "division",
            "id_league": 3101,  # NFL League ID
            "id_game_type": 3,   # Division winner game type
            "description": "NFL Division Winner"
        }
    },
    "NBA": {
        "NBA Championship": {
            "url": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=futures&subcategory=nba-championship",
            "event_type": "championship",
            "id_league": 3102,  # NBA League ID (example)
            "id_game_type": 1,   # Championship game type
            "description": "NBA Championship"
        }
    }
=======
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
    
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
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
<<<<<<< HEAD
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Use webdriver-manager for Windows Server 2012 compatibility
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as exc:
        logger.warning("Failed to use webdriver-manager, trying default Chrome driver: %s", exc)
        driver = webdriver.Chrome(options=chrome_options)
=======
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
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

<<<<<<< HEAD
def create_game(game_data: GameData) -> Optional[int]:
    """Create a game in the CLM API and return the game ID.
    
    Args:
        game_data: GameData object containing game information
        
    Returns:
        Game ID if successful, None if failed
    """
    endpoint = f"{API_BASE_URL}/api/Game/InsertGame"
    
    try:
        response = requests.post(endpoint, json=game_data.model_dump(), timeout=30)
        if response.status_code == 200:
            result = response.json()
            game_id = result.get("idGame") or result.get("IdGame")
            logger.info("Created game with ID: %s", game_id)
            return game_id
        else:
            logger.error("Failed to create game: %s - %s", response.status_code, response.text)
            return None
    except Exception as exc:
        logger.exception("Exception creating game: %s", exc)
        return None

def submit_game_odds(game_id: int, teams_data: List[Dict[str, Any]]) -> bool:
    """Submit odds for a game to the CLM API.
    
    Args:
        game_id: The ID of the game to submit odds for
        teams_data: List of team data with odds
        
    Returns:
        True if successful, False otherwise
    """
    endpoint = f"{API_BASE_URL}/api/Game/InsertGameValuesTNT?idGame={game_id}"
    
    # Convert teams data to GameValuesTNT format
    game_values = []
    for i, team in enumerate(teams_data, 1):
        game_values.append({
            "Id": i,
            "TeamName": team["team"],
            "Odds": team["odds"]
        })
    
    try:
        response = requests.post(endpoint, json=game_values, timeout=30)
        if response.status_code == 200:
            logger.info("Successfully submitted odds for game %s with %s teams", game_id, len(game_values))
            return True
        else:
            logger.error("Failed to submit odds for game %s: %s - %s", game_id, response.status_code, response.text)
            return False
    except Exception as exc:
        logger.exception("Exception submitting odds for game %s: %s", game_id, exc)
        return False

=======
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
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
<<<<<<< HEAD
    """Loop through all CONFIG items, scrape, create games, and submit odds to CLM API."""
    for sport, tournaments in CONFIG.items():
        for tournament, conf in tournaments.items():
            url = conf["url"]
            event_type = conf["event_type"]
            id_league = conf["id_league"]
            id_game_type = conf["id_game_type"]
            description = conf["description"]
            
            logger.info("Scraping %s - %s", sport, tournament)
            try:
                # Scrape the odds data
                results = scrape_odds(url, event_type)
                
                # Extract teams data based on event type
                teams_data = []
                if event_type == "championship":
                    teams_data = results.get("teams", [])
                elif event_type == "conference":
                    for conf_data in results.get("conferences", []):
                        teams_data.extend(conf_data.get("teams", []))
                elif event_type == "division":
                    for div_data in results.get("divisions", []):
                        teams_data.extend(div_data.get("teams", []))
                
                num_teams = len(teams_data)
                logger.info("Scraped %s teams for %s - %s", num_teams, sport, tournament)
                
                if num_teams == 0:
                    logger.warning("No teams found for %s - %s, skipping", sport, tournament)
                    continue
                
                # Create game data
                current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
                game_data = GameData(
                    IdLeague=id_league,
                    IdGameType=id_game_type,
                    GameDateTime=current_time,
                    VisitorTeam=teams_data[0]["team"] if teams_data else "Unknown",
                    HomeTeam=teams_data[1]["team"] if len(teams_data) > 1 else "Unknown",
                    EventDate=current_time,
                    NumTeams=num_teams,
                    Description=description
                )
                
                # Create the game
                game_id = create_game(game_data)
                if not game_id:
                    logger.error("Failed to create game for %s - %s", sport, tournament)
                    continue
                
                # Submit the odds
                success = submit_game_odds(game_id, teams_data)
                if success:
                    logger.info("Successfully processed %s - %s with game ID %s", sport, tournament, game_id)
                else:
                    logger.error("Failed to submit odds for %s - %s", sport, tournament)
                
=======
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

>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
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
<<<<<<< HEAD
                        "game_id": game_id,
                        "data": results
                    }, f, ensure_ascii=False, indent=2)
                logger.info("Saved scrape to %s", file_path)
                
=======
                        "data": results
                    }, f, ensure_ascii=False, indent=2)
                logger.info("Saved scrape to %s", file_path)

                response = _post_with_retries(endpoint, results)
                if response.status_code == 200:
                    data = response.json()
                    logger.info("Posted to %s | event=%s total_teams=%s", endpoint, data.get("event_type"), data.get("total_teams"))
                else:
                    logger.error("Failed POST to %s | status=%s body=%s", endpoint, response.status_code, response.text)
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
            except Exception as exc:
                logger.exception("Failed processing %s - %s: %s", sport, tournament, exc)


<<<<<<< HEAD
def test_payload_generation():
    """Test function to generate both API payloads without calling endpoints.
    
    This function creates sample data and generates the payloads for both endpoints:
    1. InsertGame - Creates the game data payload
    2. InsertGameValuesTNT - Creates the odds data payload
    
    Returns:
        Dictionary containing both payloads and validation info
    """
    print("=" * 60)
    print("TESTING PAYLOAD GENERATION")
    print("=" * 60)
    
    # Sample scraped data (simulating what would come from DraftKings)
    sample_teams_data = [
        {"team": "Kansas City Chiefs", "odds": "+1500"},
        {"team": "Buffalo Bills", "odds": "-1800"},
        {"team": "Baltimore Ravens", "odds": "-2800"},
        {"team": "Miami Dolphins", "odds": "+1200"},
        {"team": "Cincinnati Bengals", "odds": "+800"}
    ]
    
    # Configuration for NFL Super Bowl
    sport_config = {
        "sport": "NFL",
        "tournament": "Super Bowl",
        "id_league": 3101,
        "id_game_type": 1,
        "description": "NFL Super Bowl Championship"
    }
    
    print(f"\n1. SAMPLE DATA:")
    print(f"   Sport: {sport_config['sport']}")
    print(f"   Tournament: {sport_config['tournament']}")
    print(f"   Teams found: {len(sample_teams_data)}")
    print(f"   Teams: {[team['team'] for team in sample_teams_data]}")
    
    # Generate current timestamp
    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
    
    print(f"\n2. GENERATING GAME CREATION PAYLOAD (InsertGame):")
    print("-" * 50)
    
    # Create GameData payload
    game_data = GameData(
        IdLeague=sport_config["id_league"],
        IdGameType=sport_config["id_game_type"],
        GameDateTime=current_time,
        VisitorTeam=sample_teams_data[0]["team"],
        HomeTeam=sample_teams_data[1]["team"] if len(sample_teams_data) > 1 else "Unknown",
        EventDate=current_time,
        NumTeams=len(sample_teams_data),
        Description=sport_config["description"]
    )
    
    # Convert to dict for display
    game_payload = game_data.model_dump()
    
    print("PAYLOAD STRUCTURE:")
    print(json.dumps(game_payload, indent=2, ensure_ascii=False))
    
    print(f"\n3. GENERATING ODDS PAYLOAD (InsertGameValuesTNT):")
    print("-" * 50)
    
    # Create GameValuesTNT payload
    game_values = []
    for i, team in enumerate(sample_teams_data, 1):
        game_values.append({
            "Id": i,
            "TeamName": team["team"],
            "Odds": team["odds"]
        })
    
    print("PAYLOAD STRUCTURE:")
    print(json.dumps(game_values, indent=2, ensure_ascii=False))
    
    print(f"\n4. VALIDATION SUMMARY:")
    print("-" * 50)
    
    # Validate GameData payload
    validation_results = {
        "game_creation": {
            "IdSport": game_payload["IdSport"] == "TNT",
            "IdLeague": game_payload["IdLeague"] == sport_config["id_league"],
            "IdGameType": game_payload["IdGameType"] == sport_config["id_game_type"],
            "GameStat": game_payload["GameStat"] == "D",
            "VisitorNumber": game_payload["VisitorNumber"] == 1,
            "HomeNumber": game_payload["HomeNumber"] == 2,
            "VisitorScore": game_payload["VisitorScore"] == 0,
            "HomeScore": game_payload["HomeScore"] == 0,
            "Period": game_payload["Period"] == 0,
            "NumTeams": game_payload["NumTeams"] == len(sample_teams_data),
            "TournamentType": game_payload["TournamentType"] == 1,
            "TournamentPlacestoPaid": game_payload["TournamentPlacestoPaid"] == "1",
            "IdUser": game_payload["IdUser"] == 360,
            "Description": game_payload["Description"] == sport_config["description"]
        },
        "odds_submission": {
            "correct_structure": all("Id" in item and "TeamName" in item and "Odds" in item for item in game_values),
            "sequential_ids": all(item["Id"] == i+1 for i, item in enumerate(game_values)),
            "team_count": len(game_values) == len(sample_teams_data)
        }
    }
    
    print("GAME CREATION PAYLOAD VALIDATION:")
    for field, is_valid in validation_results["game_creation"].items():
        status = "✓" if is_valid else "✗"
        print(f"   {status} {field}: {is_valid}")
    
    print("\nODDS SUBMISSION PAYLOAD VALIDATION:")
    for field, is_valid in validation_results["odds_submission"].items():
        status = "✓" if is_valid else "✗"
        print(f"   {status} {field}: {is_valid}")
    
    print(f"\n5. ENDPOINT URLS:")
    print("-" * 50)
    print(f"Game Creation: {API_BASE_URL}/api/Game/InsertGame")
    print(f"Odds Submission: {API_BASE_URL}/api/Game/InsertGameValuesTNT?idGame=<GAME_ID>")
    
    print(f"\n6. NEXT STEPS:")
    print("-" * 50)
    print("1. Review the payload structures above")
    print("2. Verify all required fields are present and correct")
    print("3. Test with actual API endpoints when ready")
    print("4. Check SQL for game types if needed")
    
    return {
        "game_creation_payload": game_payload,
        "odds_submission_payload": game_values,
        "validation_results": validation_results,
        "sample_data": sample_teams_data,
        "config": sport_config
    }


if __name__ == "__main__":
    # Uncomment the line below to test payload generation
    test_payload_generation()
    
    # Uncomment the line below to run the actual scraper
    # run_scraper()
=======
if __name__ == "__main__":
    run_scraper()
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
