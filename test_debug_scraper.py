#!/usr/bin/env python3
"""
Test script for the debug scraper
"""

import requests
import json

def test_debug_scraper():
    """Test the debug scraper with a URL"""
    url = "https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026"  # Replace with your actual URL
    
    # Test data
    test_data = {
        "url": url,
        "event_type": "championship"
    }
    
    print("🧪 Testing Debug Scraper")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Event Type: {test_data['event_type']}")
    print()
    
    try:
        # Make request to debug scraper
        response = requests.post('http://localhost:5001/api/debug-scrape', json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Found {result['count']} entries")
            print()
            
            # Show the scraped data
            if isinstance(result['odds'], list):
                print("📊 SCRAPED DATA:")
                for i, entry in enumerate(result['odds'][:10]):  # Show first 10
                    print(f"  {i+1}. {entry.get('team', 'N/A')} @ {entry.get('odds', 'N/A')} (original: {entry.get('original_odds', 'N/A')})")
                if len(result['odds']) > 10:
                    print(f"  ... and {len(result['odds']) - 10} more entries")
            else:
                print("📊 SCRAPED DATA (structured):")
                print(json.dumps(result['odds'], indent=2))
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to debug scraper")
        print("Make sure the debug scraper is running on port 5001")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_debug_scraper()
