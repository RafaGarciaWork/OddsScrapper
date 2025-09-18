import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

url = 'https://www.betonline.ag/sportsbook/futures-and-props/nfl-futures/super-bowl-futures'

chrome_options = Options()
# chrome_options.add_argument("--headless")  # Comment out for debugging
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(options=chrome_options)
driver.get(url)

# Wait longer for dynamic content
time.sleep(10)

soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# Debug: print a snippet of the HTML to check if the expected classes are present
snippet = soup.prettify()[:2000]
print("HTML snippet:\n", snippet)

team_elements = soup.find_all("p", class_="text-component small no-truncated left color-primary")
odds_elements = soup.find_all("p", class_="text-component small bold no-truncated center color-link")

print(f"Found {len(team_elements)} teams and {len(odds_elements)} odds.")

results = []
for team, odd in zip(team_elements, odds_elements):
    team_name = team.get_text(strip=True)
    odds_value = odd.get_text(strip=True)
    results.append({"team": team_name, "odds": odds_value})

with open("betonline_superbowl_odds.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print("Extracted odds saved to betonline_superbowl_odds.json")
