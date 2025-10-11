# DraftKings Odds Scraper

A comprehensive sports odds scraping system that extracts betting data from DraftKings and submits it to the CLM API backend. Designed for scalability across multiple sports and events.

## Features

- **Multi-Sport Support**: NFL, NBA, and other sports with configurable league IDs
- **Multiple Event Types**: Championships, conferences, divisions, and more
- **API Integration**: Seamless integration with CLM API for game creation and odds submission
- **Comprehensive Testing**: Full test suite with odds calculation validation
- **Scalable Architecture**: Easy to add new sports and tournaments

## Project Structure

```
V1/draftkings/
├── __init__.py           # Package initialization
├── main.py              # FastAPI server for API endpoints
├── scrapper.py          # Core scraping logic and CLI functionality
├── successful_test.py    # Comprehensive test suite
└── README.md            # This file
```

## Core Components

### `main.py` - FastAPI Server
- **Purpose**: Provides REST API endpoints for triggering scrapes
- **Endpoints**:
  - `POST /api/scrape` - Trigger scraping and submission to CLM API
  - `GET /api/status` - Get server status and configuration
  - `GET /api/games` - List recent games created
  - `GET /api/config` - Get current configuration

### `scrapper.py` - Core Scraping Logic
- **Purpose**: Main scraping functionality and CLI interface
- **Features**:
  - Web scraping with Selenium and BeautifulSoup
  - Multiple event type support (championship, conference, division)
  - API integration for game creation and odds submission
  - Comprehensive error handling and logging

### `successful_test.py` - Test Suite
- **Purpose**: Comprehensive testing and validation
- **Features**:
  - Odds calculation testing (25% reduction + rounding)
  - 7-digit ID generation system
  - API payload validation
  - End-to-end testing with real DraftKings data

## Configuration

The scraper supports multiple sports and tournaments through the `CONFIG` dictionary in `scrapper.py`:

```python
CONFIG = {
    "NFL": {
        "Super Bowl": {
            "url": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl",
            "event_type": "championship",
            "id_league": 3101,
            "id_game_type": 1,
            "description": "NFL Super Bowl Championship"
        }
    }
}
```

## API Endpoints

### Game Creation
- **URL**: `https://clmapi.sportsfanwagers.com/api/Game/InsertGame`
- **Method**: POST
- **Purpose**: Creates a new game in the system

### Odds Submission
- **URL**: `https://clmapi.sportsfanwagers.com/api/Game/InsertGameValuesTNT?idGame={gameId}`
- **Method**: POST
- **Purpose**: Submits odds data for a specific game

## Usage

### Running the API Server
```bash
python V1/draftkings/main.py
```

### Running the CLI Scraper
```bash
python V1/draftkings/scrapper.py
```

### Running Tests
```bash
python V1/draftkings/successful_test.py
```

## Odds Processing

The system applies specific processing rules to odds:
1. **25% Reduction**: All odds are reduced by 25%
2. **Rounding**: Odds are rounded down to the nearest 0 or 5
3. **Capping**: Maximum odds value is capped at 20000

## Adding New Sports/Events

To add new sports or tournaments:

1. **Add to CONFIG**: Update the `CONFIG` dictionary in `scrapper.py`
2. **Configure URLs**: Add the appropriate DraftKings URL
3. **Set Event Type**: Choose from 'championship', 'conference', 'division'
4. **Set League/Game IDs**: Configure the appropriate IDs for the CLM API
5. **Test**: Run the test suite to validate the new configuration

## Dependencies

- `selenium` - Web scraping
- `beautifulsoup4` - HTML parsing
- `requests` - API communication
- `fastapi` - API server
- `pydantic` - Data validation
- `webdriver-manager` - Chrome driver management

## Logging

The system provides comprehensive logging:
- Application logs with timestamps
- Scraped data saved to JSON files
- Database logging for tracking game creation
- Error handling with detailed exception information

## Future Enhancements

This organized structure makes it easy to:
- Add new sports and tournaments
- Implement additional event types
- Scale to multiple betting providers
- Add new API endpoints
- Implement advanced odds processing rules
