from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional, Union

app = FastAPI()

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

# In-memory storage for odds by sport and tournament
stored_odds: Dict[str, Dict[str, OddsData]] = {}

# Initialize storage
for sport in ["nfl", "nba", "wnba"]:
    stored_odds[sport] = {}

@app.post("/api/{sport}/{tournament}")
async def receive_odds(sport: str, tournament: str, odds_data: OddsData):
    if sport not in stored_odds:
        stored_odds[sport] = {}
    stored_odds[sport][tournament] = odds_data
    
    # Count total teams for logging
    total_teams = 0
    if odds_data.event_type == "championship":
        total_teams = len(odds_data.teams)
    elif odds_data.event_type == "conference":
        total_teams = sum(len(conf.teams) for conf in odds_data.conferences)
    elif odds_data.event_type == "division":
        total_teams = sum(len(div.teams) for div in odds_data.divisions)
    
    print(f"Received {total_teams} teams for {tournament.replace('-', ' ').title()} {sport.upper()} ({odds_data.event_type})")
    return {"status": "success", "event_type": odds_data.event_type, "total_teams": total_teams}

@app.get("/api/{sport}/{tournament}")
async def get_odds(sport: str, tournament: str):
    if sport in stored_odds and tournament in stored_odds[sport]:
        return {"odds": stored_odds[sport][tournament]}
    return {"error": "No odds data available for this sport and tournament"}, 404

# New endpoints for specific data access
@app.get("/api/{sport}/{tournament}/championship")
async def get_championship_odds(sport: str, tournament: str):
    """Get championship odds as a flat list of teams"""
    if sport in stored_odds and tournament in stored_odds[sport]:
        data = stored_odds[sport][tournament]
        if data.event_type == "championship":
            return {"teams": data.teams}
        else:
            return {"error": "This tournament is not a championship event"}, 400
    return {"error": "No odds data available"}, 404

@app.get("/api/{sport}/{tournament}/conferences")
async def get_conference_odds(sport: str, tournament: str):
    """Get conference odds grouped by conference"""
    if sport in stored_odds and tournament in stored_odds[sport]:
        data = stored_odds[sport][tournament]
        if data.event_type == "conference":
            return {"conferences": data.conferences}
        else:
            return {"error": "This tournament is not a conference event"}, 400
    return {"error": "No odds data available"}, 404

@app.get("/api/{sport}/{tournament}/divisions")
async def get_division_odds(sport: str, tournament: str):
    """Get division odds grouped by division"""
    if sport in stored_odds and tournament in stored_odds[sport]:
        data = stored_odds[sport][tournament]
        if data.event_type == "division":
            return {"divisions": data.divisions}
        else:
            return {"error": "This tournament is not a division event"}, 400
    return {"error": "No odds data available"}, 404