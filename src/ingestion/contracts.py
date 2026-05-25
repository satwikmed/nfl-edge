"""
Contract and salary cap data ingestion.
Uses nfl_data_py's built-in import_contracts() which pulls from OverTheCap.
"""

import logging
import nfl_data_py as nfl
import pandas as pd
import numpy as np

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS
from src.utils.db import get_connection, init_db, query

logger = logging.getLogger(__name__)

# Total salary cap for 2025 season
SALARY_CAP_2025 = 272_600_000

# Map OTC team names to standard abbreviations
OTC_TEAM_MAP = {
    "Cardinals": "ARI", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF",
    "Panthers": "CAR", "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE",
    "Cowboys": "DAL", "Broncos": "DEN", "Lions": "DET", "Packers": "GB",
    "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX", "Chiefs": "KC",
    "Raiders": "LV", "Chargers": "LAC", "Rams": "LAR", "Dolphins": "MIA",
    "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG",
    "Jets": "NYJ", "Eagles": "PHI", "Steelers": "PIT", "49ers": "SF",
    "Seahawks": "SEA", "Buccaneers": "TB", "Titans": "TEN", "Commanders": "WAS",
    # Handle multi-team entries
    "GB/NYJ": "GB", "NYJ/GB": "NYJ",
}


def _resolve_team(team_name: str) -> str:
    """Resolve OTC team name to standard abbreviation."""
    if not team_name or pd.isna(team_name):
        return ''
    
    # Direct match
    if team_name in OTC_TEAM_MAP:
        return OTC_TEAM_MAP[team_name]
    
    # Check if it's already an abbreviation
    if team_name in TEAM_ABBRS:
        return team_name
    
    # Partial match
    for otc_name, abbr in OTC_TEAM_MAP.items():
        if otc_name.lower() in team_name.lower():
            return abbr
    
    return ''


def ingest_contracts(season: int = None):
    """
    Ingest contract data using nfl_data_py's import_contracts().
    This pulls comprehensive OTC data including value, APY, guaranteed money.
    """
    season = season or CURRENT_SEASON
    logger.info(f"Ingesting contract data for {season}...")
    
    try:
        contracts = nfl.import_contracts()
    except Exception as e:
        logger.error(f"Failed to fetch contract data: {e}")
        raise
    
    if contracts is None or len(contracts) == 0:
        logger.warning("No contract data available")
        return 0
    
    logger.info(f"Fetched {len(contracts)} total contracts from OTC")
    
    # Filter to active contracts only
    active = contracts[contracts['is_active'] == True].copy()
    logger.info(f"Active contracts: {len(active)}")
    
    # Get player ID mapping from our roster
    players = query("SELECT player_id, name, team_id FROM players")
    
    # Build player lookup by name (lowercase)
    player_lookup = {}
    for p in players:
        name = p['name'].lower().strip()
        player_lookup[name] = p
        # Also add without suffix (Jr., III, etc.)
        clean_name = name.rstrip('.').replace(' jr', '').replace(' sr', '').replace(' iii', '').replace(' ii', '').strip()
        if clean_name != name:
            player_lookup[clean_name] = p
    
    # Also build lookup by gsis_id
    gsis_lookup = {p['player_id']: p for p in players}
    
    rows = []
    matched = 0
    unmatched = 0
    
    for _, contract in active.iterrows():
        player_name = str(contract.get('player', '')).strip()
        team_name = str(contract.get('team', '')).strip()
        team_abbr = _resolve_team(team_name)
        
        # Try to match by gsis_id first
        gsis_id = contract.get('gsis_id', '')
        player_info = None
        
        if gsis_id and pd.notna(gsis_id) and str(gsis_id) in gsis_lookup:
            player_info = gsis_lookup[str(gsis_id)]
            matched += 1
        else:
            # Try name match
            name_lower = player_name.lower().strip()
            if name_lower in player_lookup:
                player_info = player_lookup[name_lower]
                matched += 1
            else:
                unmatched += 1
                continue
        
        player_id = player_info['player_id']
        
        # Parse contract values (in millions from OTC)
        def safe_millions(val):
            """Convert OTC value (in millions) to actual dollars."""
            if pd.isna(val) or val is None:
                return 0.0
            return float(val) * 1_000_000
        
        total_value = safe_millions(contract.get('value', 0))
        apy = safe_millions(contract.get('apy', 0))
        guaranteed = safe_millions(contract.get('guaranteed', 0))
        years = int(contract.get('years', 1)) if pd.notna(contract.get('years')) else 1
        year_signed = int(contract.get('year_signed', season)) if pd.notna(contract.get('year_signed')) else season
        
        # Estimate current cap hit based on APY
        cap_hit = apy  # Simplified: APY ≈ cap hit
        
        # Estimate dead cap (prorated signing bonus remaining)
        years_remaining = max(1, years - (season - year_signed))
        dead_cap = guaranteed * (years_remaining / max(years, 1))
        
        # Estimate free agent year
        free_agent_year = year_signed + years
        
        rows.append({
            'player_id': player_id,
            'team_id': team_abbr or player_info.get('team_id', ''),
            'total_value': round(total_value),
            'avg_annual': round(apy),
            'cap_hit_current': round(cap_hit),
            'dead_cap': round(dead_cap),
            'guaranteed_remaining': round(guaranteed * (years_remaining / max(years, 1))),
            'free_agent_year': free_agent_year,
            'contract_years': years,
            'base_salary': round(cap_hit * 0.65),  # Estimated base
            'signing_bonus_proration': round(cap_hit * 0.25),
            'roster_bonus': round(cap_hit * 0.10),
        })
    
    # Insert into database
    with get_connection() as conn:
        conn.execute("DELETE FROM contracts")
        
        for row in rows:
            conn.execute("""
                INSERT OR REPLACE INTO contracts
                (player_id, team_id, total_value, avg_annual, cap_hit_current,
                 dead_cap, guaranteed_remaining, free_agent_year, contract_years,
                 base_salary, signing_bonus_proration, roster_bonus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['player_id'], row['team_id'],
                row['total_value'], row['avg_annual'], row['cap_hit_current'],
                row['dead_cap'], row['guaranteed_remaining'],
                row['free_agent_year'], row['contract_years'],
                row['base_salary'], row['signing_bonus_proration'],
                row['roster_bonus'],
            ))
    
    logger.info(f"Ingested {len(rows)} contracts (matched: {matched}, unmatched: {unmatched})")
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    ingest_contracts()
