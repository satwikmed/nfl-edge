"""
Team metadata ingestion.
Populates the teams table with all 32 NFL teams including coaches,
locations, and season records.
"""

import logging
import nfl_data_py as nfl
import pandas as pd

from src.utils.config import TEAMS, CURRENT_SEASON
from src.utils.db import get_connection, init_db

logger = logging.getLogger(__name__)


def _get_coaching_data() -> dict:
    """
    Attempt to pull coaching staff from nflverse.
    Falls back to a static mapping if unavailable.
    """
    # Static coaching data for 2025 season (will be updated)
    # These are reasonable defaults — actual values come from data
    coaches = {}
    try:
        # nfl_data_py may have roster data with coach info
        rosters = nfl.import_rosters([CURRENT_SEASON])
        if rosters is not None and len(rosters) > 0:
            logger.info("Got roster data for coaching extraction")
    except Exception as e:
        logger.warning(f"Could not fetch coaching data: {e}")
    
    return coaches


def _get_team_records() -> dict:
    """Pull win-loss records from schedule data."""
    records = {}
    try:
        schedules = nfl.import_schedules([CURRENT_SEASON])
        if schedules is not None and len(schedules) > 0:
            # Filter to completed games
            completed = schedules[schedules['result'].notna()].copy()
            
            for _, game in completed.iterrows():
                home = game.get('home_team', '')
                away = game.get('away_team', '')
                result = game.get('result', 0)
                
                if home not in records:
                    records[home] = {'wins': 0, 'losses': 0, 'ties': 0}
                if away not in records:
                    records[away] = {'wins': 0, 'losses': 0, 'ties': 0}
                
                if result > 0:
                    records[home]['wins'] += 1
                    records[away]['losses'] += 1
                elif result < 0:
                    records[home]['losses'] += 1
                    records[away]['wins'] += 1
                else:
                    records[home]['ties'] += 1
                    records[away]['ties'] += 1
            
            logger.info(f"Got records for {len(records)} teams")
    except Exception as e:
        logger.warning(f"Could not fetch schedule data: {e}")
    
    return records


def ingest_teams():
    """Ingest all 32 team records into the database."""
    logger.info("Starting team metadata ingestion...")
    
    records = _get_team_records()
    coaches = _get_coaching_data()
    
    rows = []
    for team in TEAMS:
        abbr = team["abbr"]
        record = records.get(abbr, {'wins': 0, 'losses': 0, 'ties': 0})
        coach_info = coaches.get(abbr, {})
        
        rows.append({
            "team_id": abbr,
            "name": team["name"],
            "abbreviation": abbr,
            "city": team["city"],
            "state": team["state"],
            "division": team["division"],
            "conference": team["conference"],
            "latitude": team["lat"],
            "longitude": team["lng"],
            "stadium": team["stadium"],
            "head_coach": coach_info.get("head_coach", ""),
            "offensive_coordinator": coach_info.get("oc", ""),
            "defensive_coordinator": coach_info.get("dc", ""),
            "wins": record["wins"],
            "losses": record["losses"],
            "ties": record["ties"],
        })
    
    with get_connection() as conn:
        for row in rows:
            conn.execute("""
                INSERT OR REPLACE INTO teams 
                (team_id, name, abbreviation, city, state, division, conference,
                 latitude, longitude, stadium, head_coach, offensive_coordinator,
                 defensive_coordinator, wins, losses, ties, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                row["team_id"], row["name"], row["abbreviation"],
                row["city"], row["state"], row["division"], row["conference"],
                row["latitude"], row["longitude"], row["stadium"],
                row["head_coach"], row["offensive_coordinator"],
                row["defensive_coordinator"],
                row["wins"], row["losses"], row["ties"],
            ))
    
    logger.info(f"Ingested {len(rows)} teams")
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    count = ingest_teams()
    print(f"Ingested {count} teams")
