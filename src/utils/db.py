"""
Database utility module for NFL Team Intelligence Command Center.
Handles schema creation, connections, and common query patterns.
"""

import sqlite3
import json
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Any

from src.utils.config import DB_PATH

logger = logging.getLogger(__name__)


# ── Schema DDL ─────────────────────────────────────────────────────
SCHEMA_SQL = """
-- Team metadata
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT UNIQUE NOT NULL,
    city TEXT,
    state TEXT,
    division TEXT,
    conference TEXT,
    latitude REAL,
    longitude REAL,
    stadium TEXT,
    head_coach TEXT,
    offensive_coordinator TEXT,
    defensive_coordinator TEXT,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player roster
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team_id TEXT,
    position TEXT,
    position_group TEXT,
    age INTEGER,
    experience INTEGER,
    height TEXT,
    weight INTEGER,
    draft_round INTEGER,
    draft_pick INTEGER,
    draft_year INTEGER,
    college TEXT,
    status TEXT,
    jersey_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Contract data
CREATE TABLE IF NOT EXISTS contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    team_id TEXT,
    total_value REAL,
    avg_annual REAL,
    cap_hit_current REAL,
    dead_cap REAL,
    guaranteed_remaining REAL,
    free_agent_year INTEGER,
    contract_years INTEGER,
    base_salary REAL,
    signing_bonus_proration REAL,
    roster_bonus REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Play-by-play data
CREATE TABLE IF NOT EXISTS play_by_play (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    play_id INTEGER,
    team_id TEXT,
    defteam_id TEXT,
    season INTEGER,
    week INTEGER,
    quarter INTEGER,
    half_seconds_remaining INTEGER,
    game_seconds_remaining INTEGER,
    down INTEGER,
    ydstogo INTEGER,
    yardline_100 INTEGER,
    play_type TEXT,
    pass_or_run TEXT,
    shotgun INTEGER,
    no_huddle INTEGER,
    personnel_offense TEXT,
    personnel_defense TEXT,
    formation TEXT,
    yards_gained REAL,
    air_yards REAL,
    yards_after_catch REAL,
    epa REAL,
    wp REAL,
    def_wp REAL,
    wpa REAL,
    success INTEGER,
    first_down INTEGER,
    touchdown INTEGER,
    interception INTEGER,
    fumble INTEGER,
    sack INTEGER,
    penalty INTEGER,
    score_differential INTEGER,
    posteam_score INTEGER,
    defteam_score INTEGER,
    passer_player_id TEXT,
    rusher_player_id TEXT,
    receiver_player_id TEXT,
    fourth_down_decision TEXT,
    fourth_down_converted INTEGER,
    goal_to_go INTEGER,
    two_point_attempt INTEGER,
    two_point_conv_result TEXT,
    timeout INTEGER,
    timeout_team TEXT,
    field_goal_attempt INTEGER,
    field_goal_result TEXT,
    punt_attempt INTEGER,
    extra_point_attempt INTEGER,
    desc TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Player weekly stats
CREATE TABLE IF NOT EXISTS player_weekly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    season INTEGER,
    week INTEGER,
    team_id TEXT,
    position TEXT,
    games INTEGER DEFAULT 0,
    snaps INTEGER DEFAULT 0,
    snap_share REAL DEFAULT 0,

    -- Passing
    completions INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    passing_yards REAL DEFAULT 0,
    passing_tds INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    sacks_taken INTEGER DEFAULT 0,
    passing_epa REAL DEFAULT 0,
    cpoe REAL DEFAULT 0,
    
    -- Rushing
    carries INTEGER DEFAULT 0,
    rushing_yards REAL DEFAULT 0,
    rushing_tds INTEGER DEFAULT 0,
    rushing_epa REAL DEFAULT 0,
    
    -- Receiving
    targets INTEGER DEFAULT 0,
    receptions INTEGER DEFAULT 0,
    receiving_yards REAL DEFAULT 0,
    receiving_tds INTEGER DEFAULT 0,
    receiving_epa REAL DEFAULT 0,
    target_share REAL DEFAULT 0,
    air_yards_share REAL DEFAULT 0,
    
    -- Defense
    tackles REAL DEFAULT 0,
    tackles_for_loss REAL DEFAULT 0,
    sacks REAL DEFAULT 0,
    interceptions_def INTEGER DEFAULT 0,
    pass_deflections INTEGER DEFAULT 0,
    forced_fumbles INTEGER DEFAULT 0,
    fumble_recoveries INTEGER DEFAULT 0,
    
    -- Advanced
    epa_per_play REAL DEFAULT 0,
    fantasy_points REAL DEFAULT 0,
    fantasy_points_ppr REAL DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season, week),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Player season aggregates
CREATE TABLE IF NOT EXISTS player_season (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    season INTEGER,
    team_id TEXT,
    position TEXT,
    games INTEGER DEFAULT 0,
    total_snaps INTEGER DEFAULT 0,
    avg_snap_share REAL DEFAULT 0,

    -- Passing aggregates
    completions INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    passing_yards REAL DEFAULT 0,
    passing_tds INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    sacks_taken INTEGER DEFAULT 0,
    total_passing_epa REAL DEFAULT 0,
    avg_cpoe REAL DEFAULT 0,
    
    -- Rushing aggregates
    carries INTEGER DEFAULT 0,
    rushing_yards REAL DEFAULT 0,
    rushing_tds INTEGER DEFAULT 0,
    total_rushing_epa REAL DEFAULT 0,
    
    -- Receiving aggregates
    targets INTEGER DEFAULT 0,
    receptions INTEGER DEFAULT 0,
    receiving_yards REAL DEFAULT 0,
    receiving_tds INTEGER DEFAULT 0,
    total_receiving_epa REAL DEFAULT 0,
    avg_target_share REAL DEFAULT 0,
    
    -- Defense aggregates
    tackles REAL DEFAULT 0,
    tackles_for_loss REAL DEFAULT 0,
    sacks REAL DEFAULT 0,
    interceptions_def INTEGER DEFAULT 0,
    pass_deflections INTEGER DEFAULT 0,
    forced_fumbles INTEGER DEFAULT 0,
    fumble_recoveries INTEGER DEFAULT 0,
    
    -- Advanced
    total_epa REAL DEFAULT 0,
    epa_per_play REAL DEFAULT 0,
    fantasy_points REAL DEFAULT 0,
    fantasy_points_ppr REAL DEFAULT 0,

    -- VOR and cap efficiency (computed by engines)
    vor REAL DEFAULT 0,
    cap_efficiency REAL DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Game results
CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    season INTEGER,
    week INTEGER,
    game_type TEXT,
    home_team TEXT,
    away_team TEXT,
    home_score INTEGER,
    away_score INTEGER,
    spread REAL,
    over_under REAL,
    result TEXT,
    home_rest INTEGER,
    away_rest INTEGER,
    stadium TEXT,
    roof TEXT,
    surface TEXT,
    temp REAL,
    wind REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team) REFERENCES teams(team_id),
    FOREIGN KEY (away_team) REFERENCES teams(team_id)
);

-- Injury reports
CREATE TABLE IF NOT EXISTS injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    season INTEGER,
    week INTEGER,
    team_id TEXT,
    report_status TEXT,
    practice_status TEXT,
    injury_type TEXT,
    games_missed INTEGER DEFAULT 0,
    date_modified TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Analysis results (JSON blobs per team per engine)
CREATE TABLE IF NOT EXISTS team_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id TEXT NOT NULL,
    season INTEGER,
    analysis_type TEXT NOT NULL,  -- 'profile', 'play_calling', 'roster_value', 'in_game_decisions', 'composite'
    analysis_data TEXT NOT NULL,  -- JSON blob
    grade TEXT,  -- A through F
    score REAL,  -- Numeric score 0-100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(team_id, season, analysis_type),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_pbp_team ON play_by_play(team_id);
CREATE INDEX IF NOT EXISTS idx_pbp_game ON play_by_play(game_id);
CREATE INDEX IF NOT EXISTS idx_pbp_season_week ON play_by_play(season, week);
CREATE INDEX IF NOT EXISTS idx_pbp_down ON play_by_play(down);
CREATE INDEX IF NOT EXISTS idx_pbp_play_type ON play_by_play(play_type);
CREATE INDEX IF NOT EXISTS idx_player_weekly_player ON player_weekly(player_id);
CREATE INDEX IF NOT EXISTS idx_player_weekly_team ON player_weekly(team_id);
CREATE INDEX IF NOT EXISTS idx_player_season_team ON player_season(team_id);
CREATE INDEX IF NOT EXISTS idx_contracts_team ON contracts(team_id);
CREATE INDEX IF NOT EXISTS idx_contracts_player ON contracts(player_id);
CREATE INDEX IF NOT EXISTS idx_injuries_player ON injuries(player_id);
CREATE INDEX IF NOT EXISTS idx_team_analysis_team ON team_analysis(team_id);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
"""


