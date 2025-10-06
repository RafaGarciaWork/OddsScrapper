import json
import logging
import sqlite3
from contextlib import closing
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Union

app = FastAPI()

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

class ConferenceGroup(BaseModel):
    conference: str
    teams: List[TeamOdds]

class DivisionGroup(BaseModel):
    division: str
    conference: str
    teams: List[TeamOdds]

class ChampionshipData(BaseModel):
    event_type: str = "championship"
    teams: List[TeamOdds]

class ConferenceData(BaseModel):
    event_type: str = "conference"
    conferences: List[ConferenceGroup]

class DivisionData(BaseModel):
    event_type: str = "division"
    divisions: List[DivisionGroup]

# Union type for all possible data structures
OddsData = Union[ChampionshipData, ConferenceData, DivisionData]

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