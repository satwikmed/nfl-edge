"""
Play-by-play data ingestion from nflverse via nfl_data_py.
This is the core dataset — every snap of the season with EPA, WP, and situational data.
"""

import logging
import nfl_data_py as nfl
import pandas as pd
import numpy as np

from src.utils.config import CURRENT_SEASON
from src.utils.db import get_connection, init_db

logger = logging.getLogger(__name__)

# Columns we want from the nflverse play-by-play data
PBP_COLUMNS = [
    'game_id', 'play_id', 'posteam', 'defteam', 'season', 'week',
    'qtr', 'half_seconds_remaining', 'game_seconds_remaining',
    'down', 'ydstogo', 'yardline_100',
    'play_type', 'pass', 'rush',
    'shotgun', 'no_huddle',
    'offense_personnel', 'defense_personnel',
    'offense_formation',
    'yards_gained', 'air_yards', 'yards_after_catch',
    'epa', 'wp', 'def_wp', 'wpa',
    'success', 'first_down_rush', 'first_down_pass', 'first_down_penalty',
    'td_team', 'interception', 'fumble', 'sack',
    'penalty', 'score_differential', 'posteam_score', 'defteam_score',
    'passer_player_id', 'rusher_player_id', 'receiver_player_id',
    'fourth_down_decision', 'fourth_down_converted',
    'goal_to_go', 'two_point_attempt', 'two_point_conv_result',
    'timeout', 'timeout_team',
    'field_goal_attempt', 'field_goal_result',
    'punt_attempt', 'extra_point_attempt',
    'desc',
]


def _classify_pass_or_run(row) -> str:
    """Classify play as pass or run."""
    if row.get('pass') == 1:
        return 'pass'
    elif row.get('rush') == 1:
        return 'run'
    return 'other'


def _extract_first_down(row) -> int:
    """Check if play resulted in a first down."""
    return int(
        row.get('first_down_rush', 0) == 1 or
        row.get('first_down_pass', 0) == 1 or
        row.get('first_down_penalty', 0) == 1
    )


def _extract_touchdown(row) -> int:
    """Check if play resulted in a touchdown."""
    return int(bool(row.get('td_team')))


