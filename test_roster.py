import sqlite3
from src.utils.db import query
print(query("SELECT COUNT(*) FROM player_season WHERE team_id='SEA'"))
print(query("SELECT * FROM player_season WHERE team_id='SEA' LIMIT 1"))
