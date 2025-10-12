#!/usr/bin/env python3
"""
Page inspector to see what elements are actually available on the page
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

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver(headless=False):  # Set to False to see the browser
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
    # options.add_argument('--disable-images')  # Comment out to see images
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logger.warning(f"Failed to use webdriver-manager: {e}")
        driver = webdriver.Chrome(options=options)
    
    return driver

def inspect_page(url):
    """Inspect the page to see what elements are actually available."""
    logger.info(f"🔍 INSPECTING PAGE: {url}")
    
    driver = setup_driver(headless=False)  # Set to False to see the browser
    try:
        logger.info(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        logger.info("⏳ Waiting for page to load...")
        time.sleep(5)
        
        # Take a screenshot for debugging
        try:
            driver.save_screenshot("page_screenshot.png")
            logger.info("📸 Screenshot saved as page_screenshot.png")
        except Exception as e:
            logger.warning(f"Could not save screenshot: {e}")
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        logger.info("🔍 PAGE INSPECTION RESULTS:")
        logger.info("=" * 80)
        
        # Check for various selectors
        selectors_to_check = [
            'span[data-testid="button-title-market-board"]',
            'span[data-testid="button-odds-market-board"]',
            'span[data-testid*="button-title"]',
            'span[data-testid*="button-odds"]',
            'span[data-testid*="title"]',
            'span[data-testid*="odds"]',
            'span[data-testid*="market"]',
            'div[data-testid="offer-card"]',
            '.market-board-item',
            '.sportsbook-table-row',
            'span[class*="title"]',
            'span[class*="odds"]',
            'span[class*="price"]',
            'button[data-testid*="title"]',
            'button[data-testid*="odds"]'
        ]
        
        for selector in selectors_to_check:
            elements = soup.select(selector)
            logger.info(f"🔍 Selector '{selector}': {len(elements)} elements found")
            if elements and len(elements) <= 5:  # Show first 5 elements
                for i, elem in enumerate(elements[:5]):
                    text = elem.get_text(strip=True)
                    logger.info(f"  {i+1}. '{text}'")
        
        # Look for any elements with data-testid
        logger.info("\n🔍 ALL ELEMENTS WITH data-testid:")
        testid_elements = soup.find_all(attrs={"data-testid": True})
        logger.info(f"Found {len(testid_elements)} elements with data-testid")
        
        # Group by data-testid value
        testid_groups = {}
        for elem in testid_elements:
            testid = elem.get('data-testid', '')
            if testid not in testid_groups:
                testid_groups[testid] = []
            testid_groups[testid].append(elem)
        
        # Show unique data-testid values
        logger.info("\n🔍 UNIQUE data-testid VALUES:")
        for testid, elements in testid_groups.items():
            logger.info(f"  '{testid}': {len(elements)} elements")
            if len(elements) <= 3:  # Show first 3 examples
                for i, elem in enumerate(elements[:3]):
                    text = elem.get_text(strip=True)
                    logger.info(f"    {i+1}. '{text}'")
        
        # Look for tournament headers
        logger.info("\n🔍 TOURNAMENT HEADERS:")
        tournament_headers = soup.find_all("div", class_="cb-title__simple-title cb-title__nav-title")
        logger.info(f"Found {len(tournament_headers)} tournament headers")
        for i, header in enumerate(tournament_headers):
            header_text = header.get_text(strip=True)
            logger.info(f"  {i+1}. '{header_text}'")
        
        # Look for any text that might contain team names or odds
        logger.info("\n🔍 SEARCHING FOR POTENTIAL TEAM NAMES AND ODDS:")
        all_text = soup.get_text()
        
        # Look for patterns that might be team names
        import re
        potential_teams = re.findall(r'[A-Z][a-z]+ [A-Z][a-z]+', all_text)
        unique_teams = list(set(potential_teams))[:20]  # First 20 unique
        logger.info(f"Found {len(unique_teams)} potential team names:")
        for team in unique_teams:
            logger.info(f"  - {team}")
        
        # Look for odds patterns
        odds_patterns = re.findall(r'[+-]\d+', all_text)
        unique_odds = list(set(odds_patterns))[:20]  # First 20 unique
        logger.info(f"Found {len(unique_odds)} potential odds:")
        for odd in unique_odds:
            logger.info(f"  - {odd}")
        
        # Check if page contains expected content
        logger.info("\n🔍 PAGE CONTENT ANALYSIS:")
        page_text = soup.get_text().lower()
        
        keywords_to_check = [
            'tour de france', 'cycling', 'tadej pogacar', 'jonas vingegaard',
            'odds', 'betting', 'sportsbook', 'draftkings'
        ]
        
        for keyword in keywords_to_check:
            if keyword in page_text:
                logger.info(f"  ✅ Found keyword: '{keyword}'")
            else:
                logger.info(f"  ❌ Missing keyword: '{keyword}'")
        
        # Check page title
        title = soup.find('title')
        if title:
            logger.info(f"\n🔍 PAGE TITLE: '{title.get_text()}'")
        
        # Check for error messages
        error_indicators = [
            'error', 'not found', '404', 'access denied', 'blocked',
            'unavailable', 'maintenance', 'coming soon'
        ]
        
        for indicator in error_indicators:
            if indicator in page_text:
                logger.warning(f"  ⚠️ Found error indicator: '{indicator}'")
        
        logger.info("\n🔍 INSPECTION COMPLETE")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Inspection error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("🔚 Closing driver...")
        driver.quit()

def main():
    """Run page inspector"""
    if len(sys.argv) < 2:
        print("Usage: python debug_page_inspector.py <URL>")
        print("Example: python debug_page_inspector.py 'https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026'")
        sys.exit(1)
    
    url = sys.argv[1]
    inspect_page(url)

if __name__ == "__main__":
    main()
