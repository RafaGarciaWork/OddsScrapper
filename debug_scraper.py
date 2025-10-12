#!/usr/bin/env python3
"""
Debug version of the scraper with comprehensive logging to track data flow
"""

from flask import Flask, request, jsonify
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

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_team_name(team_name):
    """Clean team/driver names by removing unwanted prefixes and suffixes."""
    logger.debug(f"🔧 CLEANING: Input team name: '{team_name}'")
    
    if not team_name:
        logger.debug(f"🔧 CLEANING: Empty input, returning as-is")
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
        'AMRACE Winner',
        'AMRACE',
        'Race Winner',
        'Race',
        'Finish ',
        'Finish To',
        'Finish Winner',
        'Finish Lando',
        'Finish Max',
        'Finish Oscar',
        'Finish George',
        'Finish Charles',
        'Finish Lewis',
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
    logger.debug(f"🔧 CLEANING: After strip: '{cleaned_name}'")
    
    # Remove prefixes (case insensitive) - try multiple times to catch nested prefixes
    max_iterations = 5
    for iteration in range(max_iterations):
        original_name = cleaned_name
        for prefix in unwanted_prefixes:
            if cleaned_name.lower().startswith(prefix.lower()):
                cleaned_name = cleaned_name[len(prefix):].strip()
                logger.debug(f"🔧 CLEANING: Removed prefix '{prefix}' -> '{cleaned_name}'")
                break
        if cleaned_name == original_name:  # No more prefixes to remove
            break
    
    # Remove suffixes (case insensitive)
    for suffix in unwanted_suffixes:
        if cleaned_name.lower().endswith(suffix.lower()):
            cleaned_name = cleaned_name[:-len(suffix)].strip()
            logger.debug(f"🔧 CLEANING: Removed suffix '{suffix}' -> '{cleaned_name}'")
    
    # Clean up any extra spaces and special characters
    cleaned_name = ' '.join(cleaned_name.split())
    
    # Remove any remaining unwanted patterns
    unwanted_patterns = [
        r'^Finish\s*',
        r'\s+Finish$',
        r'^To\s+Finish\s+',
        r'^To\s+Win\s+',
        r'^AMRace\s+Winner\s*',
        r'^AMRACE\s+Winner\s*',
        r'^Race\s+Winner\s*',
    ]
    
    import re
    for pattern in unwanted_patterns:
        old_name = cleaned_name
        cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE).strip()
        if cleaned_name != old_name:
            logger.debug(f"🔧 CLEANING: Removed pattern '{pattern}' -> '{cleaned_name}'")
    
    logger.debug(f"🔧 CLEANING: Final result: '{team_name}' -> '{cleaned_name}'")
    return cleaned_name

def normalize_driver_name(name, tournament_type='championship'):
    """Normalize team/player names for any sport, with fallback for aggressive cleaning."""
    logger.debug(f"🔄 NORMALIZING: Input: '{name}', tournament_type: '{tournament_type}'")
    
    if not name:
        logger.debug(f"🔄 NORMALIZING: Empty input, returning as-is")
        return name
    
    # Clean the name first
    cleaned = clean_team_name(name)
    logger.debug(f"🔄 NORMALIZING: After cleaning: '{cleaned}'")
    
    # If cleaning resulted in empty name, use original with minimal cleaning
    if not cleaned or len(cleaned.strip()) < 2:
        logger.warning(f"🔄 NORMALIZING: Cleaned name empty or too short, using original with minimal cleaning")
        # Minimal cleaning: just strip whitespace and capitalize
        cleaned = name.strip()
        cleaned = ' '.join(word.capitalize() for word in cleaned.split())
        logger.debug(f"🔄 NORMALIZING: Minimal cleaning result: '{cleaned}'")
        return cleaned
    
    # For auto racing (F1), try to match against known drivers
    if tournament_type == 'auto_racing':
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
                result = ' '.join(word.capitalize() for word in driver.split())
                logger.debug(f"🔄 NORMALIZING: F1 driver match: '{name}' -> '{result}'")
                return result
    
    # For all other sports (cycling, etc.), return cleaned name with proper capitalization
    result = ' '.join(word.capitalize() for word in cleaned.split())
    logger.debug(f"🔄 NORMALIZING: Final result: '{name}' -> '{result}'")
    return result

