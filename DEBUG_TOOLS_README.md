# Debug Tools for Scraper Troubleshooting

This directory contains comprehensive debug tools to help troubleshoot the scraper and identify where data is being lost.

## The Problem

The scraper is getting a 404 error when trying to find elements with `span[data-testid="button-odds-market-board"]`. This suggests either:
1. The page structure has changed
2. The URL is not loading the expected content
3. The elements are loaded dynamically and need more time
4. The page is blocked or requires different handling

## Debug Tools Available

### 1. `simple_debug.py` - Quick Element Finder
**Purpose**: Quickly find any elements that might contain team names and odds
**Usage**: `python simple_debug.py <URL>`
**What it shows**:
- All elements with data-testid attributes
- Any text that looks like team names or odds
- Alternative selectors that might work
- Content verification (does the page contain expected text?)

### 2. `debug_page_inspector.py` - Comprehensive Page Analysis
**Purpose**: Deep analysis of the page structure (opens browser, takes screenshot)
**Usage**: `python debug_page_inspector.py <URL>`
**What it shows**:
- Screenshot of the page
- All available selectors and their results
- Unique data-testid values
- Tournament headers
- Potential team names and odds patterns
- Error indicators

### 3. `debug_scraper.py` - Full Scraper with Logging
**Purpose**: Complete scraper with detailed logging of every step
**Usage**: `python debug_scraper.py` (starts Flask server on port 5001)
**What it shows**:
- Raw scraped data
- Step-by-step processing
- Odds processing (including negative odds)
- Name normalization
- Filtering decisions
- Final JSON payload

### 4. `run_debug_tools.py` - Run All Tools
**Purpose**: Run multiple debug tools in sequence
**Usage**: `python run_debug_tools.py <URL>`
**What it does**:
- Runs simple debug first
- Asks if you want to run page inspector
- Provides summary of findings

## Quick Start

### Step 1: Run Simple Debug
```bash
python simple_debug.py "https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026"
```

This will quickly show you:
- What elements are available on the page
- Whether the page contains expected content
- Alternative selectors that might work

### Step 2: Run Page Inspector (if needed)
```bash
python debug_page_inspector.py "https://sportsbook.draftkings.com/leagues/cycling/1000001/tour-de-france-2026"
```

This will:
- Open a browser window (so you can see what's happening)
- Take a screenshot
- Show all available elements and selectors
- Help identify the correct selectors to use

### Step 3: Run Full Debug Scraper (if elements are found)
```bash
# Terminal 1
python debug_scraper.py

# Terminal 2
python test_debug_scraper.py
```

## What to Look For

### ✅ Good Signs
- Page contains "Tour de France", "cycling", "Tadej Pogacar", "Jonas Vingegaard"
- Elements with data-testid attributes are found
- Odds patterns like "+120", "-150" are found
- No error messages like "404", "blocked", "unavailable"

### ❌ Problem Signs
- Page shows "404", "blocked", "unavailable"
- No cycling/cycling content found
- No elements with data-testid attributes
- Page title doesn't match expected content

### 🔍 Alternative Selectors to Try
If the original selectors don't work, look for:
- `span[data-testid*="title"]` (partial match)
- `span[data-testid*="odds"]` (partial match)
- `div[data-testid*="card"]` (offer cards)
- `span[class*="title"]` (class-based)
- `span[class*="odds"]` (class-based)

## Common Issues and Solutions

### Issue 1: Page Not Loading
**Symptoms**: 404 errors, "no such element" errors
**Solutions**:
- Check if the URL is correct
- Try opening the URL in a browser manually
- Check if the page requires login or has geo-blocking

### Issue 2: Elements Not Found
**Symptoms**: 0 elements found with expected selectors
**Solutions**:
- Use `simple_debug.py` to find alternative selectors
- Check if elements are loaded dynamically (need more wait time)
- Look for different data-testid values

### Issue 3: Wrong Content
**Symptoms**: Page loads but contains different content
**Solutions**:
- Verify the URL is correct
- Check if the page structure has changed
- Look for alternative URLs or selectors

## Expected Output

### Simple Debug Output
```
🔍 Found 25 elements with data-testid
🔍 Unique data-testid values (15):
  - button-title-market-board
  - button-odds-market-board
  - offer-card
  ...
✅ Found: 'tour de france'
✅ Found: 'tadej pogacar'
✅ Found: 'jonas vingegaard'
```

### Page Inspector Output
```
📸 Screenshot saved as page_screenshot.png
🔍 Selector 'span[data-testid="button-title-market-board"]': 25 elements found
  1. 'Tadej Pogacar'
  2. 'Jonas Vingegaard'
  ...
```

## Next Steps

1. **Run the debug tools** to see what's available on the page
2. **Identify the correct selectors** that work for your specific page
3. **Update the main scraper** with the working selectors
4. **Test the updated scraper** to ensure it works correctly

## Files Created

- `simple_debug.py` - Quick element finder
- `debug_page_inspector.py` - Comprehensive page analysis
- `debug_scraper.py` - Full scraper with logging
- `run_debug_tools.py` - Run all tools
- `test_debug_scraper.py` - Test the debug scraper
- `DEBUG_TOOLS_README.md` - This file
