import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, request
import json
import time

class BetOnlineScraper:
    def __init__(self):
        self.base_urls = {
            'championship': 'https://www.betonline.ag/sportsbook/futures-and-props/ncaaf-futures/college-football-championship',
            'heisman': 'https://www.betonline.ag/sportsbook/futures-and-props/ncaaf-futures/heisman-trophy'
        }
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def click_show_more(self):
        """Click 'Show More' buttons to reveal all betting options"""
        try:
            show_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, '.show-more')
            for button in show_more_buttons:
                if button.is_displayed():
                    self.driver.execute_script("arguments,[object Object],click();", button)
                    time.sleep(1)  # Wait for content to load
        except Exception as e:
            print(f"Error clicking show more: {e}")
    
    def scrape_championship_odds(self):
        """Scrape college football championship odds"""
        try:
            self.driver.get(self.base_urls['championship'])
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.text-component'))
            )
            
            # Click show more to reveal all teams
            self.click_show_more()
            time.sleep(2)
            
            teams_data = []
            
            # Find all team name elements
            team_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'p.text-component.small.no-truncated.left.color-primary'
            )
            
            # Find all odds elements
            odds_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'p.text-component.small.bold.no-truncated.center.color-link'
            )
            
            # Pair teams with their odds
            for i in range(min(len(team_elements), len(odds_elements))):
                team_name = team_elements[i].text.strip()
                odds = odds_elements[i].text.strip()
                
                if team_name and odds:
                    teams_data.append({
                        'team': team_name,
                        'odds': odds,
                        'type': 'championship'
                    })
            
            return teams_data
            
        except Exception as e:
            print(f"Error scraping championship odds: {e}")
            return []
    
    def scrape_heisman_odds(self):
        """Scrape Heisman Trophy odds"""
        try:
            self.driver.get(self.base_urls['heisman'])
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.text-component'))
            )
            
            # Click show more to reveal all players
            self.click_show_more()
            time.sleep(2)
            
            players_data = []
            
            # Find all player name elements
            player_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'p.text-component.small.no-truncated.left.color-primary'
            )
            
            # Find all odds elements
            odds_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'p.text-component.small.bold.no-truncated.center.color-link'
            )
            
            # Pair players with their odds
            for i in range(min(len(player_elements), len(odds_elements))):
                player_name = player_elements[i].text.strip()
                odds = odds_elements[i].text.strip()
                
                if player_name and odds:
                    players_data.append({
                        'player': player_name,
                        'odds': odds,
                        'type': 'heisman'
                    })
            
            return players_data
            
        except Exception as e:
            print(f"Error scraping Heisman odds: {e}")
            return []
    
    def scrape_all_data(self):
        """Scrape both championship and Heisman data"""
        championship_data = self.scrape_championship_odds()
        heisman_data = self.scrape_heisman_odds()
        
        return {
            'provider': 'betonline',
            'championship': championship_data,
            'heisman': heisman_data,
            'timestamp': time.time()
        }
    
    def close(self):
        """Close the driver"""
        if hasattr(self, 'driver'):
            self.driver.quit()

# Flask API
app = Flask(__name__)
scraper = BetOnlineScraper()

@app.route('/api/betonline/odds', methods=['GET'])
def get_all_odds():
    """Get all BetOnline odds"""
    try:
        data = scraper.scrape_all_data()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/betonline/championship', methods=['GET'])
def get_championship_odds():
    """Get championship odds only"""
    try:
        data = scraper.scrape_championship_odds()
        return jsonify({
            'success': True,
            'data': {
                'provider': 'betonline',
                'type': 'championship',
                'odds': data,
                'timestamp': time.time()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/betonline/heisman', methods=['GET'])
def get_heisman_odds():
    """Get Heisman odds only"""
    try:
        data = scraper.scrape_heisman_odds()
        return jsonify({
            'success': True,
            'data': {
                'provider': 'betonline',
                'type': 'heisman',
                'odds': data,
                'timestamp': time.time()
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/betonline/refresh', methods=['POST'])
def refresh_data():
    """Refresh scraped data"""
    try:
        data = scraper.scrape_all_data()
        return jsonify({
            'success': True,
            'message': 'Data refreshed successfully',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        scraper.close()