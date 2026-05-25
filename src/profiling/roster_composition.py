"""
Roster composition profiling.
Analyzes age distribution, experience, cap allocation, and roster depth.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS, POSITION_GROUPS
from src.utils.db import store_analysis, query

logger = logging.getLogger(__name__)


def profile_roster(team_id: str, season: int = None) -> Dict[str, Any]:
    """Build a complete roster composition profile for a team."""
    season = season or CURRENT_SEASON
    
    # Get roster
    players = query(
        "SELECT * FROM players WHERE team_id = ?", (team_id,)
    )
    
    if not players:
        return {}
    
    df = pd.DataFrame(players)
    profile = {}
    
    # ── Roster size ─────────────────────────────────────────────
    profile['total_players'] = len(df)
    
    # ── Age distribution ────────────────────────────────────────
    ages = df[df['age'].notna()]['age']
    if len(ages) > 0:
        profile['avg_age'] = round(float(ages.mean()), 1)
        profile['median_age'] = round(float(ages.median()), 1)
        profile['age_distribution'] = {
            'under_25': int((ages < 25).sum()),
            '25_to_29': int(((ages >= 25) & (ages < 30)).sum()),
            '30_plus': int((ages >= 30).sum()),
        }
    
    # ── Experience curve ────────────────────────────────────────
    exp = df[df['experience'].notna()]['experience']
    if len(exp) > 0:
        profile['avg_experience'] = round(float(exp.mean()), 1)
        profile['experience_distribution'] = {
            'years_1_3': int(((exp >= 1) & (exp <= 3)).sum()),
            'years_4_7': int(((exp >= 4) & (exp <= 7)).sum()),
            'years_8_plus': int((exp >= 8).sum()),
        }
    
    # ── Position group breakdown ────────────────────────────────
    position_breakdown = {}
    for group_name, positions in POSITION_GROUPS.items():
        group_players = df[df['position_group'] == group_name]
        if len(group_players) > 0:
            group_ages = group_players[group_players['age'].notna()]['age']
            position_breakdown[group_name] = {
                'count': len(group_players),
                'avg_age': round(float(group_ages.mean()), 1) if len(group_ages) > 0 else None,
                'avg_experience': round(float(
                    group_players[group_players['experience'].notna()]['experience'].mean()
                ), 1) if group_players['experience'].notna().any() else None,
            }
    profile['position_groups'] = position_breakdown
    
    # ── Draft capital ───────────────────────────────────────────
    drafted = df[df['draft_round'].notna()]
    if len(drafted) > 0:
        draft_capital = {}
        for group_name in POSITION_GROUPS:
            group = drafted[drafted['position_group'] == group_name]
            if len(group) > 0:
                draft_capital[group_name] = {
                    'players_drafted': len(group),
                    'avg_draft_round': round(float(group['draft_round'].mean()), 1),
                    'first_round_picks': int((group['draft_round'] == 1).sum()),
                    'high_picks': int((group['draft_round'] <= 3).sum()),
                }
        profile['draft_capital'] = draft_capital
    
    # ── Cap allocation ──────────────────────────────────────────
    contracts = query(
        "SELECT c.*, p.position_group FROM contracts c "
        "JOIN players p ON c.player_id = p.player_id "
        "WHERE c.team_id = ?",
        (team_id,)
    )
    
    if contracts:
        contract_df = pd.DataFrame(contracts)
        total_cap = contract_df['cap_hit_current'].sum()
        
        if total_cap > 0:
            cap_by_group = {}
            for group_name in POSITION_GROUPS:
                group = contract_df[contract_df['position_group'] == group_name]
                if len(group) > 0:
                    group_cap = group['cap_hit_current'].sum()
                    cap_by_group[group_name] = {
                        'total_cap': round(float(group_cap)),
                        'pct_of_cap': round(float(group_cap / total_cap * 100), 1),
                        'players': len(group),
                        'avg_cap_hit': round(float(group['cap_hit_current'].mean())),
                        'max_cap_hit': round(float(group['cap_hit_current'].max())),
                    }
            profile['cap_allocation'] = cap_by_group
            profile['total_cap_used'] = round(float(total_cap))
            
            # Top paid players
            top_paid = contract_df.nlargest(10, 'cap_hit_current')
            profile['top_contracts'] = []
            for _, p in top_paid.iterrows():
                # Look up player name
                player_info = query(
                    "SELECT name, position FROM players WHERE player_id = ?",
                    (p['player_id'],)
                )
                name = player_info[0]['name'] if player_info else 'Unknown'
                position = player_info[0]['position'] if player_info else ''
                
                profile['top_contracts'].append({
                    'player_id': p['player_id'],
                    'name': name,
                    'position': position,
                    'cap_hit': round(float(p['cap_hit_current'])),
                    'dead_cap': round(float(p['dead_cap'])),
                    'free_agent_year': int(p['free_agent_year']) if p['free_agent_year'] else None,
                })
    
    # ── Free agents ─────────────────────────────────────────────
    upcoming_fas = query(
        """SELECT c.player_id, c.free_agent_year, c.cap_hit_current,
                  p.name, p.position, p.position_group, p.age
           FROM contracts c
           JOIN players p ON c.player_id = p.player_id
           WHERE c.team_id = ? AND c.free_agent_year <= ?
           ORDER BY c.cap_hit_current DESC""",
        (team_id, season + 1)
    )
    
    if upcoming_fas:
        profile['upcoming_free_agents'] = [
            {
                'name': fa['name'],
                'position': fa['position'],
                'age': fa['age'],
                'cap_hit': round(float(fa['cap_hit_current'])),
                'free_agent_year': fa['free_agent_year'],
            }
            for fa in upcoming_fas[:15]
        ]
    
    return profile


def profile_all_rosters(season: int = None):
    """Profile all 32 team rosters and store results."""
    season = season or CURRENT_SEASON
    logger.info(f"Profiling all team rosters for {season}...")
    
    results = {}
    for team_id in TEAM_ABBRS:
        try:
            profile = profile_roster(team_id, season)
            if profile:
                results[team_id] = profile
                
                store_analysis(team_id, 'roster_profile', profile, season=season)
                logger.info(f"  {team_id}: {profile.get('total_players', 0)} players, "
                          f"avg_age={profile.get('avg_age', 'N/A')}")
        except Exception as e:
            logger.error(f"  {team_id}: Failed - {e}")
    
    logger.info(f"Profiled {len(results)} team rosters")
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    profile_all_rosters()