def process_odds(odds_str):
    """Process odds: reduce by 25% and round down to nearest 0 or 5."""
    logger.debug(f"💰 PROCESSING ODDS: Input: '{odds_str}'")
    
    try:
        # Remove + or - sign and convert to integer
        is_positive = odds_str.startswith('+')
        odds_value = int(odds_str.replace('+', '').replace('-', ''))
        logger.debug(f"💰 PROCESSING ODDS: Parsed value: {odds_value}, is_positive: {is_positive}")
        
        # For negative odds (favorites), we need to handle the reduction differently
        if not is_positive:  # Negative odds (favorites)
            # For favorites, reducing by 25% means making the odds less negative (closer to 0)
            # So we multiply by 0.75, but since it's negative, this makes it less negative
            processed_value = int(odds_value * 0.75)
            logger.debug(f"💰 PROCESSING ODDS: Negative odds reduction: {odds_value} * 0.75 = {processed_value}")
        else:  # Positive odds (underdogs)
            # For underdogs, reducing by 25% means making the odds less positive
            processed_value = int(odds_value * 0.75)
            logger.debug(f"💰 PROCESSING ODDS: Positive odds reduction: {odds_value} * 0.75 = {processed_value}")
        
        # Round down to nearest 0 or 5
        # If last digit is 1-4, round down to 0
        # If last digit is 6-9, round down to 5
        last_digit = processed_value % 10
        if last_digit in [1, 2, 3, 4]:
            processed_value = processed_value - last_digit  # Round down to 0
            logger.debug(f"💰 PROCESSING ODDS: Rounded down to 0: {processed_value}")
        elif last_digit in [6, 7, 8, 9]:
            processed_value = processed_value - last_digit + 5  # Round down to 5
            logger.debug(f"💰 PROCESSING ODDS: Rounded down to 5: {processed_value}")
        # If last digit is 0 or 5, keep as is
        
        # Cap at 20000 (for positive odds) or -20000 (for negative odds)
        if is_positive and processed_value > 20000:
            processed_value = 20000
            logger.debug(f"💰 PROCESSING ODDS: Capped positive odds at 20000")
        elif not is_positive and processed_value > 20000:  # For negative odds, cap at -20000
            processed_value = 20000
            logger.debug(f"💰 PROCESSING ODDS: Capped negative odds at -20000")
        
        # Add back the sign
        result = f"{'+' if is_positive else '-'}{processed_value}"
        logger.debug(f"💰 PROCESSING ODDS: Final result: '{odds_str}' -> '{result}'")
        return result
    except (ValueError, AttributeError) as e:
        # If parsing fails, return original odds
        logger.warning(f"💰 PROCESSING ODDS: Failed to parse '{odds_str}': {e}, returning original")
        return odds_str

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

