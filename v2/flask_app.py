from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import time
import random
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import logging
from webdriver_manager.chrome import ChromeDriverManager
import os

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Classes and functions from successful_test.py
class SevenDigitIDGenerator:
    """Generates sequential 7-digit IDs starting from user-specified number."""
    
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

def detect_tournament_name(url, description=""):
    """Detect tournament name from URL or use description."""
    # Common tournament patterns in URLs
    tournament_patterns = {
        'super-bowl': 'Super Bowl',
        'heisman': 'Heisman Trophy',
        'championship': 'Championship',
        'playoff': 'Playoffs',
        'futures': 'Futures',
        'nfl': 'NFL',
        'ncaa': 'NCAA',
        'college': 'College Football',
        'golf': 'Golf Tournament',
        'pga': 'PGA Tournament',
        'masters': 'Masters Tournament',
        'formula-1': 'Formula 1',
        'f1': 'Formula 1',
        'nascar': 'NASCAR',
        'indycar': 'IndyCar',
        'racing': 'Auto Racing'
    }
    
    url_lower = url.lower()
    
    # Check for specific tournament patterns
    for pattern, name in tournament_patterns.items():
        if pattern in url_lower:
            return name
    
    # If description is provided and meaningful, use it
    if description and description != "DraftKings Scraped Data":
        return description
    
    # Default fallback
    return "Tournament"

def extract_grand_prix_name(url, tournament_name):
    """Extract Grand Prix name from URL for auto racing tournaments."""
    url_lower = url.lower()
    
    # Formula 1 Grand Prix patterns
    f1_gp_patterns = {
        'monaco': 'Monaco Grand Prix',
        'silverstone': 'British Grand Prix',
        'spa': 'Belgian Grand Prix',
        'monza': 'Italian Grand Prix',
        'spain': 'Spanish Grand Prix',
        'france': 'French Grand Prix',
        'austria': 'Austrian Grand Prix',
        'hungary': 'Hungarian Grand Prix',
        'belgium': 'Belgian Grand Prix',
        'netherlands': 'Dutch Grand Prix',
        'singapore': 'Singapore Grand Prix',
        'japan': 'Japanese Grand Prix',
        'australia': 'Australian Grand Prix',
        'bahrain': 'Bahrain Grand Prix',
        'saudi': 'Saudi Arabian Grand Prix',
        'qatar': 'Qatar Grand Prix',
        'abu-dhabi': 'Abu Dhabi Grand Prix',
        'miami': 'Miami Grand Prix',
        'las-vegas': 'Las Vegas Grand Prix',
        'brazil': 'Brazilian Grand Prix',
        'mexico': 'Mexican Grand Prix',
        'canada': 'Canadian Grand Prix',
        'azerbaijan': 'Azerbaijan Grand Prix',
        'china': 'Chinese Grand Prix',
        'russia': 'Russian Grand Prix',
        'portugal': 'Portuguese Grand Prix',
        'turkey': 'Turkish Grand Prix',
        'imola': 'Emilia Romagna Grand Prix',
        'emilia': 'Emilia Romagna Grand Prix',
        'romagna': 'Emilia Romagna Grand Prix'
    }
    
    # Check for F1 Grand Prix patterns
    for pattern, gp_name in f1_gp_patterns.items():
        if pattern in url_lower:
            return gp_name
    
    # NASCAR patterns
    nascar_patterns = {
        'daytona': 'Daytona 500',
        'talladega': 'Talladega Superspeedway',
        'bristol': 'Bristol Motor Speedway',
        'martinsville': 'Martinsville Speedway',
        'richmond': 'Richmond Raceway',
        'charlotte': 'Charlotte Motor Speedway',
        'texas': 'Texas Motor Speedway',
        'phoenix': 'Phoenix Raceway',
        'las-vegas': 'Las Vegas Motor Speedway',
        'homestead': 'Homestead-Miami Speedway',
        'atlanta': 'Atlanta Motor Speedway',
        'dover': 'Dover Motor Speedway',
        'kansas': 'Kansas Speedway',
        'kentucky': 'Kentucky Speedway',
        'chicagoland': 'Chicagoland Speedway',
        'pocono': 'Pocono Raceway',
        'watkins-glen': 'Watkins Glen International',
        'sonoma': 'Sonoma Raceway',
        'road-america': 'Road America',
        'indy': 'Indianapolis Motor Speedway'
    }
    
    # Check for NASCAR patterns
    for pattern, race_name in nascar_patterns.items():
        if pattern in url_lower:
            return race_name
    
    # If no specific Grand Prix found, use the tournament name
    return tournament_name

def extract_race_name_from_page(soup, tournament_type):
    """Extract the actual race/event name from the page content."""
    race_name = None
    
    # Common selectors for race/event titles
    title_selectors = [
        '.cb-title__simple-title.cb-title__nav-title',  # DraftKings specific
        '.cb-title__simple-title',
        '.cb-title__nav-title',
        '.title',
        '.event-title',
        '.race-title',
        '.tournament-title',
        'h1',
        'h2',
        '[class*="title"]',
        '[class*="event"]',
        '[class*="race"]'
    ]
    
    logger.info(f"Extracting race name from page for tournament type: {tournament_type}")
    
    for selector in title_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 3:  # Ensure it's meaningful text
                    logger.info(f"Found potential race name: '{text}' using selector: {selector}")
                    
                    # Clean up the text
                    race_name = text.strip()
                    
                    # For auto racing, look for specific patterns
                    if tournament_type == 'auto_racing':
                        # Look for F1, NASCAR, IndyCar patterns
                        if any(term in race_name.lower() for term in ['formula 1', 'f1', 'grand prix', 'gp', 'nascar', 'indycar', 'indy']):
                            logger.info(f"Auto racing race name found: {race_name}")
                            return race_name
                    
                    # For golf, look for tournament patterns
                    elif tournament_type == 'golf':
                        if any(term in race_name.lower() for term in ['masters', 'pga', 'tournament', 'championship', 'open', 'classic']):
                            logger.info(f"Golf tournament name found: {race_name}")
                            return race_name
                    
                    # For other sports, use any meaningful title
                    else:
                        logger.info(f"General race name found: {race_name}")
                        return race_name
                        
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue
    
    logger.warning("No race name found in page content")
    return None

def detect_tournament_type(url):
    """Detect if this is Golf, Auto Racing, or other tournament type."""
    url_lower = url.lower()
    
    # Golf patterns
    golf_patterns = ['golf', 'pga', 'masters', 'us-open', 'british-open', 'pga-championship']
    if any(pattern in url_lower for pattern in golf_patterns):
        return 'golf'
    
    # Auto Racing patterns
    racing_patterns = ['formula-1', 'f1', 'nascar', 'indycar', 'racing', 'auto-racing']
    if any(pattern in url_lower for pattern in racing_patterns):
        return 'auto_racing'
    
    # Default to championship (existing behavior)
    return 'championship'

def detect_betting_lines(soup, tournament_type):
    """Detect available betting lines based on tournament type."""
    lines_found = []
    
    logger.info(f"Detecting betting lines for tournament type: {tournament_type}")
    
    # Look for betting line headers/buttons with more specific selectors
    line_selectors = [
        'button[data-testid*="line"]',
        'span[data-testid*="line"]',
        'button[data-testid*="market"]',
        'span[data-testid*="market"]',
        'button[data-testid*="bet"]',
        'span[data-testid*="bet"]',
        '.line-title',
        '.betting-line',
        '.market-title',
        '.bet-title',
        '[class*="line"]',
        '[class*="bet"]',
        '[class*="market"]',
        'h2', 'h3', 'h4',  # Common headers
        '.title', '.header',  # Common title classes
        'button', 'span'  # Generic buttons and spans
    ]
    
    for selector in line_selectors:
        elements = soup.find_all(selector)
        logger.info(f"Found {len(elements)} elements with selector: {selector}")
        
        for element in elements:
            text = element.get_text(strip=True).lower()
            logger.info(f"Checking text: '{text}'")
            
            # Golf betting lines with more comprehensive matching
            if tournament_type == 'golf':
                if any(term in text for term in ['winner', 'win', 'champion']):
                    lines_found.append('Winner')
                elif any(term in text for term in ['top 5', 'top5', 'top-5']):
                    lines_found.append('Top 5')
                elif any(term in text for term in ['top 10', 'top10', 'top-10']):
                    lines_found.append('Top 10')
                elif any(term in text for term in ['top 3', 'top3', 'top-3', 'podium']):
                    lines_found.append('Top 3')
                elif any(term in text for term in ['top 20', 'top20', 'top-20']):
                    lines_found.append('Top 20')
            
            # Auto Racing betting lines with more comprehensive matching
            elif tournament_type == 'auto_racing':
                if any(term in text for term in ['winner', 'win', 'champion', 'race winner']):
                    lines_found.append('Winner')
                elif any(term in text for term in ['top 2', 'top2', 'top-2', 'podium']):
                    lines_found.append('Top 2')
                elif any(term in text for term in ['top 3', 'top3', 'top-3']):
                    lines_found.append('Top 3')
                elif any(term in text for term in ['top 4', 'top4', 'top-4']):
                    lines_found.append('Top 4')
                elif any(term in text for term in ['top 5', 'top5', 'top-5']):
                    lines_found.append('Top 5')
                elif any(term in text for term in ['top 10', 'top10', 'top-10']):
                    lines_found.append('Top 10')
    
    # If no specific lines found, provide default lines based on tournament type
    if not lines_found:
        logger.info("No specific betting lines detected, using defaults")
        if tournament_type == 'golf':
            lines_found = ['Winner', 'Top 5', 'Top 10']
        elif tournament_type == 'auto_racing':
            lines_found = ['Winner', 'Top 2', 'Top 4']
        else:
            lines_found = ['Winner']
    
    # Remove duplicates and return
    unique_lines = list(set(lines_found))
    logger.info(f"Final betting lines detected: {unique_lines}")
    return unique_lines

