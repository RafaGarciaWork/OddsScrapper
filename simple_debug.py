#!/usr/bin/env python3
"""
Simple debug script to find any elements that might contain team names and odds
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

def find_any_elements_with_text(soup, text_patterns):
    """Find any elements that contain text matching the patterns."""
    logger.info(f"🔍 Looking for elements containing: {text_patterns}")
    
    found_elements = []
    
    # Look for any element that contains the text
    for pattern in text_patterns:
        elements = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
        for elem in elements:
            parent = elem.parent
            if parent:
                found_elements.append({
                    'tag': parent.name,
                    'text': elem.strip(),
                    'parent_text': parent.get_text(strip=True),
                    'classes': parent.get('class', []),
                    'data_testid': parent.get('data-testid', ''),
                    'id': parent.get('id', '')
                })
    
    return found_elements

def simple_debug_scrape(url):
    """Simple debug scraper that tries to find any relevant data."""
    logger.info(f"🔍 SIMPLE DEBUG SCRAPING: {url}")
    
    driver = setup_driver(headless=True)
    try:
        logger.info(f"🌐 Navigating to: {url}")
        driver.get(url)
        
        # Wait for page to load
        logger.info("⏳ Waiting for page to load...")
        time.sleep(10)  # Wait longer
        
        # Get page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        logger.info("🔍 PAGE ANALYSIS:")
        logger.info("=" * 80)
        
        # Check page title
        title = soup.find('title')
        if title:
            logger.info(f"📄 PAGE TITLE: '{title.get_text()}'")
        
        # Check for any elements with data-testid
        testid_elements = soup.find_all(attrs={"data-testid": True})
        logger.info(f"🔍 Found {len(testid_elements)} elements with data-testid")
        
        # Show unique data-testid values
        unique_testids = set()
        for elem in testid_elements:
            testid = elem.get('data-testid', '')
            if testid:
                unique_testids.add(testid)
        
        logger.info(f"🔍 Unique data-testid values ({len(unique_testids)}):")
        for testid in sorted(unique_testids):
            logger.info(f"  - {testid}")
        
        # Look for any elements that might contain team names
        logger.info("\n🔍 LOOKING FOR TEAM NAMES:")
        team_patterns = [
            'tadej pogacar', 'jonas vingegaard', 'remco evenepoel', 'primoz roglic',
            'cycling', 'tour de france', 'cyclist', 'rider'
        ]
        
        team_elements = find_any_elements_with_text(soup, team_patterns)
        logger.info(f"Found {len(team_elements)} potential team elements")
        
        for i, elem in enumerate(team_elements[:10]):  # Show first 10
            logger.info(f"  {i+1}. {elem['tag']} - '{elem['text']}' (testid: {elem['data_testid']})")
        
        # Look for any elements that might contain odds
        logger.info("\n🔍 LOOKING FOR ODDS:")
        odds_patterns = [
            r'[+-]\d+',  # +120, -150, etc.
            r'\d+:\d+',   # 2:1, 3:1, etc.
            r'\d+\.\d+',  # 2.5, 3.2, etc.
        ]
        
        odds_elements = []
        for pattern in odds_patterns:
            elements = soup.find_all(string=re.compile(pattern))
            for elem in elements:
                parent = elem.parent
                if parent:
                    odds_elements.append({
                        'tag': parent.name,
                        'text': elem.strip(),
                        'parent_text': parent.get_text(strip=True),
                        'classes': parent.get('class', []),
                        'data_testid': parent.get('data-testid', ''),
                        'id': parent.get('id', '')
                    })
        
        logger.info(f"Found {len(odds_elements)} potential odds elements")
        
        for i, elem in enumerate(odds_elements[:10]):  # Show first 10
            logger.info(f"  {i+1}. {elem['tag']} - '{elem['text']}' (testid: {elem['data_testid']})")
        
        # Look for any buttons or clickable elements
        logger.info("\n🔍 LOOKING FOR BUTTONS/CLICKABLE ELEMENTS:")
        buttons = soup.find_all(['button', 'a', 'div'], class_=lambda x: x and any(term in str(x).lower() for term in ['button', 'click', 'bet', 'odds', 'market']))
        logger.info(f"Found {len(buttons)} potential buttons/clickable elements")
        
        for i, button in enumerate(buttons[:10]):  # Show first 10
            text = button.get_text(strip=True)
            classes = button.get('class', [])
            testid = button.get('data-testid', '')
            logger.info(f"  {i+1}. {button.name} - '{text}' (classes: {classes}, testid: {testid})")
        
        # Check if page contains expected content
        logger.info("\n🔍 CONTENT VERIFICATION:")
        page_text = soup.get_text().lower()
        
        expected_content = [
            'tour de france', 'cycling', 'tadej pogacar', 'jonas vingegaard',
            'odds', 'betting', 'sportsbook', 'draftkings'
        ]
        
        for content in expected_content:
            if content in page_text:
                logger.info(f"  ✅ Found: '{content}'")
            else:
                logger.info(f"  ❌ Missing: '{content}'")
        
        # Look for any error messages
        error_indicators = [
            'error', 'not found', '404', 'access denied', 'blocked',
            'unavailable', 'maintenance', 'coming soon', 'geoblocked'
        ]
        
        for indicator in error_indicators:
            if indicator in page_text:
                logger.warning(f"  ⚠️ Found error indicator: '{indicator}'")
        
        # Try to find any elements that might be the ones we need
        logger.info("\n🔍 TRYING ALTERNATIVE SELECTORS:")
        alternative_selectors = [
            'span[data-testid*="title"]',
            'span[data-testid*="odds"]',
            'span[data-testid*="market"]',
            'span[data-testid*="button"]',
            'div[data-testid*="card"]',
            'div[data-testid*="offer"]',
            'button[data-testid*="title"]',
            'button[data-testid*="odds"]',
            'span[class*="title"]',
            'span[class*="odds"]',
            'span[class*="price"]',
            'span[class*="name"]',
            'div[class*="team"]',
            'div[class*="player"]',
            'div[class*="rider"]'
        ]
        
        for selector in alternative_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"  ✅ {selector}: {len(elements)} elements")
                    # Show first 3 elements
                    for i, elem in enumerate(elements[:3]):
                        text = elem.get_text(strip=True)
                        logger.info(f"    {i+1}. '{text}'")
                else:
                    logger.info(f"  ❌ {selector}: 0 elements")
            except Exception as e:
                logger.info(f"  ❌ {selector}: Error - {e}")
        
        logger.info("\n🔍 SIMPLE DEBUG COMPLETE")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Simple debug error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        logger.info("🔚 Closing driver...")
        driver.quit()

def main():
    """Run simple debug scraper"""
    if len(sys.argv) < 2:
        print("Usage: python simple_debug.py <URL>")
        print("Example: python simple_debug.py 'https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026'")
        sys.exit(1)
    
    url = sys.argv[1]
    simple_debug_scrape(url)

if __name__ == "__main__":
    main()
