import sqlite3
from src.utils.db import query
res = query("""
        SELECT ps.*, p.name, p.position, p.position_group, p.age, p.experience,
               c.cap_hit_current, c.dead_cap, c.free_agent_year, c.guaranteed_remaining,
               c.total_value, c.avg_annual, c.contract_years
        FROM player_season ps
        JOIN players p ON ps.player_id = p.player_id
        LEFT JOIN contracts c ON ps.player_id = c.player_id
        WHERE ps.team_id = 'SEA' AND ps.season = 2025
        ORDER BY ps.total_epa DESC
    """)
print(len(res))