def clean_team_name(team_name):
    """Clean team/driver names by removing unwanted prefixes and suffixes."""
    if not team_name:
        return team_name
    
    # Remove common unwanted prefixes
    unwanted_prefixes = [
        'Finish',
        'To Finish',
        'To Win',
        'Winner',
        'Champion',
        'Top',
        'Place',
        'Position',
        'AMRACE Winner',  # Specific to your issue
        'AMRACE',
        'Race Winner',
        'Race',
        'Finish ',  # Handle "Finish Lando Norris" case
        'Finish To',  # Handle "Finish To Win" case
        'Finish Winner',  # Handle "Finish Winner" case
        'Finish Lando',  # Specific fix for "Finish Lando Norris"
        'Finish Max',  # Specific fix for "Finish Max Verstappen"
        'Finish Oscar',  # Specific fix for "Finish Oscar Piastri"
        'Finish George',  # Specific fix for "Finish George Russell"
        'Finish Charles',  # Specific fix for "Finish Charles Leclerc"
        'Finish Lewis',  # Specific fix for "Finish Lewis Hamilton"
    ]
    
    # Remove common unwanted suffixes
    unwanted_suffixes = [
        'Finish',
        'Winner',
        'Champion',
        'To Win',
        'To Finish'
    ]
    
    cleaned_name = team_name.strip()
    
    # Remove prefixes (case insensitive) - try multiple times to catch nested prefixes
    max_iterations = 5  # Increased iterations to handle more complex cases
    for iteration in range(max_iterations):
        original_name = cleaned_name
        for prefix in unwanted_prefixes:
            if cleaned_name.lower().startswith(prefix.lower()):
                cleaned_name = cleaned_name[len(prefix):].strip()
                logger.debug(f"Removed prefix '{prefix}' from '{original_name}' -> '{cleaned_name}'")
                break  # Start over with the new cleaned name
        if cleaned_name == original_name:  # No more prefixes to remove
            break
    
    # Remove suffixes (case insensitive)
    for suffix in unwanted_suffixes:
        if cleaned_name.lower().endswith(suffix.lower()):
            cleaned_name = cleaned_name[:-len(suffix)].strip()
            logger.debug(f"Removed suffix '{suffix}' from '{team_name}' -> '{cleaned_name}'")
    
    # Clean up any extra spaces and special characters
    cleaned_name = ' '.join(cleaned_name.split())
    
    # Remove any remaining unwanted patterns
    unwanted_patterns = [
        r'^Finish\s*',  # Regex for "Finish" or "Finish " at start
        r'\s+Finish$',  # Regex for " Finish" at end
        r'^To\s+Finish\s+',  # Regex for "To Finish " at start
        r'^To\s+Win\s+',  # Regex for "To Win " at start
        r'^AMRace\s+Winner\s*',  # Regex for "AMRace Winner" at start
        r'^AMRACE\s+Winner\s*',  # Regex for "AMRACE Winner" at start
        r'^Race\s+Winner\s*',  # Regex for "Race Winner" at start
    ]
    
    import re
    for pattern in unwanted_patterns:
        cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE).strip()
    
    if cleaned_name != team_name:
        logger.info(f"Cleaned team name: '{team_name}' -> '{cleaned_name}'")
    
    return cleaned_name

def normalize_driver_name(name):
    """Normalize driver names to handle variations like 'AMRace Winner Max Verstappen' vs 'Max Verstappen'."""
    if not name:
        return name
    
    # Clean the name first
    cleaned = clean_team_name(name)
    
    # Common F1 driver names to match against
    f1_drivers = [
        'lando norris', 'max verstappen', 'oscar piastri', 'george russell', 
        'charles leclerc', 'lewis hamilton', 'carlos sainz', 'alexander albon',
        'andrea kimi antonelli', 'isack hadjar', 'fernando alonso', 'sergio perez',
        'valtteri bottas', 'esteban ocon', 'pierre gasly', 'yuki tsunoda',
        'kevin magnussen', 'nico hulkenberg', 'lance stroll', 'logan sargeant'
    ]
    
    # Try to match against known F1 drivers
    cleaned_lower = cleaned.lower()
    for driver in f1_drivers:
        if driver in cleaned_lower:
            # Return the standardized name (first letter capitalized)
            return ' '.join(word.capitalize() for word in driver.split())
    
    # If no match found, return the cleaned name
    return cleaned

def remove_duplicate_drivers(odds_data):
    """Remove duplicate drivers, keeping only the first instance of each driver."""
    seen_drivers = set()
    unique_odds_data = []
    
    for entry in odds_data:
        # Normalize the driver name
        normalized_name = normalize_driver_name(entry.get('team', ''))
        
        # Check if we've seen this driver before
        if normalized_name and normalized_name not in seen_drivers:
            # Update the entry with the normalized name
            entry['team'] = normalized_name
            unique_odds_data.append(entry)
            seen_drivers.add(normalized_name)
            logger.info(f"Added unique driver: {normalized_name}")
        else:
            logger.info(f"Skipping duplicate driver: {normalized_name}")
    
    logger.info(f"Removed {len(odds_data) - len(unique_odds_data)} duplicate drivers")
    return unique_odds_data

def ensure_all_players_have_entries(all_odds_data, betting_lines):
    """Ensure all players have entries for all betting lines, even if they don't have odds for some lines."""
    if not all_odds_data:
        return all_odds_data
    
    # Get all unique players from the data
    all_players = set()
    for entry in all_odds_data:
        all_players.add(entry.get('team', ''))
    
    logger.info(f"Found {len(all_players)} unique players: {list(all_players)}")
    
    # For each betting line, ensure all players have entries
    for line_name in betting_lines:
        logger.info(f"Ensuring all players have entries for {line_name}")
        
        # Get players that already have entries for this line
        existing_players = set()
        for entry in all_odds_data:
            if entry.get('team') in all_players:
                existing_players.add(entry.get('team'))
        
        # Find players missing from this line
        missing_players = all_players - existing_players
        
        if missing_players:
            logger.info(f"Found {len(missing_players)} players missing from {line_name}: {list(missing_players)}")
            
            # Create entries for missing players with empty odds
            for player in missing_players:
                all_odds_data.append({
                    "team": player,
                    "odds": "",  # Empty odds
                    "original_odds": ""  # Empty original odds
                })
                logger.info(f"Created entry for {player} in {line_name} with empty odds")
    
    return all_odds_data

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

def setup_driver(headless=True):
    """Setup Chrome driver with proper options for DraftKings."""
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.warning(f"Failed to use webdriver-manager: {e}")
        driver = webdriver.Chrome(options=options)
    
    return driver

def scrape_draftkings_odds(url, event_type="championship"):
    """Improved DraftKings odds scraper with support for championship, conference, and division events."""
    driver = setup_driver(headless=True)  # Use headless for production
    try:
        logger.info(f"Scraping URL: {url} with event_type: {event_type}")
        driver.get(url)
        
        # Wait for the odds elements to load
        wait = WebDriverWait(driver, 20)
        
        # Try multiple selectors for better compatibility
        selectors_to_try = [
            'span[data-testid="button-title-market-board"]',  # Primary selector
            'span[data-testid="button-odds-market-board"]',   # Odds selector
            '[data-testid="offer-card"]',                     # Fallback
            '.market-board-item',                             # Alternative
            '.sportsbook-table-row'                           # Another alternative
        ]
        
        element_found = False
        for selector in selectors_to_try:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                logger.info(f"Found elements with selector: {selector}")
                element_found = True
                break
            except:
                continue
        
        if not element_found:
            logger.warning("No elements found with any selector")
            return []
        
        # Wait a bit more for dynamic content
        time.sleep(random.uniform(2, 4))
        
        # Parse the HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Route to appropriate scraper based on event type
        if event_type == "conference":
            return scrape_conference_odds(soup)
        elif event_type == "division":
            return scrape_division_odds(soup)
        else:  # championship or unknown
            return scrape_championship_odds(soup)
    
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return []
    
    finally:
        driver.quit()

