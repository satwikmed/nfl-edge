"""
Offensive identity profiling.
Analyzes each team's offensive tendencies, efficiency, and style of play.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS
from src.utils.db import get_connection, store_analysis, query

logger = logging.getLogger(__name__)


def profile_offense(team_id: str, season: int = None) -> Dict[str, Any]:
    """Build a complete offensive identity profile for a team."""
    season = season or CURRENT_SEASON
    
    # Get all offensive plays for the team
    plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ?
        AND play_type IN ('pass', 'run')
        AND epa IS NOT NULL
    """, (team_id, season))
    
    if not plays:
        return {}
    
    df = pd.DataFrame(plays)
    
    profile = {}
    
    # ── Pass/Run ratio ──────────────────────────────────────────
    total_plays = len(df)
    pass_plays = df[df['pass_or_run'] == 'pass']
    run_plays = df[df['pass_or_run'] == 'run']
    
    profile['total_plays'] = total_plays
    profile['pass_rate'] = round(len(pass_plays) / total_plays, 3) if total_plays > 0 else 0
    profile['run_rate'] = round(len(run_plays) / total_plays, 3) if total_plays > 0 else 0
    
    # Pass/Run by down
    down_tendencies = {}
    for down in [1, 2, 3, 4]:
        down_plays = df[df['down'] == down]
        if len(down_plays) > 0:
            down_tendencies[str(down)] = {
                'plays': len(down_plays),
                'pass_rate': round(len(down_plays[down_plays['pass_or_run'] == 'pass']) / len(down_plays), 3),
                'run_rate': round(len(down_plays[down_plays['pass_or_run'] == 'run']) / len(down_plays), 3),
                'avg_epa': round(float(down_plays['epa'].mean()), 3),
            }
    profile['down_tendencies'] = down_tendencies
    
    # ── EPA metrics ─────────────────────────────────────────────
    profile['epa_per_play'] = round(float(df['epa'].mean()), 3)
    profile['pass_epa_per_play'] = round(float(pass_plays['epa'].mean()), 3) if len(pass_plays) > 0 else 0
    profile['run_epa_per_play'] = round(float(run_plays['epa'].mean()), 3) if len(run_plays) > 0 else 0
    profile['success_rate'] = round(float((df['success'] == 1).mean()), 3)
    profile['pass_success_rate'] = round(float((pass_plays['success'] == 1).mean()), 3) if len(pass_plays) > 0 else 0
    profile['run_success_rate'] = round(float((run_plays['success'] == 1).mean()), 3) if len(run_plays) > 0 else 0
    
    # ── Explosive plays ─────────────────────────────────────────
    explosive = df[df['yards_gained'] >= 20]
    profile['explosive_rate'] = round(len(explosive) / total_plays, 3) if total_plays > 0 else 0
    profile['explosive_plays'] = len(explosive)
    
    # ── Shotgun usage ───────────────────────────────────────────
    profile['shotgun_rate'] = round(float(df['shotgun'].mean()), 3)
    profile['no_huddle_rate'] = round(float(df['no_huddle'].mean()), 3)
    
    # ── Personnel groupings ─────────────────────────────────────
    personnel_stats = {}
    if 'personnel_offense' in df.columns:
        for personnel, group in df.groupby('personnel_offense'):
            if personnel and len(group) >= 10:  # Min 10 plays
                personnel_stats[str(personnel)] = {
                    'plays': len(group),
                    'usage_rate': round(len(group) / total_plays, 3),
                    'epa_per_play': round(float(group['epa'].mean()), 3),
                    'success_rate': round(float((group['success'] == 1).mean()), 3),
                    'pass_rate': round(len(group[group['pass_or_run'] == 'pass']) / len(group), 3),
                }
    profile['personnel'] = dict(sorted(personnel_stats.items(), key=lambda x: x[1]['plays'], reverse=True)[:10])
    
    # ── Formation tendencies ────────────────────────────────────
    formation_stats = {}
    if 'formation' in df.columns:
        for formation, group in df.groupby('formation'):
            if formation and len(group) >= 10:
                formation_stats[str(formation)] = {
                    'plays': len(group),
                    'usage_rate': round(len(group) / total_plays, 3),
                    'epa_per_play': round(float(group['epa'].mean()), 3),
                }
    profile['formations'] = dict(sorted(formation_stats.items(), key=lambda x: x[1]['plays'], reverse=True)[:8])
    
    # ── Pace of play ────────────────────────────────────────────
    games = query("SELECT COUNT(DISTINCT game_id) as cnt FROM play_by_play WHERE team_id = ? AND season = ?",
                  (team_id, season))
    num_games = games[0]['cnt'] if games else 1
    profile['plays_per_game'] = round(total_plays / max(num_games, 1), 1)
    
    # ── Red zone analysis ───────────────────────────────────────
    red_zone = df[df['yardline_100'] <= 20]
    if len(red_zone) > 0:
        profile['red_zone'] = {
            'plays': len(red_zone),
            'pass_rate': round(len(red_zone[red_zone['pass_or_run'] == 'pass']) / len(red_zone), 3),
            'epa_per_play': round(float(red_zone['epa'].mean()), 3),
            'td_rate': round(float(red_zone['touchdown'].mean()), 3),
        }
    else:
        profile['red_zone'] = {'plays': 0, 'pass_rate': 0, 'epa_per_play': 0, 'td_rate': 0}
    
    # ── Air yards (depth of target) ─────────────────────────────
    air_yard_plays = pass_plays[pass_plays['air_yards'].notna()]
    if len(air_yard_plays) > 0:
        profile['avg_depth_of_target'] = round(float(air_yard_plays['air_yards'].mean()), 1)
        profile['deep_pass_rate'] = round(len(air_yard_plays[air_yard_plays['air_yards'] >= 20]) / len(air_yard_plays), 3)
    else:
        profile['avg_depth_of_target'] = 0
        profile['deep_pass_rate'] = 0
    
    # ── Scoring ─────────────────────────────────────────────────
    profile['touchdowns'] = int(df['touchdown'].sum())
    profile['turnovers'] = int(df['interception'].sum() + df['fumble'].sum())
    
    return profile


def profile_all_offenses(season: int = None):
    """Profile all 32 team offenses and store results."""
    season = season or CURRENT_SEASON
    logger.info(f"Profiling all team offenses for {season}...")
    
    results = {}
    for team_id in TEAM_ABBRS:
        try:
            profile = profile_offense(team_id, season)
            if profile:
                results[team_id] = profile
                
                # Calculate a composite offensive score (0-100)
                epa = profile.get('epa_per_play', 0)
                # Map EPA from about -0.2 to +0.2 range to 0-100
                score = max(0, min(100, (epa + 0.2) / 0.4 * 100))
                
                store_analysis(team_id, 'offensive_profile', profile,
                             score=round(score, 1), season=season)
                logger.info(f"  {team_id}: EPA/play={profile['epa_per_play']}, "
                          f"pass_rate={profile['pass_rate']}, "
                          f"plays={profile['total_plays']}")
        except Exception as e:
            logger.error(f"  {team_id}: Failed - {e}")
    
    logger.info(f"Profiled {len(results)} team offenses")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    profile_all_offenses()
