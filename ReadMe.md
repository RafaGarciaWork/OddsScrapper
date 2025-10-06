# DraftKings Scraper

A comprehensive sports odds scraper for DraftKings with GUI interface and FastAPI backend.

## Features

- **GUI Interface**: Easy-to-use Tkinter application for selecting sports and tournaments
- **Multiple Sports Support**: NFL, NBA, WNBA with various tournament types
- **Structured Data**: Organized odds data by championship, conference, and division
- **FastAPI Backend**: REST API for storing and retrieving scraped data
- **Real-time Scraping**: Live data extraction from DraftKings sportsbook

## How to Run

### Prerequisites

Make sure you have Python 3.8+ installed and the required dependencies:

```bash
pip install -r requirements.txt
```

### Running the Application

1. **Start the FastAPI Backend** (Terminal 1):
```bash
cd V1/draftkings
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. **Launch the GUI Scraper** (Terminal 2):
```bash
cd V1/draftkings
python ScrapperUI.py
```

### Usage

1. Select a sport from the dropdown (NFL, NBA, WNBA)
2. Choose a tournament type (Super Bowl, Conference Winner, etc.)
3. Click "Scrape & Send" to extract odds and send to the API
4. View results in the status area

### API Endpoints

- `POST /api/{provider}/{sport}/{tournament}` - Store odds data
- `GET /api/{provider}/{sport}/{tournament}` - Retrieve all odds data
- `GET /api/{provider}/{sport}/{tournament}/championship` - Get championship odds
- `GET /api/{provider}/{sport}/{tournament}/conferences` - Get conference odds
- `GET /api/{provider}/{sport}/{tournament}/divisions` - Get division odds