def ingest_play_by_play(season: int = None, weeks: list = None):
    """
    Ingest play-by-play data for the specified season.
    
    Args:
        season: NFL season year (default: CURRENT_SEASON)
        weeks: Optional list of specific weeks to ingest
    """
    season = season or CURRENT_SEASON
    logger.info(f"Starting play-by-play ingestion for {season} season...")
    
    try:
        pbp = nfl.import_pbp_data([season])
    except Exception as e:
        logger.error(f"Failed to fetch play-by-play data: {e}")
        raise
    
    if pbp is None or len(pbp) == 0:
        logger.warning(f"No play-by-play data available for {season}")
        return 0
    
    logger.info(f"Fetched {len(pbp)} raw plays for {season}")
    
    # Filter to actual plays (exclude timeouts, penalties without plays, etc.)
    # Keep: pass, rush, field_goal, punt, extra_point, two_point_attempt, qb_kneel, qb_spike
    valid_play_types = ['pass', 'run', 'field_goal', 'punt', 'extra_point',
                        'qb_kneel', 'qb_spike', 'no_play']
    pbp = pbp[pbp['play_type'].isin(valid_play_types) | pbp['two_point_attempt'] == 1].copy()
    
    # Filter to specific weeks if requested
    if weeks:
        pbp = pbp[pbp['week'].isin(weeks)].copy()
    
    logger.info(f"Filtered to {len(pbp)} valid plays")
    
    # Available columns check — use what exists
    available_cols = set(pbp.columns)
    
    def fix_team(t):
        """Map nflverse 'LA' to 'LAR' for Rams."""
        if t == 'LA':
            return 'LAR'
        return t if pd.notna(t) else ''
    
    # Build rows for insertion
    rows = []
    for _, play in pbp.iterrows():
        row = {
            'game_id': play.get('game_id', ''),
            'play_id': int(play.get('play_id', 0)) if pd.notna(play.get('play_id')) else None,
            'team_id': fix_team(play.get('posteam', '')),
            'defteam_id': fix_team(play.get('defteam', '')),
            'season': int(season),
            'week': int(play.get('week', 0)) if pd.notna(play.get('week')) else None,
            'quarter': int(play.get('qtr', 0)) if pd.notna(play.get('qtr')) else None,
            'half_seconds_remaining': int(play.get('half_seconds_remaining', 0)) if pd.notna(play.get('half_seconds_remaining')) else None,
            'game_seconds_remaining': int(play.get('game_seconds_remaining', 0)) if pd.notna(play.get('game_seconds_remaining')) else None,
            'down': int(play.get('down', 0)) if pd.notna(play.get('down')) else None,
            'ydstogo': int(play.get('ydstogo', 0)) if pd.notna(play.get('ydstogo')) else None,
            'yardline_100': int(play.get('yardline_100', 0)) if pd.notna(play.get('yardline_100')) else None,
            'play_type': play.get('play_type', ''),
            'pass_or_run': _classify_pass_or_run(play),
            'shotgun': int(play.get('shotgun', 0)) if pd.notna(play.get('shotgun')) else 0,
            'no_huddle': int(play.get('no_huddle', 0)) if pd.notna(play.get('no_huddle')) else 0,
            'personnel_offense': play.get('offense_personnel', ''),
            'personnel_defense': play.get('defense_personnel', ''),
            'formation': play.get('offense_formation', ''),
            'yards_gained': float(play.get('yards_gained', 0)) if pd.notna(play.get('yards_gained')) else 0,
            'air_yards': float(play.get('air_yards', 0)) if pd.notna(play.get('air_yards')) else None,
            'yards_after_catch': float(play.get('yards_after_catch', 0)) if pd.notna(play.get('yards_after_catch')) else None,
            'epa': float(play.get('epa', 0)) if pd.notna(play.get('epa')) else None,
            'wp': float(play.get('wp', 0)) if pd.notna(play.get('wp')) else None,
            'def_wp': float(play.get('def_wp', 0)) if pd.notna(play.get('def_wp')) else None,
            'wpa': float(play.get('wpa', 0)) if pd.notna(play.get('wpa')) else None,
            'success': int(play.get('success', 0)) if pd.notna(play.get('success')) else 0,
            'first_down': _extract_first_down(play),
            'touchdown': _extract_touchdown(play),
            'interception': int(play.get('interception', 0)) if pd.notna(play.get('interception')) else 0,
            'fumble': int(play.get('fumble', 0)) if pd.notna(play.get('fumble')) else 0,
            'sack': int(play.get('sack', 0)) if pd.notna(play.get('sack')) else 0,
            'penalty': int(play.get('penalty', 0)) if pd.notna(play.get('penalty')) else 0,
            'score_differential': int(play.get('score_differential', 0)) if pd.notna(play.get('score_differential')) else 0,
            'posteam_score': int(play.get('posteam_score', 0)) if pd.notna(play.get('posteam_score')) else 0,
            'defteam_score': int(play.get('defteam_score', 0)) if pd.notna(play.get('defteam_score')) else 0,
            'passer_player_id': play.get('passer_player_id', ''),
            'rusher_player_id': play.get('rusher_player_id', ''),
            'receiver_player_id': play.get('receiver_player_id', ''),
            'fourth_down_decision': play.get('fourth_down_decision', ''),
            'fourth_down_converted': int(play.get('fourth_down_converted', 0)) if pd.notna(play.get('fourth_down_converted')) else None,
            'goal_to_go': int(play.get('goal_to_go', 0)) if pd.notna(play.get('goal_to_go')) else 0,
            'two_point_attempt': int(play.get('two_point_attempt', 0)) if pd.notna(play.get('two_point_attempt')) else 0,
            'two_point_conv_result': play.get('two_point_conv_result', ''),
            'timeout': int(play.get('timeout', 0)) if pd.notna(play.get('timeout')) else 0,
            'timeout_team': play.get('timeout_team', ''),
            'field_goal_attempt': int(play.get('field_goal_attempt', 0)) if pd.notna(play.get('field_goal_attempt')) else 0,
            'field_goal_result': play.get('field_goal_result', ''),
            'punt_attempt': int(play.get('punt_attempt', 0)) if pd.notna(play.get('punt_attempt')) else 0,
            'extra_point_attempt': int(play.get('extra_point_attempt', 0)) if pd.notna(play.get('extra_point_attempt')) else 0,
            'desc': str(play.get('desc', ''))[:500],  # Truncate long descriptions
        }
        
        # Clean NaN strings
        for key in row:
            if isinstance(row[key], float) and np.isnan(row[key]):
                row[key] = None
            elif isinstance(row[key], str) and row[key] == 'nan':
                row[key] = None
        
        rows.append(row)
    
    # Batch insert
    logger.info(f"Inserting {len(rows)} plays into database...")
    
    with get_connection() as conn:
        # Clear existing data for this season
        conn.execute("DELETE FROM play_by_play WHERE season = ?", (season,))
        
        columns = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT INTO play_by_play ({col_str}) VALUES ({placeholders})"
        
        # Insert in batches
        batch_size = 5000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            values = [tuple(r.get(c) for c in columns) for r in batch]
            conn.executemany(sql, values)
            logger.info(f"  Inserted batch {i // batch_size + 1} ({len(batch)} rows)")
    
    logger.info(f"Play-by-play ingestion complete: {len(rows)} plays")
    return len(rows)


