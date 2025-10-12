#!/usr/bin/env python3
"""
Simple test to verify the scraper results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from v2.flask_app import scrape_draftkings_odds

def test_simple_results():
    """Test the scraper and show results without Unicode issues"""
    url = "https://sportsbook.draftkings.com/leagues/cycling/tour-de-france"
    
    print("Testing Scraper Results")
    print("=" * 50)
    
    try:
        result = scrape_draftkings_odds(url, "championship")
        
        print(f"SUCCESS! Found {len(result)} entries")
        print()
        
        # Check for Tadej Pogacar specifically
        tadej_entries = [entry for entry in result if 'pogacar' in entry.get('team', '').lower()]
        if tadej_entries:
            for entry in tadej_entries:
                team = entry.get('team', 'N/A')
                odds = entry.get('odds', 'N/A')
                original = entry.get('original_odds', 'N/A')
                print(f"TADEJ POGACAR: {team} @ {odds} (original: {original})")
        else:
            print("TADEJ POGACAR: Not found")
        
        # Check for Jonas Vingegaard
        jonas_entries = [entry for entry in result if 'vingegaard' in entry.get('team', '').lower()]
        if jonas_entries:
            for entry in jonas_entries:
                team = entry.get('team', 'N/A')
                odds = entry.get('odds', 'N/A')
                original = entry.get('original_odds', 'N/A')
                print(f"JONAS VINGEGAARD: {team} @ {odds} (original: {original})")
        else:
            print("JONAS VINGEGAARD: Not found")
        
        # Check for negative odds (should only be Tadej Pogacar)
        negative_odds = [entry for entry in result if entry.get('odds', '').startswith('-')]
        print(f"\nNEGATIVE ODDS COUNT: {len(negative_odds)}")
        for entry in negative_odds:
            team = entry.get('team', 'N/A')
            odds = entry.get('odds', 'N/A')
            print(f"  - {team}: {odds}")
        
        # Check for positive odds
        positive_odds = [entry for entry in result if entry.get('odds', '').startswith('+')]
        print(f"\nPOSITIVE ODDS COUNT: {len(positive_odds)}")
        print("First 5 positive odds:")
        for entry in positive_odds[:5]:
            team = entry.get('team', 'N/A')
            odds = entry.get('odds', 'N/A')
            print(f"  - {team}: {odds}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_simple_results()
