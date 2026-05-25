"""
Engine B — Roster Value Analysis.
Calculates Value Over Replacement, cap efficiency, and generates roster move
recommendations for every team.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS, POSITION_GROUPS, REPLACEMENT_LEVEL_PERCENTILE
from src.utils.db import store_analysis, query
from src.utils.epa import letter_grade

logger = logging.getLogger(__name__)

SALARY_CAP = 272_600_000


def _calculate_replacement_levels(season: int) -> Dict[str, float]:
    """Calculate replacement-level EPA per play for each position group."""
    players = query("""
        SELECT ps.player_id, ps.total_epa, ps.epa_per_play,
               COALESCE(ps.attempts, 0) + COALESCE(ps.carries, 0) + COALESCE(ps.targets, 0) as touches,
               p.position_group, ps.games
        FROM player_season ps
        JOIN players p ON ps.player_id = p.player_id
        WHERE ps.season = ? AND (
            ps.attempts > 0 OR ps.carries > 0 OR ps.targets > 0
            OR (p.position_group IN ('DL', 'LB', 'DB') AND ps.games >= 4)
        )
    """, (season,))
    
    if not players:
        return {}
    
    df = pd.DataFrame(players)
    
    replacement = {}
    for group in df['position_group'].unique():
        group_data = df[df['position_group'] == group]
        if len(group_data) >= 3:
            if group in ('DL', 'LB', 'DB'):
                # For defensive players, compute EPA per estimated snap
                def_epa_rates = group_data.apply(
                    lambda r: r['total_epa'] / max(r.get('games', 1) * 40, 1), axis=1
                )
                replacement[group] = float(def_epa_rates.quantile(REPLACEMENT_LEVEL_PERCENTILE))
            else:
                replacement[group] = float(
                    group_data['epa_per_play'].quantile(REPLACEMENT_LEVEL_PERCENTILE)
                )
        else:
            replacement[group] = 0.0
    
    return replacement


def analyze_roster_value(team_id: str, season: int = None) -> Dict[str, Any]:
    """
    Calculate VOR and cap efficiency for every player on the roster.
    """
    season = season or CURRENT_SEASON
    
    # Get replacement levels
    replacement_levels = _calculate_replacement_levels(season)
    
    # Get player season stats with contracts
    players = query("""
        SELECT ps.*, p.name, p.position, p.position_group, p.age, p.experience,
               c.cap_hit_current, c.dead_cap, c.free_agent_year, c.guaranteed_remaining,
               c.total_value, c.avg_annual, c.contract_years
        FROM player_season ps
        JOIN players p ON ps.player_id = p.player_id
        LEFT JOIN contracts c ON ps.player_id = c.player_id
        WHERE ps.team_id = ? AND ps.season = ?
        ORDER BY ps.total_epa DESC
    """, (team_id, season))
    
    if not players:
        return {}
    
    df = pd.DataFrame(players).fillna(0)
    
    # Calculate VOR and cap efficiency for each player
    roster = []
    total_cap = df['cap_hit_current'].sum()
    
    for _, player in df.iterrows():
        pos_group = player.get('position_group', 'UNKNOWN')
        replacement_epa = replacement_levels.get(pos_group, 0)
        
        total_epa = float(player.get('total_epa', 0) or 0)
        touches = (int(player.get('attempts', 0) or 0) + 
                  int(player.get('carries', 0) or 0) + 
                  int(player.get('targets', 0) or 0))
        games = int(player.get('games', 0) or 0)
        
        # VOR calculation: defensive players use game-estimated snaps instead of touches
        if pos_group in ('DL', 'LB', 'DB') and touches == 0:
            # Estimate ~40 defensive snaps per game for starters
            estimated_volume = max(games * 40, 1)
            vor = total_epa - (replacement_epa * estimated_volume)
        elif touches > 0:
            vor = total_epa - (replacement_epa * touches)
        else:
            vor = 0
        
        cap_hit = float(player.get('cap_hit_current', 0) or 0)
        cap_pct = (cap_hit / SALARY_CAP * 100) if cap_hit > 0 else 0
        
        # Cap efficiency = VOR / cap%
        cap_efficiency = (vor / cap_pct) if cap_pct > 0.1 else 0
        
        roster.append({
            'player_id': player.get('player_id', ''),
            'name': player.get('name', ''),
            'position': player.get('position', ''),
            'position_group': pos_group,
            'age': int(player['age']) if player.get('age') else None,
            'experience': int(player['experience']) if player.get('experience') else None,
            'games': int(player.get('games', 0) or 0),
            'total_epa': round(total_epa, 2),
            'epa_per_play': round(float(player.get('epa_per_play', 0) or 0), 3),
            'touches': touches,
            'vor': round(vor, 2),
            'cap_hit': round(cap_hit),
            'cap_pct': round(cap_pct, 2),
            'dead_cap': round(float(player.get('dead_cap', 0) or 0)),
            'cap_efficiency': round(cap_efficiency, 2),
            'free_agent_year': int(player['free_agent_year']) if player.get('free_agent_year') else None,
            'guaranteed_remaining': round(float(player.get('guaranteed_remaining', 0) or 0)),
            # Key stats
            'passing_yards': round(float(player.get('passing_yards', 0) or 0)),
            'rushing_yards': round(float(player.get('rushing_yards', 0) or 0)),
            'receiving_yards': round(float(player.get('receiving_yards', 0) or 0)),
            'total_tds': int((player.get('passing_tds', 0) or 0) + 
                           (player.get('rushing_tds', 0) or 0) + 
                           (player.get('receiving_tds', 0) or 0)),
        })
    
    # Sort by VOR
    roster.sort(key=lambda x: x['vor'], reverse=True)
    
    # Identify overpaid and underpaid
    paid_players = [p for p in roster if p['cap_hit'] > 0]
    overpaid = sorted([p for p in paid_players if p['cap_efficiency'] < -1], 
                      key=lambda x: x['cap_efficiency'])[:5]
    underpaid = sorted([p for p in paid_players if p['cap_efficiency'] > 0], 
                       key=lambda x: x['cap_efficiency'], reverse=True)[:5]
    
    return {
        'roster': roster,
        'top_5_vor': roster[:5],
        'bottom_5_vor': roster[-5:] if len(roster) >= 5 else roster,
        'most_overpaid': overpaid,
        'most_underpaid': underpaid,
        'total_cap_used': round(total_cap),
        'cap_space': round(SALARY_CAP - total_cap),
    }


def generate_roster_recommendations(team_id: str, season: int = None) -> Dict[str, Any]:
    """Generate actionable roster move recommendations."""
    season = season or CURRENT_SEASON
    
    value_data = analyze_roster_value(team_id, season)
    if not value_data:
        return {}
    
    roster = value_data['roster']
    
    re_sign = []
    cut_candidates = []
    trade_candidates = []
    draft_needs = []
    
    for player in roster:
        fa_year = player.get('free_agent_year')
        vor = player.get('vor', 0)
        cap_hit = player.get('cap_hit', 0)
        dead_cap = player.get('dead_cap', 0)
        age = player.get('age') or 25
        cap_eff = player.get('cap_efficiency', 0)
        
        # ── Re-sign candidates ──────────────────────────────────
        if fa_year and fa_year <= season + 1 and vor > 0:
            re_sign.append({
                'name': player['name'],
                'position': player['position'],
                'age': age,
                'vor': vor,
                'cap_hit': cap_hit,
                'reason': f"VOR of {vor:.1f} with expiring contract. "
                         f"{'Young player with upside' if age < 27 else 'Proven veteran'}."
            })
        
        # ── Cut candidates ──────────────────────────────────────
        cap_savings = cap_hit - dead_cap
        if vor < 0 and cap_savings > 1_000_000 and cap_hit > 2_000_000:
            cut_candidates.append({
                'name': player['name'],
                'position': player['position'],
                'age': age,
                'vor': vor,
                'cap_hit': cap_hit,
                'dead_cap': dead_cap,
                'cap_savings': round(cap_savings),
                'reason': f"Below replacement-level production (VOR: {vor:.1f}) "
                         f"with ${cap_savings/1e6:.1f}M in potential savings."
            })
        
        # ── Trade candidates ────────────────────────────────────
        if vor > 2 and cap_eff > 1 and age < 30:
            # Check if position has depth
            same_pos = [p for p in roster if p['position'] == player['position'] 
                       and p['player_id'] != player['player_id'] and p['vor'] > 0]
            if len(same_pos) >= 1:
                trade_candidates.append({
                    'name': player['name'],
                    'position': player['position'],
                    'age': age,
                    'vor': vor,
                    'cap_hit': cap_hit,
                    'reason': f"High VOR ({vor:.1f}) on efficient deal. "
                             f"Team has depth at {player['position']}."
                })
    
    # ── Draft needs ─────────────────────────────────────────────
    position_vor = {}
    for player in roster:
        pg = player.get('position_group', 'UNKNOWN')
        if pg not in position_vor:
            position_vor[pg] = []
        position_vor[pg].append({
            'name': player['name'],
            'vor': player['vor'],
            'age': player.get('age') or 25,
            'cap_hit': player['cap_hit'],
        })
    
    for pg, players_list in position_vor.items():
        if pg in ('K', 'P', 'LS', 'UNKNOWN'):
            continue
        
        avg_vor = np.mean([p['vor'] for p in players_list])
        avg_age = np.mean([p['age'] for p in players_list])
        
        if avg_vor < 0 or avg_age > 29:
            reason_parts = []
            if avg_vor < 0:
                reason_parts.append(f"below-replacement production (avg VOR: {avg_vor:.1f})")
            if avg_age > 29:
                reason_parts.append(f"aging group (avg age: {avg_age:.1f})")
            
            draft_needs.append({
                'position_group': pg,
                'avg_vor': round(avg_vor, 1),
                'avg_age': round(avg_age, 1),
                'players': len(players_list),
                'reason': f"Need {pg}: {', '.join(reason_parts)}.",
                'priority': 'HIGH' if avg_vor < -1 else 'MEDIUM',
            })
    
    draft_needs.sort(key=lambda x: x['avg_vor'])
    
    # ── Cap projection ──────────────────────────────────────────
    total_cap = value_data['total_cap_used']
    
    cap_projection = {
        'current_cap_used': total_cap,
        'current_cap_space': SALARY_CAP - total_cap,
        'if_cut_all_recommended': total_cap - sum(c['cap_savings'] for c in cut_candidates),
        'cut_savings': sum(c['cap_savings'] for c in cut_candidates),
        'dead_cap_from_cuts': sum(c['dead_cap'] for c in cut_candidates),
    }
    
    return {
        're_sign_candidates': sorted(re_sign, key=lambda x: x['vor'], reverse=True)[:8],
        'cut_candidates': sorted(cut_candidates, key=lambda x: x['cap_savings'], reverse=True)[:8],
        'trade_candidates': trade_candidates[:5],
        'draft_needs': draft_needs[:5],
        'cap_projection': cap_projection,
    }


def run_roster_value_engine(season: int = None):
    """Run complete roster value analysis for all 32 teams."""
    season = season or CURRENT_SEASON
    logger.info(f"Running Roster Value Analysis Engine for {season}...")
    
    for team_id in TEAM_ABBRS:
        try:
            value_data = analyze_roster_value(team_id, season)
            recommendations = generate_roster_recommendations(team_id, season)
            
            combined = {
                'value_analysis': value_data,
                'recommendations': recommendations,
            }
            
            # Composite score based on overall roster efficiency
            if value_data and value_data.get('roster'):
                avg_cap_eff = np.mean([p['cap_efficiency'] for p in value_data['roster'] 
                                       if p['cap_hit'] > 500_000])
                avg_vor = np.mean([p['vor'] for p in value_data['roster']])
                
                # Normalize to 0-100
                score = max(0, min(100, (avg_cap_eff + 2) / 4 * 50 + (avg_vor + 5) / 10 * 50))
            else:
                score = 50
            
            grade = letter_grade(score)
            
            store_analysis(team_id, 'roster_value', combined,
                         grade=grade, score=round(score, 1), season=season)
            
            n_overpaid = len(value_data.get('most_overpaid', []))
            n_resign = len(recommendations.get('re_sign_candidates', []))
            logger.info(f"  {team_id}: Grade={grade} (score={score:.1f}), "
                      f"overpaid={n_overpaid}, re-sign={n_resign}")
            
        except Exception as e:
            logger.error(f"  {team_id}: Failed - {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("Roster Value Analysis Engine complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_roster_value_engine()