@contextmanager
def get_connection(db_path: Optional[Path] = None):
    """Context manager for database connections."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path] = None):
    """Initialize the database with the full schema."""
    path = db_path or DB_PATH
    logger.info(f"Initializing database at {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as conn:
        conn.executescript(SCHEMA_SQL)
    logger.info("Database schema created successfully")


def insert_many(table: str, rows: list[dict], db_path: Optional[Path] = None,
                replace: bool = False):
    """Bulk insert rows into a table.
    
    Args:
        table: Table name
        rows: List of dicts, keys matching column names
        db_path: Optional database path override
        replace: If True, use INSERT OR REPLACE
    """
    if not rows:
        return 0
    
    columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    col_str = ", ".join(columns)
    verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
    sql = f"{verb} INTO {table} ({col_str}) VALUES ({placeholders})"
    
    values = [tuple(row.get(c) for c in columns) for row in rows]
    
    with get_connection(db_path) as conn:
        conn.executemany(sql, values)
        count = conn.total_changes
    
    logger.info(f"Inserted {count} rows into {table}")
    return count


def query(sql: str, params: tuple = (), db_path: Optional[Path] = None) -> list[dict]:
    """Execute a query and return results as list of dicts."""
    with get_connection(db_path) as conn:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def store_analysis(team_id: str, analysis_type: str, data: dict,
                   grade: str = None, score: float = None,
                   season: int = None, db_path: Optional[Path] = None):
    """Store analysis results for a team."""
    from src.utils.config import CURRENT_SEASON
    season = season or CURRENT_SEASON
    
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO team_analysis
            (team_id, season, analysis_type, analysis_data, grade, score, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (team_id, season, analysis_type, json.dumps(data), grade, score))
    
    logger.info(f"Stored {analysis_type} analysis for {team_id}")


def get_analysis(team_id: str, analysis_type: str,
                 season: int = None, db_path: Optional[Path] = None) -> Optional[dict]:
    """Retrieve stored analysis for a team."""
    from src.utils.config import CURRENT_SEASON
    season = season or CURRENT_SEASON
    
    results = query(
        "SELECT analysis_data, grade, score FROM team_analysis "
        "WHERE team_id = ? AND analysis_type = ? AND season = ?",
        (team_id, analysis_type, season), db_path
    )
    
    if results:
        row = results[0]
        return {
            "data": json.loads(row["analysis_data"]),
            "grade": row["grade"],
            "score": row["score"]
        }
    return None


def get_table_count(table: str, db_path: Optional[Path] = None) -> int:
    """Get row count for a table."""
    results = query(f"SELECT COUNT(*) as cnt FROM {table}", db_path=db_path)
    return results[0]["cnt"] if results else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print(f"Database initialized at {DB_PATH}")
    print(f"File size: {DB_PATH.stat().st_size / 1024:.1f} KB")
