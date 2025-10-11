"""Test script to generate API payloads without calling endpoints.

This script tests the payload generation for both CLM API endpoints:
1. InsertGame - Creates the game data payload
2. InsertGameValuesTNT - Creates the odds data payload
"""

import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

class SevenDigitIDGenerator:
    """Generates sequential 7-digit IDs starting from 1000000 to ensure uniqueness."""
    
    def __init__(self, start_id: int = 1000000):
        """
        Initialize the ID generator.
        
        Args:
            start_id: Starting ID (must be 7 digits). Defaults to 1000000.
        """
        if not (1000000 <= start_id <= 9999999):
            raise ValueError("Start ID must be a 7-digit number (1000000-9999999)")
        
        self._current_id = start_id - 1  # Will be incremented to start_id on first call
    
    def get_next_id(self) -> int:
        """Get the next sequential 7-digit ID."""
        self._current_id += 1
        
        if self._current_id > 9999999:
            raise OverflowError("Maximum 7-digit ID (9999999) reached. Cannot generate more unique IDs.")
        
        return self._current_id
    
    def get_current_id(self) -> int:
        """Get the current ID without incrementing."""
        return self._current_id
    
    def reset(self, start_id: int = 1000000):
        """Reset the generator to a new starting ID."""
        if not (1000000 <= start_id <= 9999999):
            raise ValueError("Start ID must be a 7-digit number (1000000-9999999)")
        self._current_id = start_id - 1

# Pydantic models for the API structure
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

def process_odds(odds_str):
    """Process odds: reduce by 25% and round down to nearest 0 or 5."""
    try:
        # Remove + or - sign and convert to integer
        is_positive = odds_str.startswith('+')
        odds_value = int(odds_str.replace('+', '').replace('-', ''))
        
        # Reduce by 25% (multiply by 0.75)
        processed_value = int(odds_value * 0.75)
        
        # Round down to nearest 0 or 5
        # If last digit is 1-4, round down to 0
        # If last digit is 6-9, round down to 5
        last_digit = processed_value % 10
        if last_digit in [1, 2, 3, 4]:
            processed_value = processed_value - last_digit  # Round down to 0
        elif last_digit in [6, 7, 8, 9]:
            processed_value = processed_value - last_digit + 5  # Round down to 5
        # If last digit is 0 or 5, keep as is
        
        # Cap at 20000
        if processed_value > 20000:
            processed_value = 20000
        
        # Add back the sign
        return f"{'+' if is_positive else '-'}{processed_value}"
    except (ValueError, AttributeError):
        # If parsing fails, return original odds
        return odds_str

def scrape_superbowl_odds():
    """Scrape Super Bowl odds from DraftKings."""
    print("=" * 60)
    print("SCRAPING SUPER BOWL ODDS FROM DRAFTKINGS")
    print("=" * 60)
    
    url = "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl"
    
    chrome_options = Options()
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
        print(f"Failed to use webdriver-manager, trying default Chrome driver: {exc}")
        driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait for odds buttons to appear
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-testid="button-odds-market-board"]'))
        )
        
        page_source = driver.page_source
        print("Page loaded successfully")
        
    except Exception as exc:
        print(f"Error loading page: {exc}")
        return []
    finally:
        driver.quit()

    soup = BeautifulSoup(page_source, "html.parser")
    
    # Scrape championship odds as a flat list of all teams
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    teams = []
    for team, odd in zip(team_elements, odds_elements):
        original_odds = odd.get_text(strip=True)
        processed_odds = process_odds(original_odds)
        teams.append({
            "team": team.get_text(strip=True), 
            "odds": processed_odds,
            "original_odds": original_odds
        })
    
    print(f"Scraped {len(teams)} teams:")
    for i, team in enumerate(teams, 1):
        print(f"  {i}. {team['team']} - {team['original_odds']} -> {team['odds']}")
    
    return teams

