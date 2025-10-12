#!/usr/bin/env python3
"""
Test the fixed main scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from v2.flask_app import scrape_draftkings_odds

def test_fixed_main_scraper():
    """Test the fixed main scraper"""
    url = "https://sportsbook.draftkings.com/leagues/cycling/tour-de-france"
    
    print("Testing Fixed Main Scraper")
    print("=" * 50)
    print(f"URL: {url}")
    print()
    
    try:
        result = scrape_draftkings_odds(url, "championship")
        
        print("SUCCESS!")
        print(f"Found {len(result)} entries")
        print()
        
        # Show first 10 entries
        print("FIRST 10 ENTRIES:")
        for i, entry in enumerate(result[:10]):
            print(f"  {i+1}. {entry.get('team', 'N/A')} @ {entry.get('odds', 'N/A')} (original: {entry.get('original_odds', 'N/A')})")
        
        if len(result) > 10:
            print(f"  ... and {len(result) - 10} more entries")
        
        # Check for specific cyclists
        print("\nCHECKING FOR SPECIFIC CYCLISTS:")
        cyclists_to_check = ['Tadej Pogacar', 'Jonas Vingegaard', 'Remco Evenepoel', 'Primoz Roglic']
        
        for cyclist in cyclists_to_check:
            found = any(entry.get('team', '') == cyclist for entry in result)
            if found:
                entry = next((e for e in result if e.get('team', '') == cyclist), None)
                print(f"  FOUND {cyclist}: {entry.get('odds', 'N/A')} (original: {entry.get('original_odds', 'N/A')})")
            else:
                print(f"  MISSING {cyclist}: Not found")
        
        # Check for negative odds (favorites)
        print("\nCHECKING FOR NEGATIVE ODDS (FAVORITES):")
        negative_odds = [entry for entry in result if entry.get('odds', '').startswith('-')]
        print(f"Found {len(negative_odds)} entries with negative odds:")
        for entry in negative_odds[:5]:  # Show first 5
            print(f"  - {entry.get('team', 'N/A')}: {entry.get('odds', 'N/A')}")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_fixed_main_scraper()
