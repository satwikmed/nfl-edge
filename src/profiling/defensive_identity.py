"""
Defensive identity profiling.
Analyzes each team's defensive tendencies, pressure, coverage, and efficiency.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS
from src.utils.db import get_connection, store_analysis, query

logger = logging.getLogger(__name__)


def profile_defense(team_id: str, season: int = None) -> Dict[str, Any]:
    """Build a complete defensive identity profile for a team."""
    season = season or CURRENT_SEASON
    
    # Get all plays where this team was on defense
    plays = query("""
        SELECT * FROM play_by_play
        WHERE defteam_id = ? AND season = ?
        AND play_type IN ('pass', 'run')
        AND epa IS NOT NULL
    """, (team_id, season))
    
    if not plays:
        return {}
    
    df = pd.DataFrame(plays)
    total_plays = len(df)
    
    pass_plays = df[df['pass_or_run'] == 'pass']
    run_plays = df[df['pass_or_run'] == 'run']
    
    profile = {}
    
    # ── Overall defensive EPA (inverted — negative EPA = good defense) ──
    profile['total_plays_faced'] = total_plays
    profile['epa_per_play_allowed'] = round(float(df['epa'].mean()), 3)
    profile['pass_epa_allowed'] = round(float(pass_plays['epa'].mean()), 3) if len(pass_plays) > 0 else 0
    profile['run_epa_allowed'] = round(float(run_plays['epa'].mean()), 3) if len(run_plays) > 0 else 0
    profile['success_rate_allowed'] = round(float((df['success'] == 1).mean()), 3)
    
    # ── Sack and pressure metrics ───────────────────────────────
    sacks = int(df['sack'].sum())
    profile['sacks'] = sacks
    profile['sack_rate'] = round(sacks / len(pass_plays), 3) if len(pass_plays) > 0 else 0
    
    # ── Turnover generation ─────────────────────────────────────
    interceptions = int(df['interception'].sum())
    fumbles = int(df['fumble'].sum())
    profile['interceptions'] = interceptions
    profile['fumbles_forced'] = fumbles
    profile['turnover_rate'] = round((interceptions + fumbles) / total_plays, 3) if total_plays > 0 else 0
    
    # ── Explosive plays allowed ─────────────────────────────────
    explosive_allowed = df[df['yards_gained'] >= 20]
    profile['explosive_allowed'] = len(explosive_allowed)
    profile['explosive_rate_allowed'] = round(len(explosive_allowed) / total_plays, 3) if total_plays > 0 else 0
    
    # ── Third down defense ──────────────────────────────────────
    third_down = df[df['down'] == 3]
    if len(third_down) > 0:
        third_conversions = third_down[third_down['first_down'] == 1]
        profile['third_down_conversion_allowed'] = round(len(third_conversions) / len(third_down), 3)
        profile['third_down_epa_allowed'] = round(float(third_down['epa'].mean()), 3)
    else:
        profile['third_down_conversion_allowed'] = 0
        profile['third_down_epa_allowed'] = 0
    
    # ── Red zone defense ────────────────────────────────────────
    red_zone = df[df['yardline_100'] <= 20]
    if len(red_zone) > 0:
        profile['red_zone_defense'] = {
            'plays': len(red_zone),
            'td_rate_allowed': round(float(red_zone['touchdown'].mean()), 3),
            'epa_per_play_allowed': round(float(red_zone['epa'].mean()), 3),
        }
    else:
        profile['red_zone_defense'] = {'plays': 0, 'td_rate_allowed': 0, 'epa_per_play_allowed': 0}
    
    # ── Down and distance defense ───────────────────────────────
    down_defense = {}
    for down in [1, 2, 3, 4]:
        down_plays = df[df['down'] == down]
        if len(down_plays) > 0:
            down_defense[str(down)] = {
                'plays': len(down_plays),
                'epa_allowed': round(float(down_plays['epa'].mean()), 3),
                'success_rate_allowed': round(float((down_plays['success'] == 1).mean()), 3),
                'avg_yards_allowed': round(float(down_plays['yards_gained'].mean()), 1),
            }
    profile['down_defense'] = down_defense
    
    # ── Yards allowed breakdown ─────────────────────────────────
    profile['avg_yards_per_play_allowed'] = round(float(df['yards_gained'].mean()), 1)
    profile['avg_pass_yards_allowed'] = round(float(pass_plays['yards_gained'].mean()), 1) if len(pass_plays) > 0 else 0
    profile['avg_rush_yards_allowed'] = round(float(run_plays['yards_gained'].mean()), 1) if len(run_plays) > 0 else 0
    
    # ── Points and scoring allowed ──────────────────────────────
    profile['touchdowns_allowed'] = int(df['touchdown'].sum())
    
    # ── Opponent pass/run ratio faced ───────────────────────────
    profile['opponent_pass_rate'] = round(len(pass_plays) / total_plays, 3) if total_plays > 0 else 0
    profile['opponent_run_rate'] = round(len(run_plays) / total_plays, 3) if total_plays > 0 else 0
    
    # ── Personnel defense ───────────────────────────────────────
    personnel_defense = {}
    if 'personnel_defense' in df.columns:
        for personnel, group in df.groupby('personnel_defense'):
            if personnel and len(group) >= 10:
                personnel_defense[str(personnel)] = {
                    'plays': len(group),
                    'usage_rate': round(len(group) / total_plays, 3),
                    'epa_allowed': round(float(group['epa'].mean()), 3),
                }
    profile['defensive_personnel'] = dict(sorted(personnel_defense.items(), 
                                                  key=lambda x: x[1]['plays'], reverse=True)[:8])
    
    # ── Half adjustments ────────────────────────────────────────
    first_half = df[df['quarter'].isin([1, 2])]
    second_half = df[df['quarter'].isin([3, 4])]
    
    if len(first_half) > 0 and len(second_half) > 0:
        profile['first_half_epa_allowed'] = round(float(first_half['epa'].mean()), 3)
        profile['second_half_epa_allowed'] = round(float(second_half['epa'].mean()), 3)
        profile['halftime_adjustment'] = round(
            profile['first_half_epa_allowed'] - profile['second_half_epa_allowed'], 3
        )
    
    return profile


def profile_all_defenses(season: int = None):
    """Profile all 32 team defenses and store results."""
    season = season or CURRENT_SEASON
    logger.info(f"Profiling all team defenses for {season}...")
    
    results = {}
    for team_id in TEAM_ABBRS:
        try:
            profile = profile_defense(team_id, season)
            if profile:
                results[team_id] = profile
                
                # Score: lower EPA allowed = better defense (invert for 0-100)
                epa = profile.get('epa_per_play_allowed', 0)
                score = max(0, min(100, (-epa + 0.2) / 0.4 * 100))
                
                store_analysis(team_id, 'defensive_profile', profile,
                             score=round(score, 1), season=season)
                logger.info(f"  {team_id}: EPA/play allowed={profile['epa_per_play_allowed']}, "
                          f"sack_rate={profile['sack_rate']}, "
                          f"turnover_rate={profile['turnover_rate']}")
        except Exception as e:
            logger.error(f"  {team_id}: Failed - {e}")
    
    logger.info(f"Profiled {len(results)} team defenses")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    profile_all_defenses()
