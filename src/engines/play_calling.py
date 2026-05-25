"""
Engine A — Play-Calling Analysis.
Evaluates play-calling decisions, identifies predictability, and quantifies
points left on the table from suboptimal 4th down decisions.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS
from src.utils.db import store_analysis, query
from src.utils.epa import fourth_down_expected_points, letter_grade

logger = logging.getLogger(__name__)


def analyze_fourth_downs(team_id: str, season: int = None) -> Dict[str, Any]:
    """
    Analyze every 4th down decision for a team.
    Compares actual decision vs optimal decision based on expected points.
    """
    season = season or CURRENT_SEASON
    
    plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ? AND down = 4
        AND epa IS NOT NULL
    """, (team_id, season))
    
    if not plays:
        return {'decisions': [], 'summary': {}}
    
    df = pd.DataFrame(plays)
    
    decisions = []
    total_ep_left = 0
    correct = 0
    incorrect = 0
    
    for _, play in df.iterrows():
        yard_line = play.get('yardline_100', 50)
        ydstogo = play.get('ydstogo', 5)
        play_type = play.get('play_type', '')
        epa = play.get('epa', 0)
        
        if yard_line is None or ydstogo is None:
            continue
        
        # Calculate optimal decision
        ep_calc = fourth_down_expected_points(int(yard_line), int(ydstogo))
        recommended = ep_calc['recommended']
        
        # Determine actual decision
        if play.get('punt_attempt') == 1:
            actual = 'punt'
        elif play.get('field_goal_attempt') == 1:
            actual = 'field_goal'
        else:
            actual = 'go_for_it'
        
        # Calculate EP difference
        ep_actual = ep_calc.get(actual, 0) or 0
        ep_optimal = ep_calc.get(recommended, 0) or 0
        ep_diff = ep_optimal - ep_actual
        
        is_correct = actual == recommended
        
        # Late-game override: FG that ties/wins is always correct
        quarter = int(play.get('quarter', 0) or 0)
        time_remaining = int(play.get('game_seconds_remaining', 3600) or 3600)
        score_diff = int(play.get('score_differential', 0) or 0)
        
        if quarter >= 4 and time_remaining < 300 and actual == 'field_goal' and yard_line <= 40:
            score_after_fg = score_diff + 3
            if score_after_fg >= 0 and score_diff < 0:  # FG ties or takes the lead
                is_correct = True
                ep_diff = 0  # No EP left on table for correct late-game decisions
        
        if is_correct:
            correct += 1
        else:
            incorrect += 1
            total_ep_left += max(0, ep_diff)
        
        decision = {
            'game_id': play.get('game_id', ''),
            'week': int(play.get('week', 0)) if play.get('week') else 0,
            'quarter': int(play.get('quarter', 0)) if play.get('quarter') else 0,
            'yard_line': int(yard_line),
            'yards_to_go': int(ydstogo),
            'score_diff': int(play.get('score_differential', 0)) if play.get('score_differential') else 0,
            'actual_decision': actual,
            'recommended_decision': recommended,
            'correct': is_correct,
            'ep_actual': round(ep_actual, 2),
            'ep_optimal': round(ep_optimal, 2),
            'ep_left_on_table': round(max(0, ep_diff), 2),
            'actual_epa': round(float(epa) if epa else 0, 2),
            'result_yards': float(play.get('yards_gained', 0)),
            'converted': bool(play.get('fourth_down_converted')),
            'description': str(play.get('desc', ''))[:200],
        }
        decisions.append(decision)
    
    total_decisions = correct + incorrect
    
    summary = {
        'total_fourth_downs': total_decisions,
        'correct_decisions': correct,
        'incorrect_decisions': incorrect,
        'accuracy_pct': round(correct / total_decisions * 100, 1) if total_decisions > 0 else 0,
        'total_ep_left_on_table': round(total_ep_left, 1),
        'avg_ep_per_incorrect': round(total_ep_left / incorrect, 2) if incorrect > 0 else 0,
        'went_for_it_count': sum(1 for d in decisions if d['actual_decision'] == 'go_for_it'),
        'punted_count': sum(1 for d in decisions if d['actual_decision'] == 'punt'),
        'fg_count': sum(1 for d in decisions if d['actual_decision'] == 'field_goal'),
        'should_have_gone_for_it': sum(1 for d in decisions 
                                        if not d['correct'] and d['recommended_decision'] == 'go_for_it'),
    }
    
    return {
        'decisions': sorted(decisions, key=lambda x: x['ep_left_on_table'], reverse=True),
        'summary': summary,
    }


