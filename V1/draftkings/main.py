<<<<<<< HEAD
"""DraftKings Sports Odds API Server

This module provides a FastAPI server for managing DraftKings sports odds data.
It integrates with the CLM API for game creation and odds submission.
Designed for Windows Server 2012 compatibility.

Endpoints:
    POST /api/scrape: Trigger scraping and submission to CLM API
    GET /api/status: Get server status and configuration
    GET /api/games: List recent games created
"""

=======
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
import json
import logging
import sqlite3
from contextlib import closing
<<<<<<< HEAD
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
=======
from fastapi import FastAPI
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
from pydantic import BaseModel

# Import the scraper functions
from .scrapper import run_scraper, CONFIG, GameData, GameValuesTNT

<<<<<<< HEAD
app = FastAPI(title="DraftKings Odds Scraper API", version="2.0.0")
=======
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("odds_api")

# Initialize SQLite connection and schema
conn = sqlite3.connect("odds.db", check_same_thread=False)
with closing(conn.cursor()) as cur:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS odds (
            provider TEXT,
            sport TEXT,
            tournament TEXT,
            data TEXT,
            PRIMARY KEY(provider, sport, tournament)
        )
        """
    )
    conn.commit()

class TeamOdds(BaseModel):
    team: str
    odds: str
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("odds_api")

# Initialize SQLite connection for logging
conn = sqlite3.connect("odds_scraper.db", check_same_thread=False)
with closing(conn.cursor()) as cur:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS scraping_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            sport TEXT,
            tournament TEXT,
            game_id INTEGER,
            status TEXT,
            message TEXT
        )
        """
    )
    conn.commit()

class ScrapeRequest(BaseModel):
    sport: Optional[str] = None
    tournament: Optional[str] = None

class ScrapeResponse(BaseModel):
    status: str
    message: str
    games_created: int
    total_teams: int

class GameLog(BaseModel):
    id: int
    timestamp: str
    sport: str
    tournament: str
    game_id: Optional[int]
    status: str
    message: str

def log_scraping_activity(sport: str, tournament: str, game_id: Optional[int], status: str, message: str):
    """Log scraping activity to the database."""
    timestamp = datetime.utcnow().isoformat()
    with closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT INTO scraping_logs (timestamp, sport, tournament, game_id, status, message) VALUES (?, ?, ?, ?, ?, ?)",
            (timestamp, sport, tournament, game_id, status, message)
        )
        conn.commit()

<<<<<<< HEAD
@app.post("/api/scrape", response_model=ScrapeResponse)
async def trigger_scrape(request: ScrapeRequest = ScrapeRequest()):
    """Trigger scraping of DraftKings odds and submission to CLM API."""
    try:
        logger.info("Starting scrape process")
        
        # If specific sport/tournament requested, filter CONFIG
        config_to_process = CONFIG
        if request.sport:
            config_to_process = {k: v for k, v in CONFIG.items() if k.lower() == request.sport.lower()}
            if not config_to_process:
                raise HTTPException(status_code=404, detail=f"Sport '{request.sport}' not found")
        
        games_created = 0
        total_teams = 0
        
        for sport, tournaments in config_to_process.items():
            for tournament, conf in tournaments.items():
                # Skip if specific tournament requested and doesn't match
                if request.tournament and tournament.lower() != request.tournament.lower():
                    continue
                
                try:
                    logger.info("Processing %s - %s", sport, tournament)
                    
                    # Import and run the scraper logic
                    from .scrapper import scrape_odds, create_game, submit_game_odds, GameData
                    
                    # Scrape the odds data
                    results = scrape_odds(conf["url"], conf["event_type"])
                    
                    # Extract teams data based on event type
                    teams_data = []
                    if conf["event_type"] == "championship":
                        teams_data = results.get("teams", [])
                    elif conf["event_type"] == "conference":
                        for conf_data in results.get("conferences", []):
                            teams_data.extend(conf_data.get("teams", []))
                    elif conf["event_type"] == "division":
                        for div_data in results.get("divisions", []):
                            teams_data.extend(div_data.get("teams", []))
                    
                    num_teams = len(teams_data)
                    total_teams += num_teams
                    
                    if num_teams == 0:
                        log_scraping_activity(sport, tournament, None, "warning", "No teams found")
                        continue
                    
                    # Create game data
                    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
                    game_data = GameData(
                        IdLeague=conf["id_league"],
                        IdGameType=conf["id_game_type"],
                        GameDateTime=current_time,
                        VisitorTeam=teams_data[0]["team"] if teams_data else "Unknown",
                        HomeTeam=teams_data[1]["team"] if len(teams_data) > 1 else "Unknown",
                        EventDate=current_time,
                        NumTeams=num_teams,
                        Description=conf["description"]
                    )
                    
                    # Create the game
                    game_id = create_game(game_data)
                    if game_id:
                        games_created += 1
                        log_scraping_activity(sport, tournament, game_id, "success", f"Game created with {num_teams} teams")
                        
                        # Submit the odds
                        success = submit_game_odds(game_id, teams_data)
                        if success:
                            log_scraping_activity(sport, tournament, game_id, "success", "Odds submitted successfully")
                        else:
                            log_scraping_activity(sport, tournament, game_id, "error", "Failed to submit odds")
                    else:
                        log_scraping_activity(sport, tournament, None, "error", "Failed to create game")
                        
                except Exception as exc:
                    logger.exception("Error processing %s - %s: %s", sport, tournament, exc)
                    log_scraping_activity(sport, tournament, None, "error", str(exc))
        
        return ScrapeResponse(
            status="success",
            message=f"Scraping completed. Created {games_created} games with {total_teams} total teams.",
            games_created=games_created,
            total_teams=total_teams
        )
        
    except Exception as exc:
        logger.exception("Scraping failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(exc)}")