def scrape_first_tournament_only(soup, tournament_type):
    """Scrape only the first tournament on the page, limiting to first N entries to avoid cross-tournament contamination."""
    odds_data = []
    seen_teams = set()
    
    # Find all tournament division headers
    tournament_headers = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    logger.info(f"Found {len(tournament_headers)} tournament headers on page")
    
    # Get the first tournament name for reference
    first_tournament_name = None
    if tournament_headers:
        first_tournament_name = tournament_headers[0].get_text(strip=True)
        logger.info(f"First tournament: {first_tournament_name}")
    
    # Try multiple selectors to find team and odds elements
    team_elements = []
    odds_elements = []
    
    # Primary selectors (DraftKings specific)
    team_selectors = [
        'span[data-testid="button-title-market-board"]',
        'span[data-testid="button-title"]',
        '[data-testid="button-title-market-board"]',
        '[data-testid="button-title"]'
    ]
    
    odds_selectors = [
        'span[data-testid="button-odds-market-board"]',
        'span[data-testid="button-odds"]',
        '[data-testid="button-odds-market-board"]',
        '[data-testid="button-odds"]'
    ]
    
    # Try to find team elements
    for selector in team_selectors:
        elements = soup.select(selector)
        if elements:
            team_elements = elements
            logger.info(f"Found {len(team_elements)} team elements using selector: {selector}")
            break
    
    # Try to find odds elements
    for selector in odds_selectors:
        elements = soup.select(selector)
        if elements:
            odds_elements = elements
            logger.info(f"Found {len(odds_elements)} odds elements using selector: {selector}")
            break
    
    # Fallback to generic selectors if specific ones don't work
    if not team_elements or not odds_elements:
        logger.info("Trying fallback selectors...")
        
        # Generic selectors
        team_elements = soup.find_all("span", class_=lambda x: x and any(term in x.lower() for term in ['title', 'name', 'team', 'driver']))
        odds_elements = soup.find_all("span", class_=lambda x: x and any(term in x.lower() for term in ['odds', 'price', 'value']))
        
        # If still no elements, try even more generic selectors
        if not team_elements or not odds_elements:
            team_elements = soup.find_all("span", string=lambda text: text and any(char.isdigit() for char in text) and '+' in text)
            odds_elements = soup.find_all("span", string=lambda text: text and any(char.isdigit() for char in text) and '+' in text)
    
    if not team_elements or not odds_elements:
        logger.warning("No team or odds elements found with any selector")
        
        # Debug: Log some information about the page structure
        logger.info("Debugging page structure...")
        all_spans = soup.find_all("span")
        logger.info(f"Total spans on page: {len(all_spans)}")
        
        # Look for any elements with data-testid
        testid_elements = soup.find_all(attrs={"data-testid": True})
        logger.info(f"Elements with data-testid: {len(testid_elements)}")
        
        # Log some sample data-testid values
        for i, element in enumerate(testid_elements[:10]):
            testid = element.get('data-testid', '')
            text = element.get_text(strip=True)[:50]
            logger.info(f"  {i+1}. data-testid='{testid}' text='{text}'")
        
        return []
    
    logger.info(f"Found {len(team_elements)} teams and {len(odds_elements)} odds elements")
    
    # Limit scraping to first tournament only by limiting to first N entries
    # This prevents cross-tournament contamination by stopping before other tournaments
    max_entries = min(len(team_elements), len(odds_elements), 25)  # Limit to first 25 entries
    logger.info(f"Limiting scraping to first {max_entries} entries to avoid cross-tournament contamination")
    
    # Process teams and odds, limiting to first tournament
    for i in range(max_entries):
        if i >= len(team_elements) or i >= len(odds_elements):
            break
            
        team_span = team_elements[i]
        odds_span = odds_elements[i]
        
        team_name = clean_team_name(team_span.get_text(strip=True))
        original_odds = odds_span.get_text(strip=True)
        processed_odds = process_odds(original_odds)
        
        # Additional check: if we encounter a team name that suggests we're in a different tournament
        # (like "Las Vegas GP" or other tournament names), stop scraping
        if any(tournament_indicator in team_name.lower() for tournament_indicator in ['gp', 'grand prix', 'las vegas', 'miami', 'monaco']):
            if i > 5:  # Only stop if we've already scraped some entries
                logger.info(f"Stopping at element {i} - detected different tournament: {team_name}")
                break
        
        # Check for duplicates and add to results
        if team_name and original_odds and team_name not in seen_teams:
            odds_data.append({
                "team": team_name,
                "odds": processed_odds,
                "original_odds": original_odds
            })
            seen_teams.add(team_name)
            logger.info(f"Scraped: {team_name} @ {original_odds} -> {processed_odds}")
        elif team_name in seen_teams:
            logger.info(f"Skipping duplicate: {team_name}")
    
    logger.info(f"Scraped {len(odds_data)} entries from first tournament only")
    return odds_data

def filter_odds_by_betting_line(odds_data, line_name, tournament_type):
    """Filter odds data to only include entries relevant to the specific betting line."""
    if not odds_data:
        return []
    
    filtered_data = []
    
    # Define patterns that should be excluded for each betting line
    exclusion_patterns = {
        'Winner': [],  # Winner gets all data
        'Top 2': ['winner', 'win', 'champion', 'amrace winner', 'race winner', 'amrace'],
        'Top 4': ['winner', 'win', 'champion', 'amrace winner', 'race winner', 'top 2', 'top2', 'podium', 'amrace'],
        'Top 5': ['winner', 'win', 'champion', 'amrace winner', 'race winner', 'top 2', 'top2', 'podium', 'top 4', 'top4', 'amrace'],
        'Top 10': ['winner', 'win', 'champion', 'amrace winner', 'race winner', 'top 2', 'top2', 'podium', 'top 4', 'top4', 'top 5', 'top5', 'amrace']
    }
    
    # Get exclusion patterns for this specific line
    patterns_to_exclude = exclusion_patterns.get(line_name, [])
    
    logger.info(f"Filtering data for {line_name} - excluding patterns: {patterns_to_exclude}")
    
    for entry in odds_data:
        team_name = entry.get('team', '').lower()
        should_exclude = False
        
        # Check if this entry matches any exclusion patterns
        for pattern in patterns_to_exclude:
            if pattern in team_name:
                should_exclude = True
                logger.debug(f"Excluding '{entry.get('team')}' for {line_name} - matches pattern '{pattern}'")
                break
        
        # Additional check: exclude entries that look like they're from different tournaments
        # (like "Las Vegas GP", "Miami GP", etc.)
        if not should_exclude:
            tournament_indicators = ['las vegas', 'miami', 'monaco', 'silverstone', 'spa', 'monza']
            if any(indicator in team_name for indicator in tournament_indicators):
                should_exclude = True
                logger.info(f"Excluding '{entry.get('team')}' for {line_name} - appears to be from different tournament")
        
        if not should_exclude:
            # Check if this player has valid odds for this betting line
            odds_value = entry.get('odds', '')
            original_odds = entry.get('original_odds', '')
            
            # If no odds or invalid odds, create entry with empty odds
            if not odds_value or odds_value == '' or not original_odds or original_odds == '':
                logger.info(f"Player '{entry.get('team')}' has no odds for {line_name}, creating entry with empty odds")
                filtered_data.append({
                    "team": entry.get('team'),
                    "odds": "",  # Empty odds
                    "original_odds": ""  # Empty original odds
                })
            else:
                filtered_data.append(entry)
        else:
            logger.info(f"Filtered out '{entry.get('team')}' from {line_name} tournament")
    
    logger.info(f"Filtered {line_name}: {len(filtered_data)} entries (removed {len(odds_data) - len(filtered_data)} entries)")
    return filtered_data