def analyze_tendencies(team_id: str, season: int = None) -> Dict[str, Any]:
    """
    Analyze play-calling tendencies for predictability.
    Identifies the most predictable situations.
    """
    season = season or CURRENT_SEASON
    
    plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ?
        AND play_type IN ('pass', 'run')
        AND down IS NOT NULL AND ydstogo IS NOT NULL
    """, (team_id, season))
    
    if not plays:
        return {}
    
    df = pd.DataFrame(plays)
    
    # ── Build tendency matrix (down × distance bucket) ──────────
    def distance_bucket(ydstogo):
        if ydstogo <= 2:
            return 'short (1-2)'
        elif ydstogo <= 5:
            return 'medium (3-5)'
        elif ydstogo <= 8:
            return 'long (6-8)'
        else:
            return 'very long (9+)'
    
    df['dist_bucket'] = df['ydstogo'].apply(distance_bucket)
    
    tendency_matrix = {}
    most_predictable = []
    
    # ── Calculate league-wide baseline pass rates per situation ──
    all_plays = query("""
        SELECT down, ydstogo, pass_or_run FROM play_by_play
        WHERE season = ? AND play_type IN ('pass', 'run')
        AND down IS NOT NULL AND ydstogo IS NOT NULL
    """, (season,))
    
    league_df = pd.DataFrame(all_plays) if all_plays else pd.DataFrame()
    if len(league_df) > 0:
        league_df['dist_bucket'] = league_df['ydstogo'].apply(distance_bucket)
    
    for down in [1, 2, 3]:
        for bucket in ['short (1-2)', 'medium (3-5)', 'long (6-8)', 'very long (9+)']:
            situation = df[(df['down'] == down) & (df['dist_bucket'] == bucket)]
            if len(situation) >= 5:
                pass_rate = len(situation[situation['pass_or_run'] == 'pass']) / len(situation)
                run_rate = 1 - pass_rate
                
                # Calculate league baseline for this situation
                league_baseline = 0.5  # fallback
                if len(league_df) > 0:
                    league_sit = league_df[(league_df['down'] == down) & (league_df['dist_bucket'] == bucket)]
                    if len(league_sit) >= 20:
                        league_baseline = len(league_sit[league_sit['pass_or_run'] == 'pass']) / len(league_sit)
                
                # Predictability = deviation from LEAGUE NORM, not 50/50
                predictability = min(1.0, abs(pass_rate - league_baseline) * 2.5)
                
                key = f"{down}_{bucket}"
                entry = {
                    'down': down,
                    'distance': bucket,
                    'plays': len(situation),
                    'pass_rate': round(pass_rate, 3),
                    'run_rate': round(run_rate, 3),
                    'predictability': round(predictability, 3),
                    'league_pass_rate': round(league_baseline, 3),
                    'pass_epa': round(float(situation[situation['pass_or_run'] == 'pass']['epa'].mean()), 3) if len(situation[situation['pass_or_run'] == 'pass']) > 0 else 0,
                    'run_epa': round(float(situation[situation['pass_or_run'] == 'run']['epa'].mean()), 3) if len(situation[situation['pass_or_run'] == 'run']) > 0 else 0,
                }
                tendency_matrix[key] = entry
                most_predictable.append(entry)
    
    # Sort by predictability
    most_predictable.sort(key=lambda x: x['predictability'], reverse=True)
    
    # Overall predictability score
    avg_predictability = np.mean([e['predictability'] for e in most_predictable]) if most_predictable else 0
    
    # ── Quarter-by-quarter tendencies ───────────────────────────
    quarter_tendencies = {}
    for qtr in [1, 2, 3, 4]:
        qtr_plays = df[df['quarter'] == qtr]
        if len(qtr_plays) > 0:
            quarter_tendencies[str(qtr)] = {
                'plays': len(qtr_plays),
                'pass_rate': round(len(qtr_plays[qtr_plays['pass_or_run'] == 'pass']) / len(qtr_plays), 3),
                'epa_per_play': round(float(qtr_plays['epa'].mean()), 3),
            }
    
    # ── Score differential tendencies ───────────────────────────
    score_tendencies = {}
    for label, condition in [
        ('trailing_big', df['score_differential'] < -14),
        ('trailing', (df['score_differential'] >= -14) & (df['score_differential'] < 0)),
        ('tied', df['score_differential'] == 0),
        ('leading', (df['score_differential'] > 0) & (df['score_differential'] <= 14)),
        ('leading_big', df['score_differential'] > 14),
    ]:
        subset = df[condition]
        if len(subset) > 0:
            score_tendencies[label] = {
                'plays': len(subset),
                'pass_rate': round(len(subset[subset['pass_or_run'] == 'pass']) / len(subset), 3),
                'epa_per_play': round(float(subset['epa'].mean()), 3),
            }
    
    # ── First half vs second half ───────────────────────────────
    first_half = df[df['quarter'].isin([1, 2])]
    second_half = df[df['quarter'].isin([3, 4])]
    
    half_comparison = {}
    if len(first_half) > 0:
        half_comparison['first_half'] = {
            'plays': len(first_half),
            'pass_rate': round(len(first_half[first_half['pass_or_run'] == 'pass']) / len(first_half), 3),
            'epa_per_play': round(float(first_half['epa'].mean()), 3),
        }
    if len(second_half) > 0:
        half_comparison['second_half'] = {
            'plays': len(second_half),
            'pass_rate': round(len(second_half[second_half['pass_or_run'] == 'pass']) / len(second_half), 3),
            'epa_per_play': round(float(second_half['epa'].mean()), 3),
        }
    
    return {
        'tendency_matrix': tendency_matrix,
        'most_predictable': most_predictable[:5],
        'avg_predictability': round(avg_predictability, 3),
        'quarter_tendencies': quarter_tendencies,
        'score_tendencies': score_tendencies,
        'half_comparison': half_comparison,
    }


def analyze_efficiency(team_id: str, season: int = None) -> Dict[str, Any]:
    """
    Map efficiency by personnel grouping and field zone.
    Identify mismatches between usage rate and EPA.
    """
    season = season or CURRENT_SEASON
    
    plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ?
        AND play_type IN ('pass', 'run')
        AND epa IS NOT NULL
    """, (team_id, season))
    
    if not plays:
        return {}
    
    df = pd.DataFrame(plays)
    total_plays = len(df)
    
    # ── Personnel efficiency ────────────────────────────────────
    personnel_eff = []
    if 'personnel_offense' in df.columns:
        for personnel, group in df.groupby('personnel_offense'):
            if personnel and len(group) >= 15:
                usage = len(group) / total_plays
                epa_pp = float(group['epa'].mean())
                
                personnel_eff.append({
                    'personnel': str(personnel),
                    'plays': len(group),
                    'usage_rate': round(usage, 3),
                    'epa_per_play': round(epa_pp, 3),
                    'success_rate': round(float((group['success'] == 1).mean()), 3),
                    'pass_rate': round(len(group[group['pass_or_run'] == 'pass']) / len(group), 3),
                    # Mismatch: high usage + low EPA or low usage + high EPA
                    'efficiency_mismatch': round(epa_pp - usage * 0.1, 3),  # Simplified mismatch score
                })
    
    personnel_eff.sort(key=lambda x: x['epa_per_play'], reverse=True)
    
    # ── Field zone efficiency ───────────────────────────────────
    field_zones = []
    zone_labels = [
        ('own_0_20', 0, 80),    # Own 0-20 (opponent's 80-100)
        ('own_20_40', 80, 60),   # Own 20-40
        ('midfield', 60, 40),    # Midfield
        ('opp_40_20', 40, 20),   # Opponent's 40-20
        ('red_zone', 20, 0),     # Red zone (opponent's 20-0)
    ]
    
    for label, yl_max, yl_min in zone_labels:
        zone = df[(df['yardline_100'] <= yl_max) & (df['yardline_100'] > yl_min)]
        if len(zone) > 0:
            field_zones.append({
                'zone': label,
                'plays': len(zone),
                'epa_per_play': round(float(zone['epa'].mean()), 3),
                'pass_rate': round(len(zone[zone['pass_or_run'] == 'pass']) / len(zone), 3),
                'success_rate': round(float((zone['success'] == 1).mean()), 3),
            })
    
    # ── Recommendations ─────────────────────────────────────────
    recommendations = []
    
    # Find underused efficient personnel
    for p in personnel_eff:
        if p['epa_per_play'] > 0.1 and p['usage_rate'] < 0.3:
            recommendations.append(
                f"Increase {p['personnel']} usage from {p['usage_rate']*100:.0f}% — "
                f"it produces {p['epa_per_play']} EPA/play (well above average)"
            )
        elif p['epa_per_play'] < -0.05 and p['usage_rate'] > 0.2:
            recommendations.append(
                f"Reduce {p['personnel']} usage from {p['usage_rate']*100:.0f}% — "
                f"it produces {p['epa_per_play']} EPA/play (below average)"
            )
    
    return {
        'personnel_efficiency': personnel_eff,
        'field_zone_efficiency': field_zones,
        'recommendations': recommendations[:5],
    }


