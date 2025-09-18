import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base URL for the API
base_url = "https://api.the-odds-api.com"
endpoint = "/v4/sports"

# API key
api_key = os.getenv("API_KEY")

if api_key is None:
    raise ValueError("API_KEY not found in .env file")

# Parameters for the request
apiKey = api_key

# Construct the full URL
url = f"{base_url}{endpoint}?apiKey={apiKey}"

# Print the URL
print("Constructed URL:", url)

# Making the GET request
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the JSON response
    data = response.json()
    
    # Save the data to a JSON file
    file_path = "events_data.json"
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)
        
    print("Sports data saved to:", file_path)
else:
    print("Error:", response.status_code)
    print(response.text)
