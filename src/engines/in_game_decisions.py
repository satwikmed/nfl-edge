"""
Engine C — In-Game Decision Analysis.
Grades teams on win probability management, two-point conversions,
timeout usage, and clutch performance.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS
from src.utils.db import store_analysis, query
from src.utils.epa import letter_grade

logger = logging.getLogger(__name__)


def analyze_win_probability(team_id: str, season: int = None) -> Dict[str, Any]:
    """Track WP swings and identify the biggest decision moments."""
    season = season or CURRENT_SEASON
    
    plays = query("""
        SELECT game_id, play_id, week, quarter, down, ydstogo, yardline_100,
               play_type, pass_or_run, yards_gained, epa, wp, wpa, 
               score_differential, desc, touchdown, interception, fumble
        FROM play_by_play
        WHERE team_id = ? AND season = ?
        AND wp IS NOT NULL AND wpa IS NOT NULL
        ORDER BY game_id, play_id
    """, (team_id, season))
    
    if not plays:
        return {}
    
    df = pd.DataFrame(plays)
    
    # ── Biggest WP swings ───────────────────────────────────────
    df['abs_wpa'] = df['wpa'].abs()
    top_positive = df.nlargest(10, 'wpa')
    top_negative = df.nsmallest(10, 'wpa')
    
    biggest_positive = []
    for _, play in top_positive.iterrows():
        biggest_positive.append({
            'game_id': play['game_id'],
            'week': int(play['week']) if play['week'] else 0,
            'quarter': int(play['quarter']) if play['quarter'] else 0,
            'wpa': round(float(play['wpa']), 3),
            'wp_after': round(float(play['wp']) + float(play['wpa']), 3),
            'description': str(play.get('desc', ''))[:200],
            'play_type': play.get('play_type', ''),
            'yards': float(play.get('yards_gained', 0)),
        })
    
    biggest_negative = []
    for _, play in top_negative.iterrows():
        biggest_negative.append({
            'game_id': play['game_id'],
            'week': int(play['week']) if play['week'] else 0,
            'quarter': int(play['quarter']) if play['quarter'] else 0,
            'wpa': round(float(play['wpa']), 3),
            'wp_after': round(float(play['wp']) + float(play['wpa']), 3),
            'description': str(play.get('desc', ''))[:200],
            'play_type': play.get('play_type', ''),
            'yards': float(play.get('yards_gained', 0)),
        })
    
    # ── Game-level WP trends ────────────────────────────────────
    game_summaries = []
    for game_id, game_df in df.groupby('game_id'):
        total_wpa = game_df['wpa'].sum()
        max_wp = game_df['wp'].max()
        min_wp = game_df['wp'].min()
        
        game_summaries.append({
            'game_id': str(game_id),
            'week': int(game_df.iloc[0]['week']) if game_df.iloc[0]['week'] else 0,
            'total_wpa': round(float(total_wpa), 3),
            'max_wp': round(float(max_wp), 3),
            'min_wp': round(float(min_wp), 3),
            'wp_volatility': round(float(max_wp - min_wp), 3),
            'plays': len(game_df),
        })
    
    game_summaries.sort(key=lambda x: abs(x['total_wpa']), reverse=True)
    
    return {
        'biggest_positive_plays': biggest_positive,
        'biggest_negative_plays': biggest_negative,
        'game_summaries': game_summaries,
        'season_total_wpa': round(float(df['wpa'].sum()), 3),
        'avg_wpa_per_play': round(float(df['wpa'].mean()), 4),
    }


def analyze_two_point_conversions(team_id: str, season: int = None) -> Dict[str, Any]:
    """Grade two-point conversion decisions."""
    season = season or CURRENT_SEASON
    
    plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ? AND two_point_attempt = 1
    """, (team_id, season))
    
    # Also get extra point attempts for comparison
    xp_plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ? AND extra_point_attempt = 1
    """, (team_id, season))
    
    attempts = []
    correct_decisions = 0
    incorrect_decisions = 0
    
    if plays:
        df = pd.DataFrame(plays)
        
        for _, play in df.iterrows():
            score_diff = int(play.get('score_differential', 0) or 0)
            quarter = int(play.get('quarter', 0) or 0)
            time_left = int(play.get('game_seconds_remaining', 3600) or 3600)
            
            # Simplified 2-point decision chart:
            # Should go for 2 when: trailing by 2, 5, 8, 11, 14 (specific score states)
            # Or when trailing in 4th quarter
            score_after_td = score_diff + 6  # Score differential after TD but before XP/2pt
            
            should_go_for_two = False
            if quarter >= 4 and time_left < 600:  # Late game
                # Down by 2 after TD = tied, go for 2 to lead
                if score_after_td in [0, -2, -5]:
                    should_go_for_two = True
            # Standard 2-pt situations
            if score_after_td in [-2, -5, -8, -11]:
                should_go_for_two = True
            
            was_correct = True  # They went for 2 — was it right?
            if not should_go_for_two and quarter < 4:
                was_correct = False
            
            if was_correct:
                correct_decisions += 1
            else:
                incorrect_decisions += 1
            
            result = str(play.get('two_point_conv_result', ''))
            
            attempts.append({
                'game_id': play.get('game_id', ''),
                'week': int(play.get('week', 0) or 0),
                'quarter': quarter,
                'score_diff_at_decision': score_diff,
                'time_remaining': time_left,
                'result': result,
                'successful': result.lower() in ['success', 'made', '1'],
                'was_correct_decision': was_correct,
                'description': str(play.get('desc', ''))[:200],
            })
    
    # Check for missed 2-point opportunities (kicked XP when should have gone for 2)
    missed_opportunities = 0
    if xp_plays:
        xp_df = pd.DataFrame(xp_plays)
        for _, play in xp_df.iterrows():
            score_diff = int(play.get('score_differential', 0) or 0)
            quarter = int(play.get('quarter', 0) or 0)
            time_left = int(play.get('game_seconds_remaining', 3600) or 3600)
            score_after_td = score_diff + 6
            
            if quarter >= 4 and time_left < 600 and score_after_td in [0, -2, -5]:
                missed_opportunities += 1
            elif score_after_td in [-2, -5, -8]:
                missed_opportunities += 1
    
    total = correct_decisions + incorrect_decisions
    
    return {
        'attempts': attempts,
        'total_attempts': len(attempts),
        'successful_conversions': sum(1 for a in attempts if a['successful']),
        'correct_decisions': correct_decisions,
        'incorrect_decisions': incorrect_decisions,
        'decision_accuracy': round(correct_decisions / total * 100, 1) if total > 0 else 100,
        'missed_opportunities': missed_opportunities,
        'conversion_rate': round(
            sum(1 for a in attempts if a['successful']) / len(attempts) * 100, 1
        ) if attempts else 0,
    }


def analyze_timeout_usage(team_id: str, season: int = None) -> Dict[str, Any]:
    """Grade timeout usage efficiency."""
    season = season or CURRENT_SEASON
    
    plays = query("""
        SELECT * FROM play_by_play
        WHERE season = ? AND timeout = 1 AND timeout_team = ?
    """, (season, team_id))
    
    if not plays:
        # Try with different team format
        plays = query("""
            SELECT * FROM play_by_play
            WHERE season = ? AND timeout = 1
        """, (season,))
        if plays:
            # Filter to this team's timeouts
            plays = [p for p in plays if p.get('timeout_team') == team_id]
    
    if not plays:
        return {
            'total_timeouts': 0,
            'timeouts_by_quarter': {},
            'wasted_timeouts': 0,
            'grade': 'N/A',
        }
    
    df = pd.DataFrame(plays)
    
    # Categorize timeouts
    total = len(df)
    by_quarter = {}
    wasted = 0
    strategic = 0
    
    for _, play in df.iterrows():
        qtr = str(int(play.get('quarter', 0) or 0))
        by_quarter[qtr] = by_quarter.get(qtr, 0) + 1
        
        time_left = int(play.get('game_seconds_remaining', 0) or 0)
        score_diff = int(play.get('score_differential', 0) or 0)
        
        # Wasted timeout: 1st/2nd quarter with comfortable lead
        if int(qtr) <= 2 and score_diff > 14:
            wasted += 1
        # Strategic: 4th quarter, close game, stopping clock
        elif int(qtr) == 4 and abs(score_diff) <= 8:
            strategic += 1
        # Late game timeout management
        elif int(qtr) >= 3 and time_left < 300:
            strategic += 1
    
    # Grade calculation
    waste_rate = wasted / total if total > 0 else 0
    if waste_rate <= 0.1:
        grade = 'A'
    elif waste_rate <= 0.2:
        grade = 'B'
    elif waste_rate <= 0.3:
        grade = 'C'
    elif waste_rate <= 0.4:
        grade = 'D'
    else:
        grade = 'F'
    
    return {
        'total_timeouts': total,
        'timeouts_by_quarter': by_quarter,
        'wasted_timeouts': wasted,
        'strategic_timeouts': strategic,
        'waste_rate': round(waste_rate, 3),
        'grade': grade,
    }


def analyze_clutch_performance(team_id: str, season: int = None) -> Dict[str, Any]:
    """Analyze performance in high-leverage situations."""
    season = season or CURRENT_SEASON
    
    # High leverage: 4th quarter, score within 7
    clutch_plays = query("""
        SELECT * FROM play_by_play
        WHERE team_id = ? AND season = ?
        AND quarter = 4 AND ABS(score_differential) <= 7
        AND play_type IN ('pass', 'run')
        AND epa IS NOT NULL
    """, (team_id, season))
    
    # Overall plays for comparison
    overall = query("""
        SELECT AVG(epa) as avg_epa, 
               AVG(CASE WHEN success = 1 THEN 1.0 ELSE 0.0 END) as success_rate
        FROM play_by_play
        WHERE team_id = ? AND season = ?
        AND play_type IN ('pass', 'run')
        AND epa IS NOT NULL
    """, (team_id, season))
    
    overall_epa = overall[0]['avg_epa'] if overall else 0
    overall_sr = overall[0]['success_rate'] if overall else 0
    
    if not clutch_plays:
        return {
            'clutch_plays': 0,
            'clutch_epa': 0,
            'overall_epa': round(float(overall_epa or 0), 3),
            'clutch_differential': 0,
        }
    
    df = pd.DataFrame(clutch_plays)
    
    clutch_epa = float(df['epa'].mean())
    clutch_sr = float((df['success'] == 1).mean())
    
    return {
        'clutch_plays': len(df),
        'clutch_epa': round(clutch_epa, 3),
        'clutch_success_rate': round(clutch_sr, 3),
        'overall_epa': round(float(overall_epa or 0), 3),
        'overall_success_rate': round(float(overall_sr or 0), 3),
        'clutch_differential': round(clutch_epa - float(overall_epa or 0), 3),
        'clutch_sr_differential': round(clutch_sr - float(overall_sr or 0), 3),
        'performs_better_under_pressure': clutch_epa > float(overall_epa or 0),
        'clutch_pass_rate': round(len(df[df['pass_or_run'] == 'pass']) / len(df), 3),
        'clutch_touchdowns': int(df['touchdown'].sum()),
        'clutch_turnovers': int(df['interception'].sum() + df['fumble'].sum()),
    }


def run_in_game_decisions_engine(season: int = None):
    """Run complete in-game decision analysis for all 32 teams."""
    season = season or CURRENT_SEASON
    logger.info(f"Running In-Game Decisions Analysis Engine for {season}...")
    
    for team_id in TEAM_ABBRS:
        try:
            wp_analysis = analyze_win_probability(team_id, season)
            two_pt = analyze_two_point_conversions(team_id, season)
            timeouts = analyze_timeout_usage(team_id, season)
            clutch = analyze_clutch_performance(team_id, season)
            
            # Build recommendations
            recommendations = []
            
            # Timeout recommendations
            if timeouts.get('wasted_timeouts', 0) > 3:
                recommendations.append(
                    f"Wasted {timeouts['wasted_timeouts']} timeouts this season on avoidable situations. "
                    f"Focus on pre-snap discipline to preserve timeouts for critical moments."
                )
            
            # Two-point recommendations
            if two_pt.get('missed_opportunities', 0) > 0:
                recommendations.append(
                    f"Missed {two_pt['missed_opportunities']} opportunities to go for two "
                    f"when the analytics chart recommended it."
                )
            if two_pt.get('incorrect_decisions', 0) > 0:
                recommendations.append(
                    f"Made {two_pt['incorrect_decisions']} incorrect two-point conversion decisions."
                )
            
            # Clutch performance
            if clutch.get('clutch_differential', 0) < -0.05:
                recommendations.append(
                    f"Performs worse under pressure: {clutch['clutch_differential']:.3f} EPA differential "
                    f"in 4th quarter close games vs overall. Consider situational practice emphasis."
                )
            
            combined = {
                'win_probability_analysis': wp_analysis,
                'two_point_analysis': two_pt,
                'timeout_analysis': timeouts,
                'clutch_performance': clutch,
                'recommendations': recommendations,
            }
            
            # Composite score
            timeout_score = {'A': 95, 'B': 80, 'C': 65, 'D': 50, 'F': 30, 'N/A': 70}
            to_score = timeout_score.get(timeouts.get('grade', 'C'), 65)
            
            two_pt_score = min(100, two_pt.get('decision_accuracy', 70))
            
            clutch_diff = clutch.get('clutch_differential', 0)
            clutch_score = max(0, min(100, (clutch_diff + 0.1) / 0.2 * 100))
            
            wp_score = max(0, min(100, 
                (wp_analysis.get('avg_wpa_per_play', 0) + 0.01) / 0.02 * 100
            )) if wp_analysis else 50
            
            score = (to_score * 0.25 + two_pt_score * 0.20 + 
                    clutch_score * 0.30 + wp_score * 0.25)
            grade = letter_grade(score)
            
            # Estimate wins impact
            wpa_total = wp_analysis.get('season_total_wpa', 0)
            estimated_wins_impact = round(wpa_total, 1)
            combined['estimated_wins_impact'] = estimated_wins_impact
            
            store_analysis(team_id, 'in_game_decisions', combined,
                         grade=grade, score=round(score, 1), season=season)
            
            logger.info(f"  {team_id}: Grade={grade} (score={score:.1f}), "
                      f"TO grade={timeouts.get('grade', 'N/A')}, "
                      f"clutch_diff={clutch.get('clutch_differential', 0):.3f}")
            
        except Exception as e:
            logger.error(f"  {team_id}: Failed - {e}")
            import traceback
            traceback.print_exc()
    
    logger.info("In-Game Decisions Analysis Engine complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_in_game_decisions_engine()
