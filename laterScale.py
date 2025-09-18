"""@app.get("/api/{sport}/odds")
async def get_odds(sport: str):
    # Logic to scrape odds for the given sport
    urls = {
        "nfl": "https://sportsbook.draftkings.com/leagues/football/nfl?category=futures&subcategory=super-bowl",
        "nba": "https://sportsbook.draftkings.com/leagues/basketball/nba?category=futures",
        # Add more sports and URLs
    }
    if sport not in urls:
        return {"error": "Sport not supported"}
    url = urls[sport]
    # Reuse your scraping logic here
    # ...
    return results"""# --- IGNORE ---Se usara despues cuando empezemos a probar con multiples deportes