def run_play_calling_engine(season: int = None):
    """Run complete play-calling analysis for all 32 teams."""
    season = season or CURRENT_SEASON
    logger.info(f"Running Play-Calling Analysis Engine for {season}...")
    
    for team_id in TEAM_ABBRS:
        try:
            fourth_down = analyze_fourth_downs(team_id, season)
            tendencies = analyze_tendencies(team_id, season)
            efficiency = analyze_efficiency(team_id, season)
            
            # Build recommendations
            recs = []
            
            # 4th down recommendations
            fd_summary = fourth_down.get('summary', {})
            if fd_summary.get('total_ep_left_on_table', 0) > 3:
                recs.append(
                    f"Left {fd_summary['total_ep_left_on_table']} expected points on the table "
                    f"from conservative 4th down decisions. "
                    f"Should have gone for it {fd_summary.get('should_have_gone_for_it', 0)} more times."
                )
            
            # Predictability recommendations
            if tendencies.get('avg_predictability', 0) > 0.4:
                top = tendencies.get('most_predictable', [{}])[0]
                recs.append(
                    f"Play-calling is highly predictable (score: {tendencies['avg_predictability']:.2f}). "
                    f"Most predictable: {top.get('down', '')}{'st' if top.get('down')==1 else 'nd' if top.get('down')==2 else 'rd'} "
                    f"and {top.get('distance', '')} — "
                    f"{'passing' if top.get('pass_rate', 0) > 0.5 else 'running'} "
                    f"{max(top.get('pass_rate', 0), top.get('run_rate', 0))*100:.0f}% of the time."
                )
            
            # Efficiency recommendations
            recs.extend(efficiency.get('recommendations', []))
            
            combined = {
                'fourth_down_analysis': fourth_down,
                'tendency_analysis': tendencies,
                'efficiency_analysis': efficiency,
                'recommendations': recs[:6],
            }
            
            # Composite score
            fd_accuracy = fd_summary.get('accuracy_pct', 50)
            predictability = (1 - tendencies.get('avg_predictability', 0.5)) * 100
            
            # Get offensive EPA for efficiency component
            off_plays = query(
                "SELECT AVG(epa) as avg_epa FROM play_by_play "
                "WHERE team_id = ? AND season = ? AND play_type IN ('pass','run') AND epa IS NOT NULL",
                (team_id, season)
            )
            epa_score = 50
            if off_plays and off_plays[0]['avg_epa']:
                epa_score = max(0, min(100, (off_plays[0]['avg_epa'] + 0.2) / 0.4 * 100))
            
            score = (fd_accuracy * 0.35 + predictability * 0.25 + epa_score * 0.40)
            grade = letter_grade(score)
            
            store_analysis(team_id, 'play_calling', combined,
                         grade=grade, score=round(score, 1), season=season)
            
            logger.info(f"  {team_id}: Grade={grade} (score={score:.1f}), "
                      f"4th down EP left={fd_summary.get('total_ep_left_on_table', 0):.1f}")
            
        except Exception as e:
            logger.error(f"  {team_id}: Failed - {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("Play-Calling Analysis Engine complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_play_calling_engine()
