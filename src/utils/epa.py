"""
EPA (Expected Points Added) utility functions.
Common calculations used across all analysis engines.
"""

import numpy as np
import pandas as pd
from typing import Optional


def calculate_success_rate(epa_series: pd.Series) -> float:
    """Calculate play success rate (% of plays with positive EPA)."""
    if len(epa_series) == 0:
        return 0.0
    return (epa_series > 0).mean()


def calculate_explosive_rate(yards_series: pd.Series, threshold: int = 20) -> float:
    """Calculate explosive play rate (% of plays with 20+ yards gained)."""
    if len(yards_series) == 0:
        return 0.0
    return (yards_series >= threshold).mean()


def epa_per_play(epa_series: pd.Series) -> float:
    """Calculate EPA per play."""
    if len(epa_series) == 0:
        return 0.0
    return epa_series.mean()


def weighted_epa(epa_series: pd.Series, weights: pd.Series) -> float:
    """Calculate weighted EPA."""
    if len(epa_series) == 0:
        return 0.0
    return np.average(epa_series, weights=weights)


def calculate_vor(player_epa: float, replacement_epa: float, snaps: int) -> float:
    """
    Calculate Value Over Replacement.
    
    Args:
        player_epa: Player's total EPA
        replacement_epa: Replacement-level EPA per snap
        snaps: Player's snap count
    
    Returns:
        VOR (EPA above replacement for given snaps)
    """
    replacement_total = replacement_epa * snaps
    return player_epa - replacement_total


def cap_efficiency_score(vor: float, cap_hit_pct: float) -> float:
    """
    Calculate cap efficiency score.
    
    Args:
        vor: Value Over Replacement
        cap_hit_pct: Player's cap hit as percentage of total team cap
    
    Returns:
        Cap efficiency score (higher is more efficient)
    """
    if cap_hit_pct <= 0:
        return 0.0
    return vor / cap_hit_pct


def letter_grade(score: float, thresholds: Optional[dict] = None) -> str:
    """
    Convert a numeric score to a letter grade.
    
    Args:
        score: Numeric score (0-100)
        thresholds: Optional custom thresholds dict
    
    Returns:
        Letter grade A+ through F
    """
    if thresholds is None:
        thresholds = {
            97: "A+", 93: "A", 90: "A-",
            87: "B+", 83: "B", 80: "B-",
            77: "C+", 73: "C", 70: "C-",
            67: "D+", 63: "D", 60: "D-",
        }
    
    for threshold, grade in sorted(thresholds.items(), reverse=True):
        if score >= threshold:
            return grade
    return "F"


def percentile_rank(value: float, distribution: pd.Series) -> float:
    """Calculate percentile rank of a value within a distribution."""
    if len(distribution) == 0:
        return 50.0
    return (distribution < value).mean() * 100


def fourth_down_expected_points(
    yard_line: int,
    yards_to_go: int,
    go_for_it_conversion_rate: float = None,
    fg_make_rate: float = None,
) -> dict:
    """
    Estimate expected points for 4th down decisions.
    
    Uses simplified EPA model. The actual values come from nflverse data,
    but this provides the decision framework.
    
    Args:
        yard_line: Yards from opponent's end zone (1-99)
        yards_to_go: Yards needed for first down
        go_for_it_conversion_rate: Override conversion probability
        fg_make_rate: Override field goal probability
    
    Returns:
        Dict with expected points for each decision
    """
    # Default conversion rates based on historical NFL data
    if go_for_it_conversion_rate is None:
        # Base conversion rate varies by distance
        base_rates = {1: 0.70, 2: 0.55, 3: 0.47, 4: 0.40, 5: 0.35}
        go_for_it_conversion_rate = base_rates.get(
            min(yards_to_go, 5), 0.30
        )
    
    if fg_make_rate is None:
        # FG make rate by distance (yard_line + 17 for snap/hold)
        fg_distance = yard_line + 17
        if fg_distance <= 30:
            fg_make_rate = 0.90
        elif fg_distance <= 40:
            fg_make_rate = 0.82
        elif fg_distance <= 50:
            fg_make_rate = 0.72
        elif fg_distance <= 55:
            fg_make_rate = 0.60
        else:
            fg_make_rate = 0.40
    
    # Simplified EP values by field position
    # Positive = offense favored, negative = defense favored
    def ep_at_yard_line(yl):
        """Approximate expected points at a yard line (yards from opponent end zone)."""
        if yl <= 0:
            return 6.96  # Touchdown
        elif yl <= 10:
            return 4.0
        elif yl <= 20:
            return 3.0
        elif yl <= 30:
            return 2.2
        elif yl <= 40:
            return 1.5
        elif yl <= 50:
            return 0.9
        elif yl <= 60:
            return 0.4
        elif yl <= 70:
            return 0.0
        elif yl <= 80:
            return -0.4
        elif yl <= 90:
            return -0.8
        else:
            return -1.2
    
    # EP if converting (new first down at current spot minus yards_to_go)
    new_yl = max(yard_line - yards_to_go, 0)
    ep_convert = ep_at_yard_line(new_yl)
    
    # EP if failing (opponent gets ball at current spot)
    ep_fail = -ep_at_yard_line(100 - yard_line)
    
    # EP of going for it
    ep_go = (go_for_it_conversion_rate * ep_convert +
             (1 - go_for_it_conversion_rate) * ep_fail)
    
    # EP of field goal attempt
    ep_fg = (fg_make_rate * 3.0 +
             (1 - fg_make_rate) * -ep_at_yard_line(100 - (yard_line + 7)))
    
    # EP of punt (assume ~42 yard net punt)
    punt_yl = min(yard_line + 42, 95)  # Pin inside 5 rarely
    ep_punt = -ep_at_yard_line(100 - punt_yl)
    
    return {
        "go_for_it": round(ep_go, 3),
        "field_goal": round(ep_fg, 3) if yard_line <= 55 else None,
        "punt": round(ep_punt, 3),
        "recommended": max(
            [("go_for_it", ep_go), 
             ("field_goal", ep_fg if yard_line <= 55 else -999),
             ("punt", ep_punt)],
            key=lambda x: x[1]
        )[0],
        "conversion_rate": go_for_it_conversion_rate,
        "fg_make_rate": fg_make_rate if yard_line <= 55 else None,
    }