def scrape_championship_odds_debug(soup):
    """Debug version of championship odds scraping with detailed logging."""
    logger.info("🎯 STARTING CHAMPIONSHIP ODDS SCRAPING")
    odds_data = []
    seen_teams = set()
    
    # Find tournament headers to detect boundaries
    tournament_headers = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    logger.info(f"📋 Found {len(tournament_headers)} tournament headers on page")
    
    # Log all tournament headers for debugging
    for i, header in enumerate(tournament_headers):
        header_text = header.get_text(strip=True)
        logger.info(f"📋 Tournament header {i+1}: '{header_text}'")
    
    # Method 1: Try the working selectors from V1
    logger.info("🔍 STEP 1: Looking for team and odds elements")
    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    logger.info(f"🔍 Found {len(team_elements)} team elements and {len(odds_elements)} odds elements")
    
    if team_elements and odds_elements:
        logger.info("✅ STEP 1 SUCCESS: Found elements using V1 selectors")
        
        # Log raw scraped data for debugging
        logger.info("📊 RAW SCRAPED DATA (first 10 teams):")
        for i, team in enumerate(team_elements[:10]):
            team_text = team.get_text(strip=True)
            logger.info(f"📊 Team {i+1}: '{team_text}'")
        
        logger.info("📊 RAW SCRAPED DATA (first 10 odds):")
        for i, odd in enumerate(odds_elements[:10]):
            odd_text = odd.get_text(strip=True)
            logger.info(f"📊 Odds {i+1}: '{odd_text}'")
        
        # Determine which tournament section to scrape
        target_tournament_index = 0
        max_entries = min(len(team_elements), len(odds_elements), 25)
        
        logger.info(f"🎯 Processing {max_entries} entries from tournament {target_tournament_index + 1}")
        
        for i, (team, odd) in enumerate(zip(team_elements[:max_entries], odds_elements[:max_entries])):
            logger.info(f"🔄 PROCESSING ENTRY {i+1}:")
            
            # Get raw data
            raw_team_name = team.get_text(strip=True)
            raw_odds = odd.get_text(strip=True)
            logger.info(f"🔄 Raw team name: '{raw_team_name}'")
            logger.info(f"🔄 Raw odds: '{raw_odds}'")
            
            # Clean team name
            cleaned_team_name = clean_team_name(raw_team_name)
            logger.info(f"🔄 Cleaned team name: '{cleaned_team_name}'")
            
            # Process odds
            processed_odds = process_odds(raw_odds)
            logger.info(f"🔄 Processed odds: '{processed_odds}'")
            
            # Normalize the driver name
            normalized_name = normalize_driver_name(cleaned_team_name, 'championship')
            logger.info(f"🔄 Normalized name: '{normalized_name}'")
            
            # Enhanced tournament boundary detection
            tournament_indicators = [
                'las vegas', 'miami', 'monaco', 'silverstone', 'spa', 'monza', 'spain', 'france',
                'austria', 'hungary', 'belgium', 'netherlands', 'singapore', 'japan', 'australia',
                'bahrain', 'saudi', 'qatar', 'abu dhabi', 'brazil', 'mexico', 'canada', 'azerbaijan',
                'china', 'russia', 'portugal', 'turkey', 'imola', 'emilia', 'romagna', 'usa gp', 'usa grand prix'
            ]
            
            # Check if team name suggests we're in a different tournament
            if any(indicator in cleaned_team_name.lower() for indicator in tournament_indicators):
                if i > 5:  # Only stop if we've already scraped some entries
                    logger.info(f"🛑 Stopping at element {i} - detected different tournament: {cleaned_team_name}")
                    break
            
            # Filter out common betting interface text patterns
            betting_interface_patterns = [
                'if the odds are', 'if odds are', 'odds are', 'betting odds', 'current odds',
                'live odds', 'updated odds', 'new odds', 'latest odds', 'odds update',
                'bet now', 'place bet', 'betting line', 'betting market', 'betting option',
                'click to bet', 'bet here', 'wagering', 'gambling', 'sportsbook'
            ]
            
            if any(pattern in cleaned_team_name.lower() for pattern in betting_interface_patterns):
                logger.info(f"🚫 Skipping betting interface text: {cleaned_team_name}")
                continue
            
            # Check for tournament name patterns that suggest we're in next week's tournament
            next_week_indicators = [
                'next week', 'upcoming', 'future', 'next race', 'next grand prix',
                'next tournament', 'next event', 'next round'
            ]
            
            if any(indicator in cleaned_team_name.lower() for indicator in next_week_indicators):
                if i > 5:  # Only stop if we've already scraped some entries
                    logger.info(f"🛑 Stopping at element {i} - detected next week tournament: {cleaned_team_name}")
                    break
            
            # Check for duplicates using normalized name
            if normalized_name and normalized_name not in seen_teams:
                # Include player even if they don't have odds
                if raw_odds:
                    odds_data.append({
                        "team": normalized_name, 
                        "odds": processed_odds,
                        "original_odds": raw_odds
                    })
                    logger.info(f"✅ ADDED: {normalized_name} @ {raw_odds} -> {processed_odds}")
                else:
                    # Player exists but has no odds - include with empty odds
                    odds_data.append({
                        "team": normalized_name, 
                        "odds": "",
                        "original_odds": ""
                    })
                    logger.info(f"✅ ADDED (no odds): {normalized_name}")
                
                seen_teams.add(normalized_name)
            elif normalized_name in seen_teams:
                logger.info(f"🔄 SKIPPED DUPLICATE: {normalized_name}")
            else:
                logger.warning(f"❌ SKIPPED INVALID: normalized_name='{normalized_name}', raw_team='{raw_team_name}'")
    
    # Method 2: Fallback to generic selectors if V1 method fails
    if not odds_data:
        logger.info("🔄 STEP 2: Trying fallback selectors...")
        
        # Look for common DraftKings patterns
        offer_cards = soup.find_all('div', {'data-testid': 'offer-card'})
        if not offer_cards:
            offer_cards = soup.find_all('div', class_=lambda x: x and 'offer' in x.lower())
        
        logger.info(f"🔄 Found {len(offer_cards)} offer cards")
        
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
                    
                    logger.info(f"🔄 FALLBACK: Found team='{team_name}', odds='{odds_value}'")
                    
                    # Filter out common betting interface text patterns
                    betting_interface_patterns = [
                        'if the odds are', 'if odds are', 'odds are', 'betting odds', 'current odds',
                        'live odds', 'updated odds', 'new odds', 'latest odds', 'odds update',
                        'bet now', 'place bet', 'betting line', 'betting market', 'betting option',
                        'click to bet', 'bet here', 'wagering', 'gambling', 'sportsbook'
                    ]
                    
                    if any(pattern in team_name.lower() for pattern in betting_interface_patterns):
                        logger.info(f"🚫 FALLBACK: Skipping betting interface text: {team_name}")
                        continue
                    
                    # Validate odds format and check for duplicates
                    if (team_name and odds_value and ('+' in odds_value or '-' in odds_value) 
                        and team_name not in seen_teams):
                        processed_odds = process_odds(odds_value)
                        odds_data.append({
                            "team": team_name, 
                            "odds": processed_odds,
                            "original_odds": odds_value
                        })
                        seen_teams.add(team_name)
                        logger.info(f"✅ FALLBACK ADDED: {team_name} @ {odds_value} -> {processed_odds}")
                    elif team_name in seen_teams:
                        logger.info(f"🔄 FALLBACK SKIPPED DUPLICATE: {team_name}")
            
            except Exception as e:
                logger.warning(f"❌ FALLBACK: Error processing card: {e}")
    
    # Method 3: Text-based extraction as last resort
    if not odds_data:
        logger.info("🔄 STEP 3: Trying text-based extraction...")
        all_text = soup.get_text()
        
        # Look for patterns like "Team Name +120" or "Team Name -150"
        import re
        patterns = [
            r'([A-Za-z\s]+?)\s*([+-]\d+)',  # Team name followed by odds
            r'([A-Za-z\s]+?)\s*(\+\d+|\-\d+)',  # More specific odds pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text)
            logger.info(f"🔄 TEXT-BASED: Found {len(matches)} matches with pattern: {pattern}")
            
            for match in matches:
                team_name = match[0].strip()
                odds_value = match[1].strip()
                
                logger.info(f"🔄 TEXT-BASED: Found team='{team_name}', odds='{odds_value}'")
                
                # Filter out common betting interface text patterns
                betting_interface_patterns = [
                    'if the odds are', 'if odds are', 'odds are', 'betting odds', 'current odds',
                    'live odds', 'updated odds', 'new odds', 'latest odds', 'odds update',
                    'bet now', 'place bet', 'betting line', 'betting market', 'betting option',
                    'click to bet', 'bet here', 'wagering', 'gambling', 'sportsbook'
                ]
                
                if any(pattern in team_name.lower() for pattern in betting_interface_patterns):
                    logger.info(f"🚫 TEXT-BASED: Skipping betting interface text: {team_name}")
                    continue
                
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
                    logger.info(f"✅ TEXT-BASED ADDED: {team_name} @ {odds_value} -> {processed_odds}")
                elif team_name in seen_teams:
                    logger.info(f"🔄 TEXT-BASED SKIPPED DUPLICATE: {team_name}")
    
    if not odds_data:
        logger.warning("❌ No odds data found. Page structure might have changed.")
    
    # Final deduplication check (extra safety)
    final_odds_data = []
    final_seen_teams = set()
    
    for item in odds_data:
        team_name = item["team"]
        if team_name not in final_seen_teams:
            final_odds_data.append(item)
            final_seen_teams.add(team_name)
        else:
            logger.info(f"🔄 FINAL DEDUP: Skipping duplicate {team_name}")
    
    logger.info(f"🎯 FINAL RESULT: {len(final_odds_data)} unique teams scraped")
    return final_odds_data

def scrape_draftkings_odds_debug(url, event_type="championship"):
    """Debug version of DraftKings odds scraper with detailed logging."""
    logger.info(f"🚀 STARTING DEBUG SCRAPING: {url} with event_type: {event_type}")
    
    driver = setup_driver(headless=True)
    try:
        logger.info(f"🌐 Navigating to: {url}")
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
                logger.info(f"✅ Found elements with selector: {selector}")
                element_found = True
                break
            except:
                continue
        
        if not element_found:
            logger.warning("❌ No elements found with any selector")
            return []
        
        # Wait a bit more for dynamic content
        logger.info("⏳ Waiting for dynamic content to load...")
        time.sleep(random.uniform(2, 4))
        
        # Parse the HTML
        logger.info("🔍 Parsing HTML content...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Route to appropriate scraper based on event type
        if event_type == "conference":
            logger.info("📊 Using conference scraper...")
            return scrape_conference_odds_debug(soup)
        elif event_type == "division":
            logger.info("📊 Using division scraper...")
            return scrape_division_odds_debug(soup)
        else:  # championship or unknown
            logger.info("📊 Using championship scraper...")
            return scrape_championship_odds_debug(soup)
    
    except Exception as e:
        logger.error(f"❌ Scraping error: {e}")
        return []
    
    finally:
        logger.info("🔚 Closing driver...")
        driver.quit()

def scrape_conference_odds_debug(soup):
    """Debug version of conference odds scraping."""
    logger.info("📊 CONFERENCE ODDS SCRAPING")
    team_spans = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_spans = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    logger.info(f"📊 Found {len(team_spans)} team spans and {len(odds_spans)} odds spans")
    
    # Create teams list with bounds checking
    teams = [
        {"team": team_span.get_text(strip=True), "odds": odds_spans[i].get_text(strip=True)}
        for i, team_span in enumerate(team_spans)
        if i < len(odds_spans)
    ]
    
    logger.info(f"📊 Created {len(teams)} team entries")
    
    # Process odds for all teams
    for team in teams:
        team["processed_odds"] = process_odds(team["odds"])
        team["original_odds"] = team["odds"]
        team["odds"] = team["processed_odds"]
        logger.info(f"📊 Processed: {team['team']} @ {team['original_odds']} -> {team['odds']}")
    
    # Split teams into conferences (first half = NFC, second half = AFC)
    total_teams = len(teams)
    mid_point = total_teams // 2
    
    conferences = [
        {"conference": "NFC", "teams": teams[:mid_point]},
        {"conference": "AFC", "teams": teams[mid_point:]}
    ]
    
    logger.info(f"📊 Conference scraping: {len(conferences)} conferences, {total_teams} total teams")
    
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

def scrape_division_odds_debug(soup):
    """Debug version of division odds scraping."""
    logger.info("📊 DIVISION ODDS SCRAPING")
    division_titles = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    team_spans = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_spans = soup.find_all("span", {"data-testid": "button-odds-market-board"})
    
    logger.info(f"📊 Found {len(division_titles)} division titles, {len(team_spans)} team spans, {len(odds_spans)} odds spans")
    
    # Create teams list with bounds checking
    teams = [
        {"team": clean_team_name(team_span.get_text(strip=True)), "odds": odds_spans[i].get_text(strip=True)}
        for i, team_span in enumerate(team_spans)
        if i < len(odds_spans)
    ]
    
    logger.info(f"📊 Created {len(teams)} team entries")
    
    # Process odds for all teams
    for team in teams:
        team["processed_odds"] = process_odds(team["odds"])
        team["original_odds"] = team["odds"]
        team["odds"] = team["processed_odds"]
        logger.info(f"📊 Processed: {team['team']} @ {team['original_odds']} -> {team['odds']}")
    
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
            logger.info(f"📊 Division {i+1}: {conference} {division} with {len(division_teams)} teams")
    
    logger.info(f"📊 Division scraping: {len(divisions)} divisions, {len(teams)} total teams")
    
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

@app.route('/api/debug-scrape', methods=['POST'])
def debug_scrape_url():
    """Debug API endpoint to scrape a single URL with comprehensive logging."""
    try:
        data = request.get_json()
        url = data.get('url')
        event_type = data.get('event_type', 'championship')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"🎯 DEBUG API REQUEST: {url} with event_type: {event_type}")
        
        # Scrape the URL with debug logging
        odds = scrape_draftkings_odds_debug(url, event_type)
        
        logger.info(f"🎯 DEBUG SCRAPING COMPLETE: Found {len(odds) if isinstance(odds, list) else 'structured data'}")
        
        return jsonify({
            'success': True,
            'url': url,
            'event_type': event_type,
            'odds': odds,
            'count': len(odds) if isinstance(odds, list) else 'structured data'
        })
        
    except Exception as e:
        logger.error(f"❌ DEBUG API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/debug-status')
def debug_status():
    """Debug API endpoint to check server status."""
    return jsonify({
        'status': 'running',
        'timestamp': time.time(),
        'version': 'debug-1.0.0'
    })

if __name__ == '__main__':
    logger.info("🚀 Starting Debug Scraper Server...")
    app.run(debug=True, host='0.0.0.0', port=5001)
