#!/usr/bin/env python3
"""
Run the debug scraper with a specific URL
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from debug_scraper import scrape_draftkings_odds_debug

def main():
    """Run debug scraper directly"""
    if len(sys.argv) < 2:
        print("Usage: python run_debug_scraper.py <URL> [event_type]")
        print("Example: python run_debug_scraper.py 'https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026' championship")
        sys.exit(1)
    
    url = sys.argv[1]
    event_type = sys.argv[2] if len(sys.argv) > 2 else "championship"
    
    print(f"🚀 Running debug scraper for: {url}")
    print(f"Event type: {event_type}")
    print("=" * 80)
    
    try:
        result = scrape_draftkings_odds_debug(url, event_type)
        
        print("\n" + "=" * 80)
        print("🎯 FINAL RESULT:")
        print("=" * 80)
        
        if isinstance(result, list):
            print(f"Found {len(result)} entries:")
            for i, entry in enumerate(result):
                print(f"  {i+1}. {entry.get('team', 'N/A')} @ {entry.get('odds', 'N/A')} (original: {entry.get('original_odds', 'N/A')})")
        else:
            print("Structured data:")
            import json
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