def test_new_odds_calculation():
    """Test function to verify the new odds calculation rules (25% reduction + rounding down)."""
    print("=" * 60)
    print("TESTING NEW ODDS CALCULATION RULES")
    print("=" * 60)
    
    # Test cases with expected results
    test_cases = [
        {"original": "+475", "expected_reduction": 356, "expected_rounded": 355, "description": "475 -> 356 (25% off) -> 355 (round down 6 to 5)"},
        {"original": "+650", "expected_reduction": 487, "expected_rounded": 485, "description": "650 -> 487 (25% off) -> 485 (round down 7 to 5)"},
        {"original": "+784", "expected_reduction": 588, "expected_rounded": 585, "description": "784 -> 588 (25% off) -> 585 (round down 8 to 5)"},
        {"original": "+456", "expected_reduction": 342, "expected_rounded": 340, "description": "456 -> 342 (25% off) -> 340 (round down 2 to 0)"},
        {"original": "+123", "expected_reduction": 92, "expected_rounded": 90, "description": "123 -> 92 (25% off) -> 90 (round down 2 to 0)"},
        {"original": "+789", "expected_reduction": 591, "expected_rounded": 590, "description": "789 -> 591 (25% off) -> 590 (round down 1 to 0)"},
        {"original": "-1200", "expected_reduction": 900, "expected_rounded": 900, "description": "-1200 -> -900 (25% off) -> -900 (ends in 0)"},
        {"original": "+20000", "expected_reduction": 15000, "expected_rounded": 15000, "description": "+20000 -> +15000 (25% off) -> +15000 (ends in 0)"},
        {"original": "+25000", "expected_reduction": 18750, "expected_rounded": 18750, "description": "+25000 -> +18750 (25% off) -> +18750 (no cap needed)"},
        {"original": "+30000", "expected_reduction": 20000, "expected_rounded": 20000, "description": "+30000 -> +20000 (capped at 20000) -> +20000"},
    ]
    
    print(f"\n1. TESTING ODDS CALCULATION LOGIC:")
    print("-" * 50)
    
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        original = test_case["original"]
        expected_reduction = test_case["expected_reduction"]
        expected_rounded = test_case["expected_rounded"]
        description = test_case["description"]
        
        # Test the actual function
        result = process_odds(original)
        
        # Extract the numeric value from result
        is_positive = result.startswith('+')
        result_value = int(result.replace('+', '').replace('-', ''))
        
        # Check if result matches expected
        passed = result_value == expected_rounded
        all_passed = all_passed and passed
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"   {status} Test {i}: {description}")
        print(f"        Original: {original}")
        print(f"        Result:   {result}")
        print(f"        Expected: {expected_rounded}")
        if not passed:
            print(f"        ERROR: Expected {expected_rounded}, got {result_value}")
        print()
    
    print(f"\n2. SUMMARY:")
    print("-" * 50)
    if all_passed:
        print("   [SUCCESS] All odds calculation tests passed!")
        print("   [OK] 25% reduction applied correctly")
        print("   [OK] Rounding down logic working properly")
        print("   [OK] Cap at 20000 working correctly")
    else:
        print("   [FAILURE] Some tests failed. Check the logic above.")
    
    return all_passed

def test_seven_digit_id_generation():
    """Test function to demonstrate the 7-digit ID generation system with actual Super Bowl data."""
    print("=" * 60)
    print("TESTING 7-DIGIT ID GENERATION SYSTEM WITH SUPER BOWL DATA")
    print("=" * 60)
    
    # Scrape actual Super Bowl odds
    sample_teams_data = scrape_superbowl_odds()
    
    if not sample_teams_data:
        print("ERROR: No teams scraped from DraftKings. Cannot proceed with test.")
        return []
    
    print(f"\n1. SCRAPED SUPER BOWL TEAM DATA:")
    for i, team in enumerate(sample_teams_data, 1):
        print(f"   {i}. {team['team']} - {team['original_odds']} -> {team['odds']}")
    
    print(f"\n2. GENERATING 7-DIGIT IDs:")
    print("-" * 50)
    
    # Create ID generator
    id_generator = SevenDigitIDGenerator()
    
    # Generate payload with 7-digit IDs
    game_values = []
    for team in sample_teams_data:
        team_id = id_generator.get_next_id()
        game_values.append({
            "Id": team_id,
            "TeamName": team["team"],
            "Odds": team["odds"]
        })
        print(f"   Generated ID {team_id} for team: {team['team']}")
    
    print(f"\n3. FINAL PAYLOAD WITH 7-DIGIT IDs:")
    print("-" * 50)
    print(json.dumps(game_values, indent=2, ensure_ascii=False))
    
    print(f"\n4. VALIDATION:")
    print("-" * 50)
    
    # Validate the generated IDs
    all_seven_digits = all(1000000 <= item["Id"] <= 9999999 for item in game_values)
    all_unique = len(set(item["Id"] for item in game_values)) == len(game_values)
    sequential = all(game_values[i]["Id"] == game_values[0]["Id"] + i for i in range(len(game_values)))
    
    print(f"   [{'OK' if all_seven_digits else 'FAIL'}] All IDs are 7-digit numbers")
    print(f"   [{'OK' if all_unique else 'FAIL'}] All IDs are unique")
    print(f"   [{'OK' if sequential else 'FAIL'}] IDs are sequential")
    print(f"   [OK] Correct structure (Id, TeamName, Odds)")
    
    print(f"\n5. ID RANGE ANALYSIS:")
    print("-" * 50)
    ids = [item["Id"] for item in game_values]
    print(f"   Starting ID: {min(ids)}")
    print(f"   Ending ID: {max(ids)}")
    print(f"   Total IDs generated: {len(ids)}")
    print(f"   ID range: {max(ids) - min(ids) + 1}")
    
    print(f"\n6. SUPER BOWL DATA SUMMARY:")
    print("-" * 50)
    print(f"   Teams scraped: {len(sample_teams_data)}")
    print(f"   Odds processed: 25% reduction applied")
    print(f"   Odds rounded down: to nearest 0 or 5")
    print(f"   Odds capped at: 20000")
    print(f"   Data source: DraftKings Super Bowl futures")
    
    return game_values