def scrape_multi_line_tournament(url):
    """Scrape tournament with multiple betting lines (Golf, Auto Racing) and create separate tournaments for each line."""
    driver = setup_driver(headless=True)  # Use headless for better performance
    try:
        logger.info(f"Scraping multi-line tournament: {url}")
        driver.get(url)
        
        # Wait for the odds elements to load
        wait = WebDriverWait(driver, 20)
        
        # Try multiple selectors for better compatibility
        selectors_to_try = [
            'span[data-testid="button-title-market-board"]',
            'span[data-testid="button-odds-market-board"]',
            '[data-testid="offer-card"]',
            '.market-board-item',
            '.sportsbook-table-row'
        ]
        
        element_found = False
        for selector in selectors_to_try:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                logger.info(f"Found elements with selector: {selector}")
                element_found = True
                break
            except:
                continue
        
        if not element_found:
            logger.warning("No elements found with any selector")
            return []
        
        # Wait a bit more for dynamic content
        time.sleep(random.uniform(2, 4))
        
        # Parse the HTML to detect tournament type and betting lines
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Detect tournament type
        tournament_type = detect_tournament_type(url)
        logger.info(f"Detected tournament type: {tournament_type}")
        
        # Extract the actual race name from the page content
        race_name = extract_race_name_from_page(soup, tournament_type)
        if race_name:
            logger.info(f"Extracted race name from page: {race_name}")
        else:
            logger.warning("Could not extract race name from page, will use URL-based detection")
        
        # Use the original working scraping method
        logger.info("Scraping all available data from page")
        all_odds_data = scrape_championship_odds(soup)
        
        if not all_odds_data:
            logger.warning("No odds data found")
            return []
        
        logger.info(f"Scraped {len(all_odds_data)} total entries from page")
        
        # Remove duplicate drivers from the scraped data
        all_odds_data = remove_duplicate_drivers(all_odds_data)
        logger.info(f"After removing duplicates: {len(all_odds_data)} unique drivers")
        
        # Create separate tournaments based on tournament type with filtered data
        tournaments = []
        
        if tournament_type == 'auto_racing':
            # For auto racing, create Winner, Top 2, Top 4 tournaments
            betting_lines = ['Winner', 'Top 2', 'Top 4']
            
            # Ensure all players have entries for all betting lines
            all_odds_data = ensure_all_players_have_entries(all_odds_data, betting_lines)
            
            for line in betting_lines:
                logger.info(f"Creating {line} tournament with filtered data")
                
                # Filter data to only include relevant entries for this betting line
                filtered_data = filter_odds_by_betting_line(all_odds_data, line, tournament_type)
                
                tournaments.append({
                    "line_name": line,
                    "tournament_type": tournament_type,
                    "odds_data": filtered_data,
                    "race_name": race_name
                })
                logger.info(f"Created {line} tournament with {len(filtered_data)} entries")
        
        elif tournament_type == 'golf':
            # For golf, create Winner, Top 5, Top 10 tournaments
            betting_lines = ['Winner', 'Top 5', 'Top 10']
            
            # Ensure all players have entries for all betting lines
            all_odds_data = ensure_all_players_have_entries(all_odds_data, betting_lines)
            
            for line in betting_lines:
                logger.info(f"Creating {line} tournament with filtered data")
                
                # Filter data to only include relevant entries for this betting line
                filtered_data = filter_odds_by_betting_line(all_odds_data, line, tournament_type)
                
                tournaments.append({
                    "line_name": line,
                    "tournament_type": tournament_type,
                    "odds_data": filtered_data,
                    "race_name": race_name
                })
                logger.info(f"Created {line} tournament with {len(filtered_data)} entries")
        
        else:
            # Default to Winner only
            logger.info("Using default Winner tournament")
            tournaments.append({
                "line_name": "Winner",
                "tournament_type": tournament_type,
                "odds_data": all_odds_data,
                "race_name": race_name
            })
        
        logger.info(f"Successfully created {len(tournaments)} tournaments")
        return tournaments
    
    except Exception as e:
        logger.error(f"Multi-line scraping error: {e}")
        return []
    
    finally:
        driver.quit()

def scrape_betting_line_with_interaction(driver, line_name, tournament_type):
    """Scrape data for a specific betting line by interacting with the page."""
    odds_data = []
    
    try:
        logger.info(f"Attempting to interact with betting line: {line_name}")
        
        # Wait for page to be ready
        wait = WebDriverWait(driver, 10)
        
        # Try to find and click on the specific betting line
        line_selectors = [
            f'button[data-testid*="{line_name.lower().replace(" ", "-")}"]',
            f'button[data-testid*="{line_name.lower().replace(" ", "")}"]',
            f'button[data-testid*="{line_name.lower()}"]',
            f'[data-testid*="{line_name.lower().replace(" ", "-")}"]',
            f'[data-testid*="{line_name.lower().replace(" ", "")}"]',
            f'[data-testid*="{line_name.lower()}"]',
            f'button:contains("{line_name}")',
            f'[class*="{line_name.lower().replace(" ", "-")}"]',
            f'[class*="{line_name.lower().replace(" ", "")}"]',
            f'[class*="{line_name.lower()}"]'
        ]
        
        line_clicked = False
        for selector in line_selectors:
            try:
                if ':contains(' in selector:
                    # Use XPath for text-based search
                    xpath = f"//button[contains(text(), '{line_name}')]"
                    elements = driver.find_elements(By.XPATH, xpath)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    element = elements[0]
                    # Scroll to element and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    element.click()
                    logger.info(f"Successfully clicked on betting line: {line_name}")
                    line_clicked = True
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not line_clicked:
            logger.warning(f"Could not find or click betting line: {line_name}")
        
        # Wait for the page to update after clicking
        time.sleep(random.uniform(2, 4))
        
        # Parse the updated HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Look for team/player names and odds
        team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
        odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
        
        if team_elements and odds_elements:
            logger.info(f"Found {len(team_elements)} teams and {len(odds_elements)} odds for {line_name}")
            
            # Create teams list with bounds checking
            teams = [
                {"team": clean_team_name(team_span.get_text(strip=True)), "odds": odds_elements[i].get_text(strip=True)}
                for i, team_span in enumerate(team_elements)
                if i < len(odds_elements)
            ]
            
            # Process odds for all teams
            for team in teams:
                team["processed_odds"] = process_odds(team["odds"])
                team["original_odds"] = team["odds"]
                team["odds"] = team["processed_odds"]
            
            odds_data = teams
            logger.info(f"Successfully scraped {len(odds_data)} entries for {line_name}")
        else:
            logger.warning(f"No team/odds elements found for {line_name}")
    
    except Exception as e:
        logger.error(f"Error interacting with betting line {line_name}: {e}")
    
    return odds_data

def scrape_betting_line_data(soup, line_name, tournament_type):
    """Scrape data for a specific betting line by navigating to that line's section."""
    odds_data = []
    
    logger.info(f"Scraping data for specific betting line: {line_name}")
    
    # First, try to find and click on the specific betting line button/tab
    line_selectors = [
        f'button[data-testid*="{line_name.lower().replace(" ", "-")}"]',
        f'button[data-testid*="{line_name.lower().replace(" ", "")}"]',
        f'button[data-testid*="{line_name.lower()}"]',
        f'[data-testid*="{line_name.lower().replace(" ", "-")}"]',
        f'[data-testid*="{line_name.lower().replace(" ", "")}"]',
        f'[data-testid*="{line_name.lower()}"]',
        f'button:contains("{line_name}")',
        f'[class*="{line_name.lower().replace(" ", "-")}"]',
        f'[class*="{line_name.lower().replace(" ", "")}"]',
        f'[class*="{line_name.lower()}"]'
    ]
    
    # Look for betting line navigation elements
    line_element = None
    for selector in line_selectors:
        try:
            if ':contains(' in selector:
                # Use BeautifulSoup's text-based search for contains
                text_to_find = line_name
                elements = soup.find_all('button', string=lambda text: text and text.strip().lower() == text_to_find.lower())
                if elements:
                    line_element = elements[0]
                    logger.info(f"Found line element using text search: {line_name}")
                    break
            else:
                elements = soup.select(selector)
                if elements:
                    line_element = elements[0]
                    logger.info(f"Found line element using selector: {selector}")
                    break
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue
    
    if line_element:
        logger.info(f"Found betting line element for: {line_name}")
        
        # Try to find the parent container that holds the odds for this line
        # Look for common DraftKings patterns
        parent_containers = [
            line_element.find_parent('div', {'data-testid': True}),
            line_element.find_parent('div', class_=lambda x: x and 'market' in x.lower()),
            line_element.find_parent('div', class_=lambda x: x and 'odds' in x.lower()),
            line_element.find_parent('section'),
            line_element.find_parent('div', class_=lambda x: x and 'container' in x.lower())
        ]
        
        # Find the most relevant parent container
        target_container = None
        for container in parent_containers:
            if container:
                target_container = container
                break
        
        if target_container:
            logger.info(f"Using parent container for {line_name}")
            # Search within the specific container
            team_elements = target_container.find_all("span", {"data-testid": "button-title-market-board"})
            odds_elements = target_container.find_all("span", {"data-testid": "button-odds-market-board"})
        else:
            logger.info(f"No specific container found for {line_name}, using page-wide search")
            # Fallback to page-wide search
            team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
            odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    else:
        logger.warning(f"Could not find betting line element for: {line_name}")
        # Fallback to page-wide search
        team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
        odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    if team_elements and odds_elements:
        logger.info(f"Found {len(team_elements)} teams and {len(odds_elements)} odds for {line_name}")
        
        # Create teams list with bounds checking
        teams = [
            {"team": clean_team_name(team_span.get_text(strip=True)), "odds": odds_elements[i].get_text(strip=True)}
            for i, team_span in enumerate(team_elements)
            if i < len(odds_elements)
        ]
        
        # Process odds for all teams
        for team in teams:
            team["processed_odds"] = process_odds(team["odds"])
            team["original_odds"] = team["odds"]
            team["odds"] = team["processed_odds"]
        
        odds_data = teams
        logger.info(f"Successfully scraped {len(odds_data)} entries for {line_name}")
    else:
        logger.warning(f"No team/odds elements found for {line_name}")
    
    return odds_data

