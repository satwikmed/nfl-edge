"""
Configuration module for NFL Team Intelligence Command Center.
Central place for all paths, constants, and settings.
"""

import os
from pathlib import Path

# ── Project paths ──────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_PATH = DATA_DIR / "nfl_teams.db"
DASHBOARD_DATA_DIR = PROJECT_ROOT / "dashboard" / "public" / "data"

# Ensure directories exist
for d in [RAW_DIR, PROCESSED_DIR, DASHBOARD_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Season configuration ───────────────────────────────────────────
CURRENT_SEASON = 2025  # 2025-2026 NFL season

# ── NFL team metadata ─────────────────────────────────────────────
# Full 32-team list with abbreviation, city, name, conference, division,
# latitude, longitude, stadium
TEAMS = [
    {"abbr": "ARI", "city": "Glendale", "state": "AZ", "name": "Arizona Cardinals", "conference": "NFC", "division": "NFC West", "lat": 33.5276, "lng": -112.2626, "stadium": "State Farm Stadium"},
    {"abbr": "ATL", "city": "Atlanta", "state": "GA", "name": "Atlanta Falcons", "conference": "NFC", "division": "NFC South", "lat": 33.7554, "lng": -84.4010, "stadium": "Mercedes-Benz Stadium"},
    {"abbr": "BAL", "city": "Baltimore", "state": "MD", "name": "Baltimore Ravens", "conference": "AFC", "division": "AFC North", "lat": 39.2780, "lng": -76.6227, "stadium": "M&T Bank Stadium"},
    {"abbr": "BUF", "city": "Orchard Park", "state": "NY", "name": "Buffalo Bills", "conference": "AFC", "division": "AFC East", "lat": 42.7738, "lng": -78.7870, "stadium": "Highmark Stadium"},
    {"abbr": "CAR", "city": "Charlotte", "state": "NC", "name": "Carolina Panthers", "conference": "NFC", "division": "NFC South", "lat": 35.2258, "lng": -80.8528, "stadium": "Bank of America Stadium"},
    {"abbr": "CHI", "city": "Chicago", "state": "IL", "name": "Chicago Bears", "conference": "NFC", "division": "NFC North", "lat": 41.8623, "lng": -87.6167, "stadium": "Soldier Field"},
    {"abbr": "CIN", "city": "Cincinnati", "state": "OH", "name": "Cincinnati Bengals", "conference": "AFC", "division": "AFC North", "lat": 39.0955, "lng": -84.5161, "stadium": "Paycor Stadium"},
    {"abbr": "CLE", "city": "Cleveland", "state": "OH", "name": "Cleveland Browns", "conference": "AFC", "division": "AFC North", "lat": 41.5061, "lng": -81.6995, "stadium": "Cleveland Browns Stadium"},
    {"abbr": "DAL", "city": "Arlington", "state": "TX", "name": "Dallas Cowboys", "conference": "NFC", "division": "NFC East", "lat": 32.7473, "lng": -97.0945, "stadium": "AT&T Stadium"},
    {"abbr": "DEN", "city": "Denver", "state": "CO", "name": "Denver Broncos", "conference": "AFC", "division": "AFC West", "lat": 39.7439, "lng": -105.0201, "stadium": "Empower Field at Mile High"},
    {"abbr": "DET", "city": "Detroit", "state": "MI", "name": "Detroit Lions", "conference": "NFC", "division": "NFC North", "lat": 42.3400, "lng": -83.0456, "stadium": "Ford Field"},
    {"abbr": "GB", "city": "Green Bay", "state": "WI", "name": "Green Bay Packers", "conference": "NFC", "division": "NFC North", "lat": 44.5013, "lng": -88.0622, "stadium": "Lambeau Field"},
    {"abbr": "HOU", "city": "Houston", "state": "TX", "name": "Houston Texans", "conference": "AFC", "division": "AFC South", "lat": 29.6847, "lng": -95.4107, "stadium": "NRG Stadium"},
    {"abbr": "IND", "city": "Indianapolis", "state": "IN", "name": "Indianapolis Colts", "conference": "AFC", "division": "AFC South", "lat": 39.7601, "lng": -86.1639, "stadium": "Lucas Oil Stadium"},
    {"abbr": "JAX", "city": "Jacksonville", "state": "FL", "name": "Jacksonville Jaguars", "conference": "AFC", "division": "AFC South", "lat": 30.3239, "lng": -81.6373, "stadium": "EverBank Stadium"},
    {"abbr": "KC", "city": "Kansas City", "state": "MO", "name": "Kansas City Chiefs", "conference": "AFC", "division": "AFC West", "lat": 39.0489, "lng": -94.4839, "stadium": "GEHA Field at Arrowhead Stadium"},
    {"abbr": "LV", "city": "Las Vegas", "state": "NV", "name": "Las Vegas Raiders", "conference": "AFC", "division": "AFC West", "lat": 36.0908, "lng": -115.1833, "stadium": "Allegiant Stadium"},
    {"abbr": "LAC", "city": "Inglewood", "state": "CA", "name": "Los Angeles Chargers", "conference": "AFC", "division": "AFC West", "lat": 33.9535, "lng": -118.3392, "stadium": "SoFi Stadium"},
    {"abbr": "LAR", "city": "Inglewood", "state": "CA", "name": "Los Angeles Rams", "conference": "NFC", "division": "NFC West", "lat": 33.9535, "lng": -118.3392, "stadium": "SoFi Stadium"},
    {"abbr": "MIA", "city": "Miami Gardens", "state": "FL", "name": "Miami Dolphins", "conference": "AFC", "division": "AFC East", "lat": 25.9580, "lng": -80.2389, "stadium": "Hard Rock Stadium"},
    {"abbr": "MIN", "city": "Minneapolis", "state": "MN", "name": "Minnesota Vikings", "conference": "NFC", "division": "NFC North", "lat": 44.9736, "lng": -93.2575, "stadium": "U.S. Bank Stadium"},
    {"abbr": "NE", "city": "Foxborough", "state": "MA", "name": "New England Patriots", "conference": "AFC", "division": "AFC East", "lat": 42.0909, "lng": -71.2643, "stadium": "Gillette Stadium"},
    {"abbr": "NO", "city": "New Orleans", "state": "LA", "name": "New Orleans Saints", "conference": "NFC", "division": "NFC South", "lat": 29.9511, "lng": -90.0812, "stadium": "Caesars Superdome"},
    {"abbr": "NYG", "city": "East Rutherford", "state": "NJ", "name": "New York Giants", "conference": "NFC", "division": "NFC East", "lat": 40.8128, "lng": -74.0742, "stadium": "MetLife Stadium"},
    {"abbr": "NYJ", "city": "East Rutherford", "state": "NJ", "name": "New York Jets", "conference": "AFC", "division": "AFC East", "lat": 40.8128, "lng": -74.0742, "stadium": "MetLife Stadium"},
    {"abbr": "PHI", "city": "Philadelphia", "state": "PA", "name": "Philadelphia Eagles", "conference": "NFC", "division": "NFC East", "lat": 39.9008, "lng": -75.1675, "stadium": "Lincoln Financial Field"},
    {"abbr": "PIT", "city": "Pittsburgh", "state": "PA", "name": "Pittsburgh Steelers", "conference": "AFC", "division": "AFC North", "lat": 40.4468, "lng": -80.0158, "stadium": "Acrisure Stadium"},
    {"abbr": "SF", "city": "Santa Clara", "state": "CA", "name": "San Francisco 49ers", "conference": "NFC", "division": "NFC West", "lat": 37.4033, "lng": -121.9694, "stadium": "Levi's Stadium"},
    {"abbr": "SEA", "city": "Seattle", "state": "WA", "name": "Seattle Seahawks", "conference": "NFC", "division": "NFC West", "lat": 47.5952, "lng": -122.3316, "stadium": "Lumen Field"},
    {"abbr": "TB", "city": "Tampa", "state": "FL", "name": "Tampa Bay Buccaneers", "conference": "NFC", "division": "NFC South", "lat": 27.9759, "lng": -82.5033, "stadium": "Raymond James Stadium"},
    {"abbr": "TEN", "city": "Nashville", "state": "TN", "name": "Tennessee Titans", "conference": "AFC", "division": "AFC South", "lat": 36.1665, "lng": -86.7713, "stadium": "Nissan Stadium"},
    {"abbr": "WAS", "city": "Landover", "state": "MD", "name": "Washington Commanders", "conference": "NFC", "division": "NFC East", "lat": 38.9076, "lng": -76.8645, "stadium": "Northwest Stadium"},
]

# Quick lookup dicts
TEAM_BY_ABBR = {t["abbr"]: t for t in TEAMS}
TEAM_ABBRS = [t["abbr"] for t in TEAMS]

# ── Position groups ────────────────────────────────────────────────
POSITION_GROUPS = {
    "QB": ["QB"],
    "RB": ["RB", "FB"],
    "WR": ["WR"],
    "TE": ["TE"],
    "OL": ["T", "OT", "G", "OG", "C", "OL"],
    "DL": ["DE", "DT", "NT", "DL"],
    "LB": ["ILB", "OLB", "MLB", "LB"],
    "DB": ["CB", "S", "FS", "SS", "DB"],
    "K": ["K"],
    "P": ["P"],
    "LS": ["LS"],
}

def get_position_group(position: str) -> str:
    """Map a specific position to its group."""
    if position is None:
        return "UNKNOWN"
    for group, positions in POSITION_GROUPS.items():
        if position.upper() in positions:
            return group
    return "UNKNOWN"

# ── Replacement-level thresholds ───────────────────────────────────
# 60th percentile EPA/play by position group (will be calibrated from data)
REPLACEMENT_LEVEL_PERCENTILE = 0.60

# ── Logging ────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