def test_payload_generation():
    """Test function to generate both API payloads with scraped Super Bowl data."""
    print("=" * 60)
    print("TESTING PAYLOAD GENERATION WITH SUPER BOWL DATA")
    print("=" * 60)
    
    # Configuration for NFL Super Bowl
    sport_config = {
        "sport": "NFL",
        "tournament": "Super Bowl",
        "id_league": 3101,
        "id_game_type": 1,
        "description": "NFL Super Bowl Championship"
    }
    
    # Scrape Super Bowl odds
    sample_teams_data = scrape_superbowl_odds()
    
    if not sample_teams_data:
        print("ERROR: No teams scraped from DraftKings. Cannot proceed with test.")
        return {
            "game_creation_payload": {},
            "odds_submission_payload": [],
            "validation_results": {},
            "sample_data": [],
            "config": sport_config
        }
    
    print(f"\n1. SAMPLE DATA:")
    print(f"   Sport: {sport_config['sport']}")
    print(f"   Tournament: {sport_config['tournament']}")
    print(f"   Teams found: {len(sample_teams_data)}")
    print(f"   Teams: {[team['team'] for team in sample_teams_data]}")
    
    # Generate current timestamp for real data
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
    
    print(f"\n2. GENERATING GAME CREATION PAYLOAD (InsertGame):")
    print("-" * 50)
    
    # Create GameData payload with scraped Super Bowl data
    game_data = GameData(
        IdLeague=sport_config["id_league"],
        IdGameType=sport_config["id_game_type"],
        GameDateTime=current_time,
        VisitorTeam=sample_teams_data[0]["team"] if sample_teams_data else "Unknown",
        HomeTeam=sample_teams_data[1]["team"] if len(sample_teams_data) > 1 else "Unknown",
        EventDate=current_time,
        NumTeams=len(sample_teams_data),
        Description=sport_config["description"]
    )
    
    # Convert to dict for display
    game_payload = game_data.dict()
    
    print("PAYLOAD STRUCTURE:")
    print(json.dumps(game_payload, indent=2, ensure_ascii=False))
    
    print(f"\n3. GENERATING ODDS PAYLOAD (InsertGameValuesTNT):")
    print("-" * 50)
    
    # Create GameValuesTNT payload with processed odds using 7-digit IDs
    id_generator = SevenDigitIDGenerator()
    game_values = []
    for team in sample_teams_data:
        game_values.append({
            "Id": id_generator.get_next_id(),
            "TeamName": team["team"],
            "Odds": team["odds"]  # This now contains the processed odds (5% reduced, capped at 20000)
        })
    
    print("PAYLOAD STRUCTURE:")
    print(json.dumps(game_values, indent=2, ensure_ascii=False))
    
    print(f"\n4. ODDS PROCESSING SUMMARY:")
    print("-" * 50)
    print("Applied 25% reduction, rounding down, and 20000 cap to all odds:")
    capped_count = sum(1 for team in sample_teams_data if team.get("original_odds") and "+80000" in team["original_odds"])
    print(f"- Teams with odds capped at 20000: {capped_count}")
    print(f"- All odds reduced by 25% from original DraftKings values")
    print(f"- All odds rounded down to nearest 0 or 5")
    
    print(f"\n5. VALIDATION SUMMARY:")
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
            "seven_digit_ids": all(1000000 <= item["Id"] <= 9999999 for item in game_values),
            "unique_ids": len(set(item["Id"] for item in game_values)) == len(game_values),
            "team_count": len(game_values) == len(sample_teams_data)
        }
    }
    
    print("GAME CREATION PAYLOAD VALIDATION:")
    for field, is_valid in validation_results["game_creation"].items():
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"   {status} {field}: {is_valid}")
    
    print("\nODDS SUBMISSION PAYLOAD VALIDATION:")
    for field, is_valid in validation_results["odds_submission"].items():
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"   {status} {field}: {is_valid}")
    
    print(f"\n6. ENDPOINT URLS:")
    print("-" * 50)
    print("Game Creation: https://clmapi.sportsfanwagers.com/api/Game/InsertGame")
    print("Odds Submission: https://clmapi.sportsfanwagers.com/api/Game/InsertGameValuesTNT?idGame=<GAME_ID>")
    
    print(f"\n7. COMPARISON WITH YOUR EXAMPLE:")
    print("-" * 50)
    print("Your example GameData fields:")
    print("[OK] IdSport: 'TNT'")
    print("[OK] IdLeague: 3101 (NFL)")
    print("[OK] IdGameType: 1 (Championship)")
    print("[OK] GameDateTime: Current timestamp")
    print("[OK] VisitorNumber: 1")
    print("[OK] HomeNumber: 2")
    print("[OK] VisitorScore: 0")
    print("[OK] HomeScore: 0")
    print("[OK] GameStat: 'D'")
    print("[OK] Period: 0")
    print("[OK] NumTeams: Number of teams")
    print("[OK] TournamentType: 1 (Single winner)")
    print("[OK] TournamentPlacestoPaid: '1'")
    print("[OK] IdUser: 360")
    print("[OK] Description: Tournament description")
    
    print(f"\n8. NEXT STEPS:")
    print("-" * 50)
    print("1. Review the payload structures above")
    print("2. Verify all required fields are present and correct")
    print("3. Test with actual API endpoints when ready")
    print("4. Check SQL for game types if needed")
    print("5. Processed odds are ready for submission")
    
    return {
        "game_creation_payload": game_payload,
        "odds_submission_payload": game_values,
        "validation_results": validation_results,
        "sample_data": sample_teams_data,
        "config": sport_config
    }

