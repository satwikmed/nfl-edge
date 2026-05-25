"""
Injury report ingestion from nflverse.
Tracks player injuries, game availability, and games missed.
"""

import logging
import nfl_data_py as nfl
import pandas as pd
import numpy as np

from src.utils.config import CURRENT_SEASON
from src.utils.db import get_connection, init_db

logger = logging.getLogger(__name__)


def ingest_injuries(season: int = None):
    """Ingest injury report data."""
    season = season or CURRENT_SEASON
    logger.info(f"Ingesting injury data for {season}...")
    
    try:
        injuries = nfl.import_injuries([season])
    except Exception as e:
        logger.warning(f"Could not fetch injury data: {e}")
        return 0
    
    if injuries is None or len(injuries) == 0:
        logger.warning(f"No injury data available for {season}")
        return 0
    
    logger.info(f"Fetched {len(injuries)} injury records")
    
    rows = []
    for _, injury in injuries.iterrows():
        pid = injury.get('gsis_id', injury.get('player_id', ''))
        if not pid or pd.isna(pid):
            continue
        
        def safe_str(val, default=''):
            return str(val) if pd.notna(val) else default
        
        def safe_int(val, default=0):
            return int(val) if pd.notna(val) else default
        
        team = safe_str(injury.get('team', injury.get('club_code', '')))
        if team == 'LA':
            team = 'LAR'
        
        report_status = safe_str(injury.get('report_status', injury.get('game_status', '')))
        
        rows.append({
            'player_id': str(pid),
            'season': int(season),
            'week': safe_int(injury.get('week')),
            'team_id': team,
            'report_status': report_status,
            'practice_status': safe_str(injury.get('practice_status', '')),
            'injury_type': safe_str(injury.get('report_primary_injury', injury.get('primary_injury', ''))),
            'games_missed': 1 if report_status.lower() in ['out', 'doubtful'] else 0,
            'date_modified': safe_str(injury.get('date_modified', '')),
        })
    
    # Disable FK checks for injury data since some player_ids may not exist
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("DELETE FROM injuries WHERE season = ?", (season,))
        
        if rows:
            columns = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            col_str = ", ".join(columns)
            sql = f"INSERT INTO injuries ({col_str}) VALUES ({placeholders})"
            
            values = [tuple(r.get(c) for c in columns) for r in rows]
            conn.executemany(sql, values)
        
        conn.execute("PRAGMA foreign_keys=ON")
    
    logger.info(f"Ingested {len(rows)} injury records")
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    ingest_injuries()