def scrape_championship_odds(soup):
    """Scrape championship odds as a flat list of all teams."""
    odds_data = []
    seen_teams = set()  # Track teams to prevent duplicates
    
    # Find tournament headers to detect boundaries
    tournament_headers = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    logger.info(f"Found {len(tournament_headers)} tournament headers on page")
    
    # Log all tournament headers for debugging
    for i, header in enumerate(tournament_headers):
        header_text = header.get_text(strip=True)
        logger.info(f"Tournament header {i+1}: '{header_text}'")
    
    # Method 1: Try the working selectors from V1
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    if team_elements and odds_elements:
        logger.info(f"Found {len(team_elements)} teams and {len(odds_elements)} odds using V1 selectors")
        
        # Determine which tournament section to scrape
        target_tournament_index = 0  # Default to first tournament
        max_entries = min(len(team_elements), len(odds_elements), 25)  # Default limit
        
        # If we have multiple tournaments, try to identify the correct one
        if len(tournament_headers) > 1:
            logger.info("Multiple tournaments detected, attempting to identify the correct one")
            
            # Look for the tournament that matches our URL or is most likely the current one
            for i, header in enumerate(tournament_headers):
                header_text = header.get_text(strip=True).lower()
                logger.info(f"Checking tournament {i+1}: '{header_text}'")
                
                # Prefer tournaments that don't contain "las vegas" or other future tournaments
                if 'las vegas' not in header_text and 'miami' not in header_text:
                    target_tournament_index = i
                    logger.info(f"Selected tournament {i+1} as target: '{header_text}'")
                    break
            
            # Calculate approximate boundaries for the selected tournament
            if target_tournament_index < len(tournament_headers) - 1:
                # There's a next tournament, so limit our scraping
                estimated_teams_per_tournament = len(team_elements) // len(tournament_headers)
                max_entries = min(
                    (target_tournament_index + 1) * estimated_teams_per_tournament,
                    len(team_elements)
                )
                logger.info(f"Limited scraping to avoid next tournament: {max_entries} entries")
            else:
                # This is the last tournament, use all remaining data
                logger.info("Using all remaining data (last tournament)")
        
        logger.info(f"Scraping {max_entries} entries from tournament {target_tournament_index + 1}")
        
        for i, (team, odd) in enumerate(zip(team_elements[:max_entries], odds_elements[:max_entries])):
            team_name = clean_team_name(team.get_text(strip=True))
            original_odds = odd.get_text(strip=True)
            processed_odds = process_odds(original_odds)
            
            # Normalize the driver name to handle variations
            normalized_name = normalize_driver_name(team_name)
            
            # Enhanced tournament boundary detection - stop if we hit different tournament indicators
            tournament_indicators = [
                'las vegas', 'miami', 'monaco', 'silverstone', 'spa', 'monza', 'spain', 'france',
                'austria', 'hungary', 'belgium', 'netherlands', 'singapore', 'japan', 'australia',
                'bahrain', 'saudi', 'qatar', 'abu dhabi', 'brazil', 'mexico', 'canada', 'azerbaijan',
                'china', 'russia', 'portugal', 'turkey', 'imola', 'emilia', 'romagna', 'usa gp', 'usa grand prix'
            ]
            
            # Check if team name suggests we're in a different tournament
            if any(indicator in team_name.lower() for indicator in tournament_indicators):
                if i > 5:  # Only stop if we've already scraped some entries
                    logger.info(f"Stopping at element {i} - detected different tournament: {team_name}")
                    break
            
            # Check for tournament name patterns that suggest we're in next week's tournament
            next_week_indicators = [
                'next week', 'upcoming', 'future', 'next race', 'next grand prix',
                'next tournament', 'next event', 'next round'
            ]
            
            if any(indicator in team_name.lower() for indicator in next_week_indicators):
                if i > 5:  # Only stop if we've already scraped some entries
                    logger.info(f"Stopping at element {i} - detected next week tournament: {team_name}")
                    break
            
            # Check for duplicates using normalized name
            if normalized_name and normalized_name not in seen_teams:
                # Include player even if they don't have odds
                if original_odds and processed_odds:
                    odds_data.append({
                        "team": normalized_name, 
                        "odds": processed_odds,
                        "original_odds": original_odds
                    })
                    logger.info(f"Scraped: {normalized_name} @ {original_odds} -> {processed_odds}")
                else:
                    # Player exists but has no odds - include with empty odds
                    odds_data.append({
                        "team": normalized_name, 
                        "odds": "",
                        "original_odds": ""
                    })
                    logger.info(f"Scraped: {normalized_name} (no odds available)")
                
                seen_teams.add(normalized_name)
            elif normalized_name in seen_teams:
                logger.info(f"Skipping duplicate: {normalized_name}")
    
    # Method 2: Fallback to generic selectors if V1 method fails
    if not odds_data:
        logger.info("Trying fallback selectors...")
        
        # Look for common DraftKings patterns
        offer_cards = soup.find_all('div', {'data-testid': 'offer-card'})
        if not offer_cards:
            offer_cards = soup.find_all('div', class_=lambda x: x and 'offer' in x.lower())
        
        for card in offer_cards:
            try:
                # Try to find team name
                team_elem = None
                team_selectors = [
                    'span[data-testid="button-title-market-board"]',
                    '.team-name',
                    '.offer-name',
                    '[class*="team"]',
                    'span[class*="title"]'
                ]
                
                for selector in team_selectors:
                    team_elem = card.select_one(selector)
                    if team_elem:
                        break
                
                # Try to find odds
                odds_elem = None
                odds_selectors = [
                    'span[data-testid="button-odds-market-board"]',
                    '.odds',
                    '.offer-price',
                    '[class*="odds"]',
                    'span[class*="price"]'
                ]
                
                for selector in odds_selectors:
                    odds_elem = card.select_one(selector)
                    if odds_elem:
                        break
                
                if team_elem and odds_elem:
                    team_name = team_elem.get_text(strip=True)
                    odds_value = odds_elem.get_text(strip=True)
                    
                    # Validate odds format (should contain + or -) and check for duplicates
                    if (team_name and odds_value and ('+' in odds_value or '-' in odds_value) 
                        and team_name not in seen_teams):
                        processed_odds = process_odds(odds_value)
                        odds_data.append({
                            "team": team_name, 
                            "odds": processed_odds,
                            "original_odds": odds_value
                        })
                        seen_teams.add(team_name)
                        logger.info(f"Fallback scraped: {team_name} @ {odds_value} -> {processed_odds}")
                    elif team_name in seen_teams:
                        logger.info(f"Skipping duplicate fallback: {team_name}")
            
            except Exception as e:
                logger.warning(f"Error processing card: {e}")
    
    # Method 3: Text-based extraction as last resort
    if not odds_data:
        logger.info("Trying text-based extraction...")
        all_text = soup.get_text()
        
        # Look for patterns like "Team Name +120" or "Team Name -150"
        import re
        patterns = [
            r'([A-Za-z\s]+?)\s*([+-]\d+)',  # Team name followed by odds
            r'([A-Za-z\s]+?)\s*(\+\d+|\-\d+)',  # More specific odds pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                team_name = match[0].strip()
                odds_value = match[1].strip()
                
                # Filter out common false positives and check for duplicates
                if (len(team_name) > 3 and len(team_name) < 50 and 
                    team_name not in ['Odds', 'Bet', 'Line', 'Point'] and
                    ('+' in odds_value or '-' in odds_value) and
                    team_name not in seen_teams):
                    processed_odds = process_odds(odds_value)
                    odds_data.append({
                        "team": team_name, 
                        "odds": processed_odds,
                        "original_odds": odds_value
                    })
                    seen_teams.add(team_name)
                    logger.info(f"Text-based scraped: {team_name} @ {odds_value} -> {processed_odds}")
                elif team_name in seen_teams:
                    logger.info(f"Skipping duplicate text-based: {team_name}")
    
    if not odds_data:
        logger.warning("No odds data found. Page structure might have changed.")
    
    # Final deduplication check (extra safety)
    final_odds_data = []
    final_seen_teams = set()
    
    for item in odds_data:
        team_name = item["team"]
        if team_name not in final_seen_teams:
            final_odds_data.append(item)
            final_seen_teams.add(team_name)
        else:
            logger.info(f"Final deduplication: Skipping duplicate {team_name}")
    
    logger.info(f"Final result: {len(final_odds_data)} unique teams scraped")
    return final_odds_data

def scrape_conference_odds(soup):
    """Scrape conference odds with teams grouped by conference (from V1 logic)."""
    team_spans = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_spans = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    # Create teams list with bounds checking
    teams = [
        {"team": team_span.get_text(strip=True), "odds": odds_spans[i].get_text(strip=True)}
        for i, team_span in enumerate(team_spans)
        if i < len(odds_spans)
    ]
    
    # Process odds for all teams
    for team in teams:
        team["processed_odds"] = process_odds(team["odds"])
        team["original_odds"] = team["odds"]
        team["odds"] = team["processed_odds"]
    
    # Split teams into conferences (first half = NFC, second half = AFC)
    total_teams = len(teams)
    mid_point = total_teams // 2
    
    conferences = [
        {"conference": "NFC", "teams": teams[:mid_point]},
        {"conference": "AFC", "teams": teams[mid_point:]}
    ]
    
    logger.info(f"Conference scraping: {len(conferences)} conferences, {total_teams} total teams")
    
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

def scrape_division_odds(soup):
    """Scrape division odds with teams grouped by division (from V1 logic)."""
    division_titles = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    team_spans = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_spans = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    # Create teams list with bounds checking
    teams = [
        {"team": clean_team_name(team_span.get_text(strip=True)), "odds": odds_spans[i].get_text(strip=True)}
        for i, team_span in enumerate(team_spans)
        if i < len(odds_spans)
    ]
    
    # Process odds for all teams
    for team in teams:
        team["processed_odds"] = process_odds(team["odds"])
        team["original_odds"] = team["odds"]
        team["odds"] = team["processed_odds"]
    
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
    
    logger.info(f"Division scraping: {len(divisions)} divisions, {len(teams)} total teams")
    
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

@app.route('/')
def index():
    """Serve the web app."""
    return render_template('web_app.html')

@app.route('/api/scrape', methods=['POST'])
def scrape_url():
    """API endpoint to scrape a single URL."""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"API request to scrape: {url}")
        
        # Scrape the URL
        odds = scrape_draftkings_odds(url)
        
        return jsonify({
            'success': True,
            'url': url,
            'odds': odds,
            'count': len(odds)
        })
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape-multiple', methods=['POST'])
def scrape_multiple_urls():
    """API endpoint to scrape multiple URLs."""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'error': 'URLs list is required'}), 400
        
        results = []
        
        for i, url in enumerate(urls):
            logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
            
            try:
                odds = scrape_draftkings_odds(url)
                results.append({
                    'url': url,
                    'success': True,
                    'odds': odds,
                    'count': len(odds)
                })
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e),
                    'odds': [],
                    'count': 0
                })
            
            # Small delay between requests
            time.sleep(1)
        
        return jsonify({
            'success': True,
            'results': results,
            'total_urls': len(urls),
            'successful_urls': len([r for r in results if r['success']]),
            'total_odds': sum(r['count'] for r in results)
        })
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-payloads', methods=['POST'])
def generate_payloads():
    """Generate API payloads for game creation and odds submission."""
    try:
        data = request.get_json()
        url = data.get('url')
        start_id = data.get('start_id', 1000000)
        sport_config = data.get('sport_config', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate start_id
        if not (1000000 <= start_id <= 9999999):
            return jsonify({'error': 'Start ID must be a 7-digit number (1000000-9999999)'}), 400
        
        logger.info(f"Generating payloads for: {url} with start_id: {start_id}")
        
        # Get event type from request
        event_type = data.get('event_type', 'championship')
        
        # Scrape the URL with event type
        odds_data = scrape_draftkings_odds(url, event_type)
        
        if not odds_data:
            return jsonify({
                'success': False,
                'error': 'No odds data found',
                'url': url
            })
        
        # Generate current timestamp
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
        
        # Detect tournament name from URL
        tournament_name = detect_tournament_name(url, sport_config.get("description", ""))
        
        # Create GameData payload
        game_payload = {
            "IdSport": "TNT",
            "IdLeague": sport_config.get("id_league", 3101),
            "IdGameType": sport_config.get("id_game_type", 1),
            "GameDateTime": current_time,
            "VisitorNumber": 1,
            "HomeNumber": 2,
            "VisitorTeam": tournament_name,  # Use detected tournament name
            "HomeTeam": tournament_name,  # Use same tournament name for both
            "VisitorScore": 0,
            "HomeScore": 0,
            "VisitorPitcher": "",
            "HomePitcher": "",
            "NormalGame": 0,
            "GameStat": "D",
            "Graded": False,
            "Hookups": False,
            "Local": True,
            "Online": True,
            "ShortGame": False,
            "EventDate": current_time,
            "DateChanged": False,
            "YimeChanged": False,
            "PitcherChanged": 0,
            "Period": 0,
            "ParentGame": 0,
            "GradedDate": None,
            "NumTeams": len(odds_data),
            "IdEvent": 0,
            "FamilyGame": 0,
            "HasChildren": False,
            "IdTeamVisitor": 0,
            "IdTeamHome": 0,
            "IdBannerType": 0,
            "Description": f"{tournament_name} - DraftKings Scraped Data",
            "AcceptAutoChanges": True,
            "IdUser": 360,
            "Result": 0,
            "TournamentType": 1,
            "TournamentPlacestoPaid": "1"
        }
        
        # Generate GameValuesTNT payload with user-specified starting ID
        id_generator = SevenDigitIDGenerator(start_id)
        game_values = []
        
        # Handle different event types
        if isinstance(odds_data, dict) and odds_data.get("event_type") == "conference":
            # Conference event - flatten all teams from all conferences
            for conference in odds_data.get("conferences", []):
                for team_data in conference.get("teams", []):
                    team_id = id_generator.get_next_id()
                    game_values.append({
                        "Id": team_id,
                        "TeamName": team_data["team"],
                        "Odds": team_data["odds"]  # Already processed odds
                    })
        elif isinstance(odds_data, dict) and odds_data.get("event_type") == "division":
            # Division event - flatten all teams from all divisions
            for division in odds_data.get("divisions", []):
                for team_data in division.get("teams", []):
                    team_id = id_generator.get_next_id()
                    game_values.append({
                        "Id": team_id,
                        "TeamName": team_data["team"],
                        "Odds": team_data["odds"]  # Already processed odds
                    })
        else:
            # Championship or flat list - process normally
            for team_data in odds_data:
                team_id = id_generator.get_next_id()
                game_values.append({
                    "Id": team_id,
                    "TeamName": team_data["team"],
                    "Odds": team_data["odds"]  # Already processed odds
                })
        
        return jsonify({
            'success': True,
            'url': url,
            'start_id': start_id,
            'game_creation_payload': game_payload,
            'odds_submission_payload': game_values,
            'scraped_data': odds_data,
            'stats': {
                'total_teams': len(odds_data),
                'id_range': f"{start_id} - {id_generator.get_current_id()}",
                'odds_processed': True
            }
        })
        
    except Exception as e:
        logger.error(f"Payload generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-multi-line-payloads', methods=['POST'])
def generate_multi_line_payloads():
    """Generate API payloads for multi-line tournaments (Golf, Auto Racing) with separate tournaments for each betting line."""
    try:
        data = request.get_json()
        url = data.get('url')
        start_id = data.get('start_id', 1000000)
        sport_config = data.get('sport_config', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate start_id
        if not (1000000 <= start_id <= 9999999):
            return jsonify({'error': 'Start ID must be a 7-digit number (1000000-9999999)'}), 400
        
        logger.info(f"Generating multi-line payloads for: {url} with start_id: {start_id}")
        
        # Scrape the URL for multi-line tournament data
        try:
            tournaments_data = scrape_multi_line_tournament(url)
        except Exception as e:
            logger.error(f"Error in scrape_multi_line_tournament: {e}")
            return jsonify({
                'success': False,
                'error': f'Scraping error: {str(e)}',
                'url': url
            })
        
        if not tournaments_data:
            return jsonify({
                'success': False,
                'error': 'No tournament data found',
                'url': url
            })
        
        # Generate current timestamp
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
        
        # Extract race name from the first tournament (they should all have the same race name)
        race_name = tournaments_data[0].get('race_name') if tournaments_data else None
        
        if race_name:
            logger.info(f"Using extracted race name: {race_name}")
            grand_prix_name = race_name
        else:
            # Fallback to URL-based detection
            tournament_name = detect_tournament_name(url, sport_config.get("description", ""))
            grand_prix_name = extract_grand_prix_name(url, tournament_name)
            logger.info(f"Using URL-based race name: {grand_prix_name}")
        
        # Create separate tournaments for each betting line
        tournament_payloads = []
        id_generator = SevenDigitIDGenerator(start_id)
        
        for tournament in tournaments_data:
            line_name = tournament['line_name']
            odds_data = tournament['odds_data']
            tournament_type = tournament['tournament_type']
            
            if not odds_data:
                logger.warning(f"No odds data for line: {line_name}")
                continue
            
            # Create individual tournament name with Grand Prix and betting line
            individual_tournament_name = f"{grand_prix_name} - {line_name}"
            individual_description = f"{grand_prix_name} {line_name} - DraftKings Scraped Data"
            
            # Create GameData payload for this individual betting line tournament
            game_payload = {
                "IdSport": "TNT",
                "IdLeague": sport_config.get("id_league", 3101),
                "IdGameType": sport_config.get("id_game_type", 1),
                "GameDateTime": current_time,
                "VisitorNumber": 1,
                "HomeNumber": 2,
                "VisitorTeam": individual_tournament_name,
                "HomeTeam": individual_tournament_name,
                "VisitorScore": 0,
                "HomeScore": 0,
                "VisitorPitcher": "",
                "HomePitcher": "",
                "NormalGame": 0,
                "GameStat": "D",
                "Graded": False,
                "Hookups": False,
                "Local": True,
                "Online": True,
                "ShortGame": False,
                "EventDate": current_time,
                "DateChanged": False,
                "YimeChanged": False,
                "PitcherChanged": 0,
                "Period": 0,
                "ParentGame": 0,
                "GradedDate": None,
                "NumTeams": len(odds_data),
                "IdEvent": 0,
                "FamilyGame": 0,
                "HasChildren": False,
                "IdTeamVisitor": 0,
                "IdTeamHome": 0,
                "IdBannerType": 0,
                "Description": individual_description,
                "AcceptAutoChanges": True,
                "IdUser": 360,
                "Result": 0,
                "TournamentType": 1,
                "TournamentPlacestoPaid": "1"
            }
            
            # Generate GameValuesTNT payload for this betting line
            game_values = []
            for team_data in odds_data:
                team_id = id_generator.get_next_id()
                game_values.append({
                    "Id": team_id,
                    "TeamName": team_data["team"],
                    "Odds": team_data["odds"]
                })
            
            tournament_payloads.append({
                "line_name": line_name,
                "tournament_type": tournament_type,
                "game_creation_payload": game_payload,
                "odds_submission_payload": game_values,
                "scraped_data": odds_data,
                "stats": {
                    "total_teams": len(odds_data),
                    "id_range": f"{start_id} - {id_generator.get_current_id()}"
                }
            })
        
        return jsonify({
            'success': True,
            'url': url,
            'start_id': start_id,
            'tournament_type': detect_tournament_type(url),
            'tournaments': tournament_payloads,
            'total_tournaments': len(tournament_payloads),
            'stats': {
                'total_lines': len(tournament_payloads),
                'total_teams': sum(t['stats']['total_teams'] for t in tournament_payloads),
                'id_range': f"{start_id} - {id_generator.get_current_id()}"
            }
        })
        
    except Exception as e:
        logger.error(f"Multi-line payload generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submit-multi-line-tournaments', methods=['POST'])
def submit_multi_line_tournaments():
    """Submit multiple tournaments for different betting lines."""
    try:
        data = request.get_json()
        tournaments = data.get('tournaments', [])
        
        if not tournaments:
            return jsonify({'error': 'Tournaments list is required'}), 400
        
        logger.info(f"Submitting {len(tournaments)} multi-line tournaments")
        
        results = []
        
        for i, tournament in enumerate(tournaments):
            line_name = tournament.get('line_name', f'Line {i+1}')
            game_payload = tournament.get('game_creation_payload')
            odds_payload = tournament.get('odds_submission_payload')
            
            if not game_payload or not odds_payload:
                results.append({
                    'line_name': line_name,
                    'success': False,
                    'error': 'Missing game or odds payload'
                })
                continue
            
            try:
                # Step 1: Create the game
                logger.info(f"Creating game for {line_name}")
                
                api_url = "https://clmapi.sportsfanwagers.com/api/Game/InsertGame"
                response = requests.post(api_url, json=game_payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle different response formats
                    if isinstance(result, dict):
                        game_id = result.get("idGame") or result.get("IdGame") or result.get("id")
                    else:
                        game_id = result
                    
                    logger.info(f"Game created for {line_name} with ID: {game_id}")
                    
                    # Step 2: Submit the odds
                    logger.info(f"Submitting odds for {line_name}")
                    
                    odds_api_url = f"https://clmapi.sportsfanwagers.com/api/Game/InsertGameValuesTNT?idGame={game_id}"
                    odds_response = requests.post(odds_api_url, json=odds_payload, timeout=60)
                    
                    if odds_response.status_code == 200:
                        odds_result = odds_response.json()
                        logger.info(f"Odds submitted successfully for {line_name}")
                        
                        results.append({
                            'line_name': line_name,
                            'success': True,
                            'game_id': game_id,
                            'message': f'Successfully created {line_name} tournament',
                            'odds_count': len(odds_payload)
                        })
                    else:
                        logger.error(f"Odds submission failed for {line_name}: {odds_response.status_code}")
                        results.append({
                            'line_name': line_name,
                            'success': False,
                            'error': f'Odds submission failed: {odds_response.status_code}',
                            'game_id': game_id
                        })
                else:
                    logger.error(f"Game creation failed for {line_name}: {response.status_code}")
                    results.append({
                        'line_name': line_name,
                        'success': False,
                        'error': f'Game creation failed: {response.status_code}'
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {line_name}: {e}")
                results.append({
                    'line_name': line_name,
                    'success': False,
                    'error': str(e)
                })
        
        successful_tournaments = len([r for r in results if r.get('success', False)])
        
        return jsonify({
            'success': True,
            'total_tournaments': len(tournaments),
            'successful_tournaments': successful_tournaments,
            'failed_tournaments': len(tournaments) - successful_tournaments,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Multi-line tournament submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submit-all-individual-tournaments', methods=['POST'])
def submit_all_individual_tournaments():
    """Submit all individual tournaments for each betting line to CLM API."""
    try:
        data = request.get_json()
        url = data.get('url')
        start_id = data.get('start_id', 1000000)
        sport_config = data.get('sport_config', {})
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate start_id
        if not (1000000 <= start_id <= 9999999):
            return jsonify({'error': 'Start ID must be a 7-digit number (1000000-9999999)'}), 400
        
        logger.info(f"Submitting all individual tournaments for: {url} with start_id: {start_id}")
        
        # First, generate the multi-line payloads
        try:
            tournaments_data = scrape_multi_line_tournament(url)
        except Exception as e:
            logger.error(f"Error in scrape_multi_line_tournament: {e}")
            return jsonify({
                'success': False,
                'error': f'Scraping error: {str(e)}',
                'url': url
            })
        
        if not tournaments_data:
            return jsonify({
                'success': False,
                'error': 'No tournament data found',
                'url': url
            })
        
        # Generate current timestamp
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M")
        
        # Extract race name from the first tournament (they should all have the same race name)
        race_name = tournaments_data[0].get('race_name') if tournaments_data else None
        
        if race_name:
            logger.info(f"Using extracted race name: {race_name}")
            grand_prix_name = race_name
        else:
            # Fallback to URL-based detection
            tournament_name = detect_tournament_name(url, sport_config.get("description", ""))
            grand_prix_name = extract_grand_prix_name(url, tournament_name)
            logger.info(f"Using URL-based race name: {grand_prix_name}")
        
        # Submit each tournament individually with sequential ID generation
        results = []
        id_generator = SevenDigitIDGenerator(start_id)
        
        logger.info(f"Starting sequential ID generation from {start_id}")
        
        for tournament in tournaments_data:
            line_name = tournament['line_name']
            odds_data = tournament['odds_data']
            tournament_type = tournament['tournament_type']
            
            if not odds_data:
                logger.warning(f"No odds data for line: {line_name}")
                results.append({
                    'line_name': line_name,
                    'success': False,
                    'error': 'No odds data available'
                })
                continue
            
            try:
                # Create individual tournament name with Grand Prix and betting line
                individual_tournament_name = f"{grand_prix_name} - {line_name}"
                individual_description = f"{grand_prix_name} {line_name} - DraftKings Scraped Data"
                
                # Log the current ID range for this tournament
                current_start_id = id_generator.get_current_id() + 1
                logger.info(f"Processing {line_name} tournament starting from ID: {current_start_id}")
                
                # Create GameData payload for this individual betting line tournament
                game_payload = {
                    "IdSport": "TNT",
                    "IdLeague": sport_config.get("id_league", 3101),
                    "IdGameType": sport_config.get("id_game_type", 1),
                    "GameDateTime": current_time,
                    "VisitorNumber": 1,
                    "HomeNumber": 2,
                    "VisitorTeam": individual_tournament_name,
                    "HomeTeam": individual_tournament_name,
                    "VisitorScore": 0,
                    "HomeScore": 0,
                    "VisitorPitcher": "",
                    "HomePitcher": "",
                    "NormalGame": 0,
                    "GameStat": "D",
                    "Graded": False,
                    "Hookups": False,
                    "Local": True,
                    "Online": True,
                    "ShortGame": False,
                    "EventDate": current_time,
                    "DateChanged": False,
                    "YimeChanged": False,
                    "PitcherChanged": 0,
                    "Period": 0,
                    "ParentGame": 0,
                    "GradedDate": None,
                    "NumTeams": len(odds_data),
                    "IdEvent": 0,
                    "FamilyGame": 0,
                    "HasChildren": False,
                    "IdTeamVisitor": 0,
                    "IdTeamHome": 0,
                    "IdBannerType": 0,
                    "Description": individual_description,
                    "AcceptAutoChanges": True,
                    "IdUser": 360,
                    "Result": 0,
                    "TournamentType": 1,
                    "TournamentPlacestoPaid": "1"
                }
                
                # Generate GameValuesTNT payload for this betting line with sequential IDs
                game_values = []
                for team_data in odds_data:
                    team_id = id_generator.get_next_id()
                    game_values.append({
                        "Id": team_id,
                        "TeamName": team_data["team"],
                        "Odds": team_data["odds"]
                    })
                
                # Log the ID range used for this tournament
                tournament_end_id = id_generator.get_current_id()
                logger.info(f"Tournament {line_name} used IDs: {current_start_id} - {tournament_end_id} ({len(game_values)} teams)")
                
                # Step 1: Create the individual tournament
                logger.info(f"Creating individual tournament: {individual_tournament_name}")
                
                api_url = "https://clmapi.sportsfanwagers.com/api/Game/InsertGame"
                response = requests.post(api_url, json=game_payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle different response formats
                    if isinstance(result, dict):
                        game_id = result.get("idGame") or result.get("IdGame") or result.get("id")
                    else:
                        game_id = result
                    
                    logger.info(f"Individual tournament created: {individual_tournament_name} with ID: {game_id}")
                    
                    # Step 2: Submit the odds for this tournament
                    logger.info(f"Submitting odds for {individual_tournament_name}")
                    
                    odds_api_url = f"https://clmapi.sportsfanwagers.com/api/Game/InsertGameValuesTNT?idGame={game_id}"
                    odds_response = requests.post(odds_api_url, json=game_values, timeout=60)
                    
                    if odds_response.status_code == 200:
                        odds_result = odds_response.json()
                        logger.info(f"Odds submitted successfully for {individual_tournament_name}")
                        
                        results.append({
                            'line_name': line_name,
                            'tournament_name': individual_tournament_name,
                            'success': True,
                            'game_id': game_id,
                            'message': f'Successfully created {individual_tournament_name}',
                            'odds_count': len(game_values),
                            'drivers': [team["TeamName"] for team in game_values],
                            'id_range': f"{current_start_id} - {tournament_end_id}",
                            'team_ids': [team["Id"] for team in game_values]
                        })
                    else:
                        logger.error(f"Odds submission failed for {individual_tournament_name}: {odds_response.status_code}")
                        results.append({
                            'line_name': line_name,
                            'tournament_name': individual_tournament_name,
                            'success': False,
                            'error': f'Odds submission failed: {odds_response.status_code}',
                            'game_id': game_id
                        })
                else:
                    logger.error(f"Tournament creation failed for {individual_tournament_name}: {response.status_code}")
                    results.append({
                        'line_name': line_name,
                        'tournament_name': individual_tournament_name,
                        'success': False,
                        'error': f'Tournament creation failed: {response.status_code}'
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {line_name}: {e}")
                results.append({
                    'line_name': line_name,
                    'tournament_name': individual_tournament_name if 'individual_tournament_name' in locals() else f"{grand_prix_name} - {line_name}",
                    'success': False,
                    'error': str(e)
                })
        
        successful_tournaments = len([r for r in results if r.get('success', False)])
        final_id = id_generator.get_current_id()
        
        return jsonify({
            'success': True,
            'grand_prix_name': grand_prix_name,
            'total_tournaments': len(tournaments_data),
            'successful_tournaments': successful_tournaments,
            'failed_tournaments': len(tournaments_data) - successful_tournaments,
            'results': results,
            'summary': {
                'grand_prix': grand_prix_name,
                'total_lines': len(tournaments_data),
                'successful_lines': successful_tournaments,
                'failed_lines': len(tournaments_data) - successful_tournaments,
                'id_range': f"{start_id} - {final_id}",
                'total_ids_used': final_id - start_id + 1
            }
        })
        
    except Exception as e:
        logger.error(f"All individual tournaments submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submit-game', methods=['POST'])
def submit_game():
    """Submit game creation to the CLM API."""
    try:
        data = request.get_json()
        game_payload = data.get('game_payload')
        
        if not game_payload:
            return jsonify({'error': 'Game payload is required'}), 400
        
        logger.info("Submitting game creation to CLM API")
        
        # Submit to CLM API
        api_url = "https://clmapi.sportsfanwagers.com/api/Game/InsertGame"
        
        response = requests.post(api_url, json=game_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, dict):
                game_id = result.get("idGame") or result.get("IdGame") or result.get("id")
            else:
                game_id = result  # If response is just the ID number
            
            logger.info(f"Game created successfully with ID: {game_id}")
            
            return jsonify({
                'success': True,
                'game_id': game_id,
                'message': f'Game created successfully with ID: {game_id}',
                'response': result
            })
        else:
            logger.error(f"Game creation failed: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': f'Game creation failed: {response.status_code}',
                'details': response.text
            }), 400
            
    except Exception as e:
        logger.error(f"Game submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submit-odds', methods=['POST'])
def submit_odds():
    """Submit odds to the CLM API."""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        odds_payload = data.get('odds_payload')
        
        if not game_id:
            return jsonify({'error': 'Game ID is required'}), 400
        
        if not odds_payload:
            return jsonify({'error': 'Odds payload is required'}), 400
        
        logger.info(f"Submitting odds for game ID: {game_id}")
        
        # Submit to CLM API
        api_url = f"https://clmapi.sportsfanwagers.com/api/Game/InsertGameValuesTNT?idGame={game_id}"
        
        response = requests.post(api_url, json=odds_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Odds submitted successfully for game {game_id}")
            
            return jsonify({
                'success': True,
                'game_id': game_id,
                'message': f'Odds submitted successfully for game {game_id}',
                'response': result,
                'odds_count': len(odds_payload)
            })
        else:
            logger.error(f"Odds submission failed: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': f'Odds submission failed: {response.status_code}',
                'details': response.text
            }), 400
            
    except Exception as e:
        logger.error(f"Odds submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/submit-complete', methods=['POST'])
def submit_complete():
    """Submit both game creation and odds submission in sequence."""
    try:
        data = request.get_json()
        game_payload = data.get('game_payload')
        odds_payload = data.get('odds_payload')
        
        if not game_payload or not odds_payload:
            return jsonify({'error': 'Both game and odds payloads are required'}), 400
        
        logger.info("Starting complete submission process")
        
        # Step 1: Create the game
        logger.info("Submitting game creation to CLM API")
        
        api_url = "https://clmapi.sportsfanwagers.com/api/Game/InsertGame"
        response = requests.post(api_url, json=game_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, dict):
                game_id = result.get("idGame") or result.get("IdGame") or result.get("id")
            else:
                game_id = result  # If response is just the ID number
            
            logger.info(f"Game created successfully with ID: {game_id}")
            
            # Step 2: Submit the odds
            logger.info(f"Submitting odds for game ID: {game_id}")
            
            odds_api_url = f"https://clmapi.sportsfanwagers.com/api/Game/InsertGameValuesTNT?idGame={game_id}"
            odds_response = requests.post(odds_api_url, json=odds_payload, timeout=60)
            
            if odds_response.status_code == 200:
                odds_result = odds_response.json()
                logger.info(f"Odds submitted successfully for game {game_id}")
                
                return jsonify({
                    'success': True,
                    'game_id': game_id,
                    'message': f'Complete submission successful! Game {game_id} created with {len(odds_payload)} odds entries',
                    'game_creation': {
                        'success': True,
                        'game_id': game_id,
                        'message': f'Game created successfully with ID: {game_id}',
                        'response': result
                    },
                    'odds_submission': {
                        'success': True,
                        'game_id': game_id,
                        'message': f'Odds submitted successfully for game {game_id}',
                        'response': odds_result,
                        'odds_count': len(odds_payload)
                    }
                })
            else:
                logger.error(f"Odds submission failed: {odds_response.status_code} - {odds_response.text}")
                return jsonify({
                    'success': False,
                    'error': f'Odds submission failed: {odds_response.status_code}',
                    'game_id': game_id,
                    'details': odds_response.text
                }), 400
        else:
            logger.error(f"Game creation failed: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': f'Game creation failed: {response.status_code}',
                'details': response.text
            }), 400
        
    except Exception as e:
        logger.error(f"Complete submission error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/check-existing-odds', methods=['GET'])
def check_existing_odds():
    """Check if odds already exist for a game."""
    try:
        game_id = request.args.get('game_id')
        
        if not game_id:
            return jsonify({'error': 'Game ID is required'}), 400
        
        logger.info(f"Checking existing odds for game ID: {game_id}")
        
        # Check existing odds
        api_url = f"https://clmapi.sportsfanwagers.com/api/Game/GetGameValuesTNT?idGame={game_id}"
        
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            existing_odds = response.json()
            has_odds = existing_odds and len(existing_odds) > 0
            
            return jsonify({
                'success': True,
                'game_id': game_id,
                'has_existing_odds': has_odds,
                'existing_odds_count': len(existing_odds) if existing_odds else 0,
                'existing_odds': existing_odds
            })
        else:
            logger.error(f"Failed to check existing odds: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Failed to check existing odds: {response.status_code}',
                'details': response.text
            }), 400
            
    except Exception as e:
        logger.error(f"Check existing odds error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
def status():
    """API endpoint to check server status."""
    return jsonify({
        'status': 'running',
        'timestamp': time.time(),
        'version': '2.0.0'
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Copy the HTML file to templates directory
    import shutil
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    web_app_path = os.path.join(script_dir, 'web_app.html')
    templates_path = os.path.join(script_dir, 'templates', 'web_app.html')
    
    # Ensure templates directory exists
    os.makedirs(os.path.join(script_dir, 'templates'), exist_ok=True)
    
    # Copy the file
    if os.path.exists(web_app_path):
        shutil.copy(web_app_path, templates_path)
        print(f"Copied web_app.html to templates directory")
    else:
        print(f"Warning: web_app.html not found at {web_app_path}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