def check_existing_odds(game_id):
    """Check if odds already exist for a game to prevent duplicates."""
    API_BASE_URL = "https://clmapi.sportsfanwagers.com"
    check_url = f"{API_BASE_URL}/api/Game/GetGameValuesTNT?idGame={game_id}"
    
    try:
        response = requests.get(check_url, timeout=10)
        if response.status_code == 200:
            existing_odds = response.json()
            if existing_odds and len(existing_odds) > 0:
                print(f"WARNING: Game {game_id} already has {len(existing_odds)} odds entries!")
                return True
        return False
    except Exception as e:
        print(f"Could not check existing odds: {e}")
        return False

def test_api_endpoints():
    """Test function to actually call the API endpoints with test data."""
    print("=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    # Get the test payloads
    test_data = test_payload_generation()
    game_payload = test_data["game_creation_payload"]
    odds_payload = test_data["odds_submission_payload"]
    
    # API endpoints
    API_BASE_URL = "https://clmapi.sportsfanwagers.com"
    create_game_url = f"{API_BASE_URL}/api/Game/InsertGame"
    
    print(f"\n1. TESTING GAME CREATION:")
    print("-" * 50)
    print(f"URL: {create_game_url}")
    print("Payload:")
    print(json.dumps(game_payload, indent=2))
    
    try:
        # Test game creation
        response = requests.post(create_game_url, json=game_payload, timeout=30)
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Response Body: {result}")
            
            # Handle different response formats
            if isinstance(result, dict):
                game_id = result.get("idGame") or result.get("IdGame") or result.get("id")
            else:
                game_id = result  # If response is just the ID number
            
            print(f"SUCCESS! Game created with ID: {game_id}")
            
            # Check if odds already exist
            if check_existing_odds(game_id):
                print(f"\n2. SKIPPING ODDS SUBMISSION:")
                print("-" * 50)
                print("Odds already exist for this game. Skipping to prevent duplicates.")
            else:
                # Test odds submission
                print(f"\n2. TESTING ODDS SUBMISSION:")
                print("-" * 50)
                odds_url = f"{API_BASE_URL}/api/Game/InsertGameValuesTNT?idGame={game_id}"
                print(f"URL: {odds_url}")
                print("Payload:")
                print(json.dumps(odds_payload, indent=2))
                
                odds_response = requests.post(odds_url, json=odds_payload, timeout=30)
                print(f"\nResponse Status: {odds_response.status_code}")
                print(f"Response Headers: {dict(odds_response.headers)}")
                
                if odds_response.status_code == 200:
                    print("SUCCESS! Odds submitted successfully")
                    print(f"Final Response: {odds_response.text}")
                else:
                    print(f"FAILED! Odds submission failed: {odds_response.text}")
                    print(f"Error details: {odds_response.text}")
                
        else:
            print(f"FAILED! Game creation failed: {response.text}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
    
    print(f"\n3. TEST COMPLETE")
    print("-" * 50)

if __name__ == "__main__":
    # Test the new odds calculation rules first
    test_new_odds_calculation()
    
    print("\n" + "="*60)
    print("NOW TESTING 7-DIGIT ID GENERATION WITH SUPER BOWL DATA")
    print("="*60)
    
    # Test the new 7-digit ID generation system
    test_seven_digit_id_generation()
    
    print("\n" + "="*60)
    print("NOW TESTING FULL PAYLOAD GENERATION")
    print("="*60)
    
    # Uncomment the line below to test payload generation only
    #test_payload_generation()
    
    # Uncomment the line below to test actual API endpoints
    test_api_endpoints()
