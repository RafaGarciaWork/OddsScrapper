from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

class OddsItem(BaseModel):
    team: str
    odds: str
    conference: str = None  # Optional for clustering
    division: str = None    # Optional for clustering

# In-memory storage for odds by sport and tournament
stored_odds: Dict[str, Dict[str, List[OddsItem]]] = {}

# Initialize storage
for sport in ["nfl", "nba", "wnba"]:
    stored_odds[sport] = {}

@app.post("/api/{sport}/{tournament}")
async def receive_odds(sport: str, tournament: str, odds: List[OddsItem]):
    if sport not in stored_odds:
        stored_odds[sport] = {}
    stored_odds[sport][tournament] = odds
    print(f"Received {len(odds)} {tournament.replace('-', ' ').title()} odds for {sport.upper()}: {odds}")
    return {"status": "success", "received": len(odds)}

@app.get("/api/{sport}/{tournament}")
async def get_odds(sport: str, tournament: str):
    if sport in stored_odds and tournament in stored_odds[sport]:
        return {"odds": stored_odds[sport][tournament]}
    return {"error": "No odds data available for this sport and tournament"}, 404