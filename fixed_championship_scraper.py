#!/usr/bin/env python3
"""
Fixed championship scraper that uses working selectors and methods
"""

import re
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

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

def scrape_championship_odds_fixed(soup):
    """Fixed championship odds scraper that uses working methods."""
    logger.info("🎯 STARTING FIXED CHAMPIONSHIP ODDS SCRAPING")
    odds_data = []
    seen_teams = set()
    
    # Find tournament headers to detect boundaries
    tournament_headers = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
    logger.info(f"📋 Found {len(tournament_headers)} tournament headers on page")
    
    # Log all tournament headers for debugging
    for i, header in enumerate(tournament_headers):
        header_text = header.get_text(strip=True)
        logger.info(f"📋 Tournament header {i+1}: '{header_text}'")
    
    # Method 1: Try regex patterns to find team names and odds
    logger.info("🔍 METHOD 1: Using regex patterns to find cycling data")
    all_text = soup.get_text()
    
    # Look for patterns like "Team Name +120" or "Team Name -150"
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
    
    # Method 2: Try alternative selectors if regex didn't find enough data
    if len(odds_data) < 5:  # If we didn't find enough data with regex
        logger.info("🔍 METHOD 2: Using alternative selectors")
        
        # Try different selectors that might work
        alternative_selectors = [
            'span[class*="title"]',
            'span[class*="odds"]',
            'span[class*="price"]',
            'span[class*="name"]',
            'div[class*="team"]',
            'div[class*="player"]',
            'div[class*="rider"]',
            'span[data-testid*="title"]',
            'span[data-testid*="odds"]',
            'span[data-testid*="price"]',
            'span[data-testid*="name"]',
            'div[data-testid*="card"]',
            'div[data-testid*="offer"]',
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
    
    # Method 3: Text-based extraction as last resort
    if len(odds_data) < 5:  # If we still didn't find enough data
        logger.info("🔍 METHOD 3: Using text-based extraction")
        
        # Look for patterns like "Team Name +120" or "Team Name -150"
        patterns = [
            r'([A-Za-z\s]+?)\s*([+-]\d+)',  # Team name followed by odds
            r'([A-Za-z\s]+?)\s*(\+\d+|\-\d+)',  # More specific odds pattern
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text)
            logger.info(f"🔍 Found {len(matches)} matches with pattern: {pattern}")
            
            for match in matches:
                team_name = match[0].strip()
                odds_value = match[1].strip()
                
                # Filter out common false positives and check for duplicates
                if (len(team_name) > 3 and len(team_name) < 50 and 
                    team_name not in ['Odds', 'Bet', 'Line', 'Point'] and
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
    
    if not odds_data:
        logger.warning("❌ No odds data found with any method")
    
    logger.info(f"🎯 FINAL RESULT: {len(odds_data)} unique teams scraped")
    return odds_data
