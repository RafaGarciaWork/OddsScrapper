import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base URL for the API
base_url = "https://api.the-odds-api.com"

# Endpoint for event odds
endpoint = "/v4/sports/{sport}/events/{eventId}/odds"

# API key
api_key = os.getenv("API_KEY")

if api_key is None:
    raise ValueError("API_KEY not found in .env file")

# Parameters for the request
sport = "basketball_nba_championship_winner"  # Update with the specific sport key
eventId = "7c66e6cf069aa52be1dd7eaa47488403"  # Update with the specific event ID
apiKey = api_key
regions = "us"  # Or any other valid region, comma delimited if multiple
markets = "outrights"  # Update with the specific market(s) you want odds for
oddsFormat = "american"  # Specifies the format of odds in the response

# Construct the full URL
url = f"{base_url}{endpoint.format(sport=sport, eventId=eventId)}?apiKey={apiKey}&regions={regions}&markets={markets}&oddsFormat={oddsFormat}"

# Print the URL
print("Constructed URL:", url)

# Making the GET request
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Save the data to a JSON file
    file_path = "event_odds_data.json"
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)
        
    print("Event odds data saved to:", file_path)
else:
    print("Error:", response.status_code)
    print(response.text)
