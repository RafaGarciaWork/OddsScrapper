from fastapi import FastAPI
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

app = FastAPI()

@app.get("/api/superbowl-odds")
async def get_superbowl_odds():
    url = 'https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl'

    # Set up headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    # Wait for JavaScript to load content
    time.sleep(5)  # Adjust as needed

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    team_elements = soup.find_all("span", {"data-testid": "button-title-market-board"})
    odds_elements = soup.find_all("span", {"data-testid": "button-odds-market-board"})

    results = []
    for team, odd in zip(team_elements, odds_elements):
        team_name = team.get_text(strip=True)
        odds_value = odd.get_text(strip=True)
        results.append({"team": team_name, "odds": odds_value})

    return results