@app.get("/api/status")
async def get_status():
    """Get server status and configuration."""
    return {
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "config": {
            "sports": list(CONFIG.keys()),
            "total_tournaments": sum(len(tournaments) for tournaments in CONFIG.values())
        }
    }

@app.get("/api/games", response_model=List[GameLog])
async def get_recent_games(limit: int = 50):
    """Get recent games created."""
    with closing(conn.cursor()) as cur:
        rows = cur.execute(
            "SELECT id, timestamp, sport, tournament, game_id, status, message FROM scraping_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        
        return [
            GameLog(
                id=row[0],
                timestamp=row[1],
                sport=row[2],
                tournament=row[3],
                game_id=row[4],
                status=row[5],
                message=row[6]
            )
            for row in rows
        ]

@app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return CONFIG

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DraftKings Odds Scraper API v2.0.0",
        "endpoints": {
            "POST /api/scrape": "Trigger scraping and submission to CLM API",
            "GET /api/status": "Get server status",
            "GET /api/games": "Get recent games created",
            "GET /api/config": "Get current configuration"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
=======
# In-memory cache optional (not relied on for persistence)
stored_odds: Dict[str, Dict[str, Dict[str, OddsData]]] = {}

@app.post("/api/{provider}/{sport}/{tournament}")
async def receive_odds(provider: str, sport: str, tournament: str, odds_data: OddsData):
    provider = provider.lower()
    sport = sport.lower()
    if provider not in stored_odds:
        stored_odds[provider] = {}
    if sport not in stored_odds[provider]:
        stored_odds[provider][sport] = {}
    stored_odds[provider][sport][tournament] = odds_data

    # Persist to SQLite as canonical storage
    with closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT OR REPLACE INTO odds(provider, sport, tournament, data) VALUES (?, ?, ?, ?)",
            (provider, sport, tournament, json.dumps(odds_data.model_dump())),
        )
        conn.commit()
    
    # Count total teams for logging
    total_teams = 0
    if odds_data.event_type == "championship":
        total_teams = len(odds_data.teams)
    elif odds_data.event_type == "conference":
        total_teams = sum(len(conf.teams) for conf in odds_data.conferences)
    elif odds_data.event_type == "division":
        total_teams = sum(len(div.teams) for div in odds_data.divisions)
    
    logger.info(
        "Received %s teams for %s %s %s (%s)",
        total_teams,
        provider.upper(),
        sport.upper(),
        tournament.replace('-', ' ').title(),
        odds_data.event_type,
    )
    return {"status": "success", "event_type": odds_data.event_type, "total_teams": total_teams}

@app.get("/api/{provider}/{sport}/{tournament}")
async def get_odds(provider: str, sport: str, tournament: str):
    provider = provider.lower()
    sport = sport.lower()
    # Try cache first
    if provider in stored_odds and sport in stored_odds[provider] and tournament in stored_odds[provider][sport]:
        return {"odds": stored_odds[provider][sport][tournament]}
    # Fallback to SQLite persistence
    with closing(conn.cursor()) as cur:
        row = cur.execute(
            "SELECT data FROM odds WHERE provider=? AND sport=? AND tournament=?",
            (provider, sport, tournament),
        ).fetchone()
        if row:
            try:
                # Return the exact JSON blob we stored so clients see the same payload
                return json.loads(row[0])
            except Exception:
                logger.exception("Failed to decode JSON for %s/%s/%s", provider, sport, tournament)
    return {"error": "No odds data available for this sport and tournament"}, 404

# New endpoints for specific data access
@app.get("/api/{provider}/{sport}/{tournament}/championship")
async def get_championship_odds(provider: str, sport: str, tournament: str):
    """Get championship odds as a flat list of teams"""
    provider = provider.lower()
    sport = sport.lower()
    if provider in stored_odds and sport in stored_odds[provider] and tournament in stored_odds[provider][sport]:
        data = stored_odds[provider][sport][tournament]
        if data.event_type == "championship":
            return {"teams": data.teams}
        else:
            return {"error": "This tournament is not a championship event"}, 400
    # Fallback to DB
    with closing(conn.cursor()) as cur:
        row = cur.execute(
            "SELECT data FROM odds WHERE provider=? AND sport=? AND tournament=?",
            (provider, sport, tournament),
        ).fetchone()
        if row:
            try:
                payload = json.loads(row[0])
                if payload.get("event_type") == "championship":
                    return {"teams": payload.get("teams", [])}
            except Exception:
                logger.exception("Failed to decode JSON for %s/%s/%s", provider, sport, tournament)
    return {"error": "No odds data available"}, 404

@app.get("/api/{provider}/{sport}/{tournament}/conferences")
async def get_conference_odds(provider: str, sport: str, tournament: str):
    """Get conference odds grouped by conference"""
    provider = provider.lower()
    sport = sport.lower()
    if provider in stored_odds and sport in stored_odds[provider] and tournament in stored_odds[provider][sport]:
        data = stored_odds[provider][sport][tournament]
        if data.event_type == "conference":
            return {"conferences": data.conferences}
        else:
            return {"error": "This tournament is not a conference event"}, 400
    # Fallback to DB
    with closing(conn.cursor()) as cur:
        row = cur.execute(
            "SELECT data FROM odds WHERE provider=? AND sport=? AND tournament=?",
            (provider, sport, tournament),
        ).fetchone()
        if row:
            try:
                payload = json.loads(row[0])
                if payload.get("event_type") == "conference":
                    return {"conferences": payload.get("conferences", [])}
            except Exception:
                logger.exception("Failed to decode JSON for %s/%s/%s", provider, sport, tournament)
    return {"error": "No odds data available"}, 404

@app.get("/api/{provider}/{sport}/{tournament}/divisions")
async def get_division_odds(provider: str, sport: str, tournament: str):
    """Get division odds grouped by division"""
    provider = provider.lower()
    sport = sport.lower()
    if provider in stored_odds and sport in stored_odds[provider] and tournament in stored_odds[provider][sport]:
        data = stored_odds[provider][sport][tournament]
        if data.event_type == "division":
            return {"divisions": data.divisions}
        else:
            return {"error": "This tournament is not a division event"}, 400
    # Fallback to DB
    with closing(conn.cursor()) as cur:
        row = cur.execute(
            "SELECT data FROM odds WHERE provider=? AND sport=? AND tournament=?",
            (provider, sport, tournament),
        ).fetchone()
        if row:
            try:
                payload = json.loads(row[0])
                if payload.get("event_type") == "division":
                    return {"divisions": payload.get("divisions", [])}
            except Exception:
                logger.exception("Failed to decode JSON for %s/%s/%s", provider, sport, tournament)


def _count_total_teams(odds_data: OddsData) -> int:
    """Count total teams in odds data based on event type.
    
    Args:
        odds_data: The odds data to count teams from
        
    Returns:
        Total number of teams
    """
    if odds_data.event_type == "championship":
        return len(odds_data.teams)
    elif odds_data.event_type == "conference":
        return sum(len(conf.teams) for conf in odds_data.conferences)
    elif odds_data.event_type == "division":
        return sum(len(div.teams) for div in odds_data.divisions)
    return 0


def _has_odds_data(provider: str, sport: str, tournament: str) -> bool:
    """Check if odds data exists for the given parameters.
    
    Args:
        provider: The odds provider
        sport: The sport
        tournament: The tournament type
        
    Returns:
        True if data exists, False otherwise
    """
    return (
        provider in stored_odds
        and sport in stored_odds[provider]
        and tournament in stored_odds[provider][sport]
    )
>>>>>>> 0967c96d35ccf3ba31b1ed299fb51952f4f64c4c
