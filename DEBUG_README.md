# Debug Scraper Tools

This directory contains debug tools to help troubleshoot the scraper data flow and identify where data is being lost.

## Files

- `debug_scraper.py` - Simplified Flask app with comprehensive logging
- `test_debug_scraper.py` - Test script to use the debug scraper via API
- `run_debug_scraper.py` - Direct script to run the debug scraper
- `DEBUG_README.md` - This file

## Usage

### Method 1: Direct Script (Recommended)

```bash
python run_debug_scraper.py "https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026" championship
```

### Method 2: Flask API

1. Start the debug scraper:
```bash
python debug_scraper.py
```

2. In another terminal, run the test:
```bash
python test_debug_scraper.py
```

## What the Debug Scraper Shows

The debug scraper provides detailed logging for every step:

1. **🔍 Raw Data**: Shows exactly what elements are found on the page
2. **🔧 Cleaning**: Shows how team names are cleaned
3. **💰 Odds Processing**: Shows how odds are processed (including negative odds)
4. **🔄 Normalization**: Shows how names are normalized
5. **✅/❌ Decisions**: Shows which entries are added or skipped and why
6. **📊 Final Result**: Shows the final scraped data

## Key Debug Information

- **Raw scraped data** (first 10 teams and odds)
- **Step-by-step processing** of each entry
- **Filtering decisions** (why entries are skipped)
- **Odds processing** (including negative odds handling)
- **Name normalization** (including fallback logic)
- **Duplicate detection**
- **Final JSON payload** structure

## Troubleshooting

The debug scraper will help you identify:

1. **Are the correct elements being found?** (Raw data logging)
2. **Are negative odds being processed correctly?** (Odds processing logging)
3. **Are team names being normalized properly?** (Normalization logging)
4. **Are entries being filtered out incorrectly?** (Decision logging)
5. **What's the final JSON structure?** (Final result logging)

## Expected Output

You should see logs like:
```
🔍 Found 25 team elements and 25 odds elements
📊 RAW SCRAPED DATA (first 10 teams):
📊 Team 1: 'Tadej Pogacar'
📊 Team 2: 'Jonas Vingegaard'
...
💰 PROCESSING ODDS: Input: '-310'
💰 PROCESSING ODDS: Final result: '-310' -> '-232'
✅ ADDED: Tadej Pogacar @ -310 -> -232
```

This will help you see exactly where the data is being lost in the process.
