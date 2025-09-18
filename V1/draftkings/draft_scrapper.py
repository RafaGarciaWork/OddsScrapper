import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

url = 'https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl'

# Set up headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

# Wait for JavaScript to load content
time.sleep(5)  # Increase if needed

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})

results = []
for team, odd in zip(team_elements, odds_elements):
    team_name = team.get_text(strip=True)
    odds_value = odd.get_text(strip=True)
    results.append({"team": team_name, "odds": odds_value})

with open("draftkings_superbowl_odds.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("Extracted odds saved to draftkings_superbowl_odds.json")
