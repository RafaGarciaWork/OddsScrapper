#!/usr/bin/env python3
"""
Test the fixed scraper with the correct selectors
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import logging
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import re

# Configure detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver(headless=True):
    """Setup Chrome driver with proper options for DraftKings."""
    logger.info("🚗 Setting up Chrome driver")
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

def clean_team_name(team_name):
    """Clean team/driver names by removing unwanted prefixes and suffixes."""
    if not team_name:
        return team_name
    
    # Remove common unwanted prefixes
    unwanted_prefixes = [
        'Finish', 'To Finish', 'To Win', 'Winner', 'Champion', 'Top', 'Place', 'Position',
        'AMRACE Winner', 'AMRACE', 'Race Winner', 'Race', 'Finish ', 'Finish To', 'Finish Winner'
    ]
    
    # Remove common unwanted suffixes
    unwanted_suffixes = [
        'Finish', 'Winner', 'Champion', 'To Win', 'To Finish'
    ]
    
    cleaned_name = team_name.strip()
    
    # Remove prefixes (case insensitive)
    for prefix in unwanted_prefixes:
        if cleaned_name.lower().startswith(prefix.lower()):
            cleaned_name = cleaned_name[len(prefix):].strip()
            break
    
    # Remove suffixes (case insensitive)
    for suffix in unwanted_suffixes:
        if cleaned_name.lower().endswith(suffix.lower()):
            cleaned_name = cleaned_name[:-len(suffix)].strip()
    
    # Clean up any extra spaces
    cleaned_name = ' '.join(cleaned_name.split())
    
    return cleaned_name

def normalize_driver_name(name, tournament_type='championship'):
    """Normalize team/player names for any sport, with fallback for aggressive cleaning."""
    if not name:
        return name
    
    # Clean the name first
    cleaned = clean_team_name(name)
    
    # If cleaning resulted in empty name, use original with minimal cleaning
    if not cleaned or len(cleaned.strip()) < 2:
        # Minimal cleaning: just strip whitespace and capitalize
        cleaned = name.strip()
        cleaned = ' '.join(word.capitalize() for word in cleaned.split())
        return cleaned
    
    # For all sports, return cleaned name with proper capitalization
    return ' '.join(word.capitalize() for word in cleaned.split())

def process_odds(odds_str):
    """Process odds: reduce by 25% and round down to nearest 0 or 5."""
    try:
        # Remove + or - sign and convert to integer
        is_positive = odds_str.startswith('+')
        odds_value = int(odds_str.replace('+', '').replace('-', ''))
        
        # For negative odds (favorites), we need to handle the reduction differently
        if not is_positive:  # Negative odds (favorites)
            # For favorites, reducing by 25% means making the odds less negative (closer to 0)
            processed_value = int(odds_value * 0.75)
        else:  # Positive odds (underdogs)
            # For underdogs, reducing by 25% means making the odds less positive
            processed_value = int(odds_value * 0.75)
        
        # Round down to nearest 0 or 5
        last_digit = processed_value % 10
        if last_digit in [1, 2, 3, 4]:
            processed_value = processed_value - last_digit  # Round down to 0
        elif last_digit in [6, 7, 8, 9]:
            processed_value = processed_value - last_digit + 5  # Round down to 5
        
        # Cap at 20000 (for positive odds) or -20000 (for negative odds)
        if is_positive and processed_value > 20000:
            processed_value = 20000
        elif not is_positive and processed_value > 20000:  # For negative odds, cap at -20000
            processed_value = 20000
        
        # Add back the sign
        return f"{'+' if is_positive else '-'}{processed_value}"
    except (ValueError, AttributeError):
        # If parsing fails, return original odds
        return odds_str

def find_cycling_data_with_regex(soup):
    """Find cycling data using regex patterns since the specific selectors don't work."""
    logger.info("🔍 Using regex patterns to find cycling data")
    
    odds_data = []
    seen_teams = set()
    
    # Get all text from the page
    all_text = soup.get_text()
    
    # Look for patterns like "Team Name +120" or "Team Name -150"
    # This is more flexible than looking for specific HTML elements
    patterns = [
        r'([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*([+-]\d+)',  # Team name followed by odds
        r'([A-Z][a-z]+ [A-Z][a-z]+)\s*([+-]\d+)',  # Simpler pattern
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, all_text)
        logger.info(f"🔍 Found {len(matches)} matches with pattern: {pattern}")
        
        for match in matches:
            team_name = match[0].strip()
            odds_value = match[1].strip()
            
            # Filter out common false positives
            if (len(team_name) > 3 and len(team_name) < 50 and 
                team_name not in ['Odds', 'Bet', 'Line', 'Point', 'Tour de France', 'DraftKings'] and
                ('+' in odds_value or '-' in odds_value) and
                team_name not in seen_teams):
                
                # Clean and normalize the team name
                cleaned_name = clean_team_name(team_name)
                normalized_name = normalize_driver_name(cleaned_name, 'championship')
                
                if normalized_name and normalized_name not in seen_teams:
                    processed_odds = process_odds(odds_value)
                    odds_data.append({
                        "team": normalized_name, 
                        "odds": processed_odds,
                        "original_odds": odds_value
                    })
                    seen_teams.add(normalized_name)
                    logger.info(f"✅ FOUND: {normalized_name} @ {odds_value} -> {processed_odds}")
    
    return odds_data

def find_cycling_data_with_alternative_selectors(soup):
    """Find cycling data using alternative selectors."""
    logger.info("🔍 Using alternative selectors to find cycling data")
    
    odds_data = []
    seen_teams = set()
    
    # Try different selectors that might work
    alternative_selectors = [
        # Look for any elements that might contain team names and odds
        'span[class*="title"]',
        'span[class*="odds"]',
        'span[class*="price"]',
        'span[class*="name"]',
        'div[class*="team"]',
        'div[class*="player"]',
        'div[class*="team"]',
        'div[class*="player"]',
        'div[class*="rider"]',
        # Look for any elements with data-testid that might be relevant
        'span[data-testid*="title"]',
        'span[data-testid*="odds"]',
        'span[data-testid*="price"]',
        'span[data-testid*="name"]',
        'div[data-testid*="card"]',
        'div[data-testid*="offer"]',
        # Look for buttons that might contain the data
        'button[data-testid*="title"]',
        'button[data-testid*="odds"]',
        'button[class*="title"]',
        'button[class*="odds"]',
    ]
    
    for selector in alternative_selectors:
        try:
            elements = soup.select(selector)
            if elements:
                logger.info(f"🔍 Found {len(elements)} elements with selector: {selector}")
                
                # Look for elements that contain both team names and odds
                for elem in elements:
                    text = elem.get_text(strip=True)
                    
                    # Check if this element contains both a team name and odds
                    if text and len(text) > 3:
                        # Look for odds pattern in the text
                        odds_match = re.search(r'([+-]\d+)', text)
                        if odds_match:
                            odds_value = odds_match.group(1)
                            # Extract team name (everything before the odds)
                            team_name = text[:odds_match.start()].strip()
                            
                            if (team_name and len(team_name) > 3 and 
                                team_name not in seen_teams and
                                team_name not in ['Odds', 'Bet', 'Line', 'Point']):
                                
                                # Clean and normalize the team name
                                cleaned_name = clean_team_name(team_name)
                                normalized_name = normalize_driver_name(cleaned_name, 'championship')
                                
                                if normalized_name and normalized_name not in seen_teams:
                                    processed_odds = process_odds(odds_value)
                                    odds_data.append({
                                        "team": normalized_name, 
                                        "odds": processed_odds,
                                        "original_odds": odds_value
                                    })
                                    seen_teams.add(normalized_name)
                                    logger.info(f"✅ FOUND: {normalized_name} @ {odds_value} -> {processed_odds}")
        except Exception as e:
            logger.debug(f"Selector {selector} failed: {e}")
            continue
    
    return odds_data

def test_fixed_scraper(url):
    """Test the fixed scraper with alternative methods."""
    logger.info(f"🔍 TESTING FIXED SCRAPER: {url}")
    
    driver = setup_driver(headless=True)
    try:
        logger.info(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        logger.info("⏳ Waiting for page to load...")
        time.sleep(10)  # Wait longer for dynamic content
        
        # Get page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        logger.info("🔍 TESTING FIXED SCRAPER:")
        logger.info("=" * 80)
        
        # Method 1: Try regex patterns
        logger.info("1️⃣ METHOD 1: Regex patterns")
        odds_data_regex = find_cycling_data_with_regex(soup)
        logger.info(f"Found {len(odds_data_regex)} entries using regex")
        
        # Method 2: Try alternative selectors
        logger.info("2️⃣ METHOD 2: Alternative selectors")
        odds_data_selectors = find_cycling_data_with_alternative_selectors(soup)
        logger.info(f"Found {len(odds_data_selectors)} entries using alternative selectors")
        
        # Combine results (avoiding duplicates)
        all_odds_data = []
        seen_teams = set()
        
        for entry in odds_data_regex + odds_data_selectors:
            team_name = entry['team']
            if team_name not in seen_teams:
                all_odds_data.append(entry)
                seen_teams.add(team_name)
        
        logger.info(f"🎯 TOTAL FOUND: {len(all_odds_data)} unique entries")
        
        # Show results
        logger.info("📊 RESULTS:")
        for i, entry in enumerate(all_odds_data):
            logger.info(f"  {i+1}. {entry['team']} @ {entry['odds']} (original: {entry['original_odds']})")
        
        return all_odds_data
        
    except Exception as e:
        logger.error(f"❌ Fixed scraper error: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        logger.info("🔚 Closing driver...")
        driver.quit()

def main():
    """Run fixed scraper test"""
    if len(sys.argv) < 2:
        print("Usage: python test_fixed_scraper.py <URL>")
        print("Example: python test_fixed_scraper.py 'https://sportsbook.draftkings.com/leagues/cycling/tour-de-france'")
        sys.exit(1)
    
    url = sys.argv[1]
    result = test_fixed_scraper(url)
    
    print("\n" + "=" * 80)
    print("🎯 FINAL RESULT:")
    print("=" * 80)
    
    if result:
        print(f"✅ SUCCESS: Found {len(result)} entries")
        for i, entry in enumerate(result):
            print(f"  {i+1}. {entry['team']} @ {entry['odds']} (original: {entry['original_odds']})")
    else:
        print("❌ FAILED: No entries found")

if __name__ == "__main__":
    main()
