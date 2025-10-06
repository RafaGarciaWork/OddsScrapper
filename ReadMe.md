# DraftKings Scraper

Lightweight DraftKings odds scraper (CLI) with a FastAPI backend and SQLite persistence.

## Features

- **CLI Scraper**: Iterates configured sports/tournaments and POSTs results to API
- **Multiple Sports**: NFL (examples in config); easy to extend
- **Persistence**: Stores payloads in `odds.db` (SQLite)
- **JSON Dumps**: Saves each scrape to `scrapes/` for review

## Install

```bash
pip install -r requirements.txt
```

Create a `.env` in project root (optional):
```
API_BASE_URL=http://localhost:8000
```

## Run

1) Start API (run from project root):
```bash
uvicorn V1.draftkings.main:app --reload
```

2) Run scraper (from project root):
```bash
python -m V1.draftkings.scrapper
```

Scraped files: `scrapes/draftkings_{sport}_{tournament}_{UTC}.json`

## API Endpoints (summary)

- `POST /api/{provider}/{sport}/{tournament}`: Store odds
- `GET /api/{provider}/{sport}/{tournament}`: Full stored JSON
- `GET /api/{provider}/{sport}/{tournament}/championship`: `{ teams: [...] }`
- `GET /api/{provider}/{sport}/{tournament}/conferences`: `{ conferences: [...] }`
- `GET /api/{provider}/{sport}/{tournament}/divisions`: `{ divisions: [...] }`

DB file: `odds.db`. Inspect with `sqlite3 odds.db` → `.schema odds`, `SELECT * FROM odds LIMIT 5;`