def ingest_games(season: int = None):
    """Ingest game results for the season."""
    season = season or CURRENT_SEASON
    logger.info(f"Ingesting game results for {season}...")
    
    try:
        schedules = nfl.import_schedules([season])
    except Exception as e:
        logger.error(f"Failed to fetch schedule data: {e}")
        raise
    
    if schedules is None or len(schedules) == 0:
        logger.warning(f"No schedule data for {season}")
        return 0
    
    # Filter to completed games
    completed = schedules[schedules['result'].notna()].copy()
    logger.info(f"Found {len(completed)} completed games")
    
    rows = []
    for _, game in completed.iterrows():
        home_score = game.get('home_score', 0)
        away_score = game.get('away_score', 0)
        
        if pd.notna(home_score) and pd.notna(away_score):
            if home_score > away_score:
                result = 'home_win'
            elif away_score > home_score:
                result = 'away_win'
            else:
                result = 'tie'
        else:
            result = None
        
        home_team = game.get('home_team', '')
        away_team = game.get('away_team', '')
        if home_team == 'LA':
            home_team = 'LAR'
        if away_team == 'LA':
            away_team = 'LAR'
        
        rows.append({
            'game_id': game.get('game_id', ''),
            'season': int(season),
            'week': int(game.get('week', 0)) if pd.notna(game.get('week')) else None,
            'game_type': game.get('game_type', ''),
            'home_team': home_team,
            'away_team': away_team,
            'home_score': int(home_score) if pd.notna(home_score) else None,
            'away_score': int(away_score) if pd.notna(away_score) else None,
            'spread': float(game.get('spread_line', game.get('spread', 0))) if pd.notna(game.get('spread_line', game.get('spread'))) else None,
            'over_under': float(game.get('total_line', game.get('total', 0))) if pd.notna(game.get('total_line', game.get('total'))) else None,
            'result': result,
            'home_rest': int(game.get('home_rest', 0)) if pd.notna(game.get('home_rest')) else None,
            'away_rest': int(game.get('away_rest', 0)) if pd.notna(game.get('away_rest')) else None,
            'stadium': game.get('stadium', '') if pd.notna(game.get('stadium')) else '',
            'roof': game.get('roof', '') if pd.notna(game.get('roof')) else '',
            'surface': game.get('surface', '') if pd.notna(game.get('surface')) else '',
            'temp': float(game.get('temp', 0)) if pd.notna(game.get('temp')) else None,
            'wind': float(game.get('wind', 0)) if pd.notna(game.get('wind')) else None,
        })
    
    with get_connection() as conn:
        conn.execute("DELETE FROM games WHERE season = ?", (season,))
        
        columns = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT INTO games ({col_str}) VALUES ({placeholders})"
        values = [tuple(r.get(c) for c in columns) for r in rows]
        conn.executemany(sql, values)
    
    logger.info(f"Ingested {len(rows)} games")
    return len(rows)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    ingest_games()
    ingest_play_by_play()
