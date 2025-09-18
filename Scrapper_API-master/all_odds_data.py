import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base URL for the API
base_url = "https://api.the-odds-api.com"
endpoint = "/v4/sports/"

# API key
api_key = os.getenv("API_KEY")

if api_key is None:
    raise ValueError("API_KEY not found in .env file")

# Parameters for the request
apiKey = api_key
regions = "us"  # Or any other valid region, comma delimited if multiple
markets = "outrights,spreads"  # Update with the specific market(s) you want odds for
oddsFormat = "american"  # Specifies the format of odds in the response
sports = ['basketball_nba_championship_winner', 'americanfootball_nfl_super_bowl_winner', 
          'icehockey_nhl_championship_winner', 'soccer_uefa_european_championship',
          'americanfootball_ncaaf_championship_winner','baseball_mlb_world_series_winner',
          'basketball_ncaab_championship_winner','soccer_uefa_europa_conference_league']

# List to store all odds data
all_odds_data = []

# Loop through each sport
for sport in sports:
    # Construct the full URL for the sport
    url = f"{base_url}{endpoint}{sport}/odds/?apiKey={apiKey}&regions={regions}&markets={markets}&oddsFormat={oddsFormat}"
    
    # Making the GET request
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        
        # Append the odds data for this sport to the list
        all_odds_data.append(data)
        
        print(f"Odds data for {sport} retrieved and added to the list.")
    else:
        print("Error:", response.status_code)
        print(response.text)

# Save all odds data to a combined JSON file
all_odds_file_path = "all_odds_data.json"
with open(all_odds_file_path, "w") as json_file:
    json.dump(all_odds_data, json_file, indent=4)
    
print("All odds data saved to:", all_odds_file_path)
