"""
Export analysis data as JSON files for the Next.js frontend.
Generates static data that the dashboard reads at build time.
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils.config import CURRENT_SEASON, TEAM_ABBRS, TEAM_BY_ABBR, DASHBOARD_DATA_DIR
from src.utils.db import query, get_analysis
from src.utils.epa import letter_grade

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


def export_all():
    """Export all analysis data as static JSON files for the dashboard."""
    logger.info("Exporting analysis data for dashboard...")
    
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # ── Export individual team data ─────────────────────────────
    teams_summary = []
    
    for team_id in TEAM_ABBRS:
        team_meta = TEAM_BY_ABBR.get(team_id, {})
        
        # Get team record
        team_db = query("SELECT * FROM teams WHERE team_id = ?", (team_id,))
        team_record = team_db[0] if team_db else {}
        
        # Get all analysis for this team
        analyses = {}
        for atype in ['offensive_profile', 'defensive_profile', 'roster_profile',
                       'play_calling', 'roster_value', 'in_game_decisions']:
            result = get_analysis(team_id, atype)
            if result:
                analyses[atype] = result
        
        # Calculate composite grade
        scores = []
        grades = {}
        for atype in ['play_calling', 'roster_value', 'in_game_decisions']:
            result = analyses.get(atype)
            if result and result.get('score'):
                scores.append(result['score'])
                grades[atype] = result.get('grade', 'N/A')
        
        composite_score = sum(scores) / len(scores) if scores else 50
        composite_grade = letter_grade(composite_score)
        
        team_data = {
            'id': team_id,
            'name': team_meta.get('name', ''),
            'city': team_meta.get('city', ''),
            'state': team_meta.get('state', ''),
            'abbreviation': team_id,
            'conference': team_meta.get('conference', ''),
            'division': team_meta.get('division', ''),
            'latitude': team_meta.get('lat', 0),
            'longitude': team_meta.get('lng', 0),
            'stadium': team_meta.get('stadium', ''),
            'wins': team_record.get('wins', 0),
            'losses': team_record.get('losses', 0),
            'ties': team_record.get('ties', 0),
            'composite_grade': composite_grade,
            'composite_score': round(composite_score, 1),
            'grades': {
                'play_calling': grades.get('play_calling', 'N/A'),
                'roster_value': grades.get('roster_value', 'N/A'),
                'in_game_decisions': grades.get('in_game_decisions', 'N/A'),
            },
            'scores': {
                atype: analyses.get(atype, {}).get('score', 0)
                for atype in ['play_calling', 'roster_value', 'in_game_decisions']
            },
            'offensive_profile': analyses.get('offensive_profile', {}).get('data', {}),
            'defensive_profile': analyses.get('defensive_profile', {}).get('data', {}),
            'roster_profile': analyses.get('roster_profile', {}).get('data', {}),
            'play_calling': analyses.get('play_calling', {}).get('data', {}),
            'roster_value': analyses.get('roster_value', {}).get('data', {}),
            'in_game_decisions': analyses.get('in_game_decisions', {}).get('data', {}),
        }
        
        # Save individual team file
        team_file = DASHBOARD_DATA_DIR / f"team_{team_id.lower()}.json"
        with open(team_file, 'w') as f:
            json.dump(team_data, f, indent=2, default=str)
        
        # Add to summary
        teams_summary.append({
            'id': team_id,
            'name': team_meta.get('name', ''),
            'abbreviation': team_id,
            'city': team_meta.get('city', ''),
            'state': team_meta.get('state', ''),
            'conference': team_meta.get('conference', ''),
            'division': team_meta.get('division', ''),
            'latitude': team_meta.get('lat', 0),
            'longitude': team_meta.get('lng', 0),
            'wins': team_record.get('wins', 0),
            'losses': team_record.get('losses', 0),
            'ties': team_record.get('ties', 0),
            'composite_grade': composite_grade,
            'composite_score': round(composite_score, 1),
            'grades': team_data['grades'],
            'scores': team_data['scores'],
            'offensive_epa': analyses.get('offensive_profile', {}).get('data', {}).get('epa_per_play', 0),
            'defensive_epa': analyses.get('defensive_profile', {}).get('data', {}).get('epa_per_play_allowed', 0),
        })
        
        logger.info(f"  {team_id}: {composite_grade} ({composite_score:.1f})")
    
    # Sort by composite score for rankings
    teams_summary.sort(key=lambda x: x['composite_score'], reverse=True)
    
    # Add rank
    for i, team in enumerate(teams_summary):
        team['rank'] = i + 1
    
    # Save teams summary
    summary_file = DASHBOARD_DATA_DIR / "teams_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(teams_summary, f, indent=2, default=str)
    
    logger.info(f"\nExported data for {len(teams_summary)} teams to {DASHBOARD_DATA_DIR}")
    logger.info(f"Top 5: {', '.join(t['abbreviation'] for t in teams_summary[:5])}")
    logger.info(f"Bottom 5: {', '.join(t['abbreviation'] for t in teams_summary[-5:])}")
    
    return teams_summary


if __name__ == "__main__":
    export_all()
