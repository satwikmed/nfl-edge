"""
Player stats ingestion from nflverse via nfl_data_py.
Pulls roster data, snap counts, and builds player stats from PBP data.
"""

import logging
import nfl_data_py as nfl
import pandas as pd
import numpy as np

from src.utils.config import CURRENT_SEASON, get_position_group
from src.utils.db import get_connection, init_db

logger = logging.getLogger(__name__)


def ingest_rosters(season: int = None):
    """Ingest player roster data using import_seasonal_rosters."""
    season = season or CURRENT_SEASON
    logger.info(f"Ingesting roster data for {season}...")
    
    try:
        rosters = nfl.import_seasonal_rosters([season])
    except Exception as e:
        logger.error(f"Failed to fetch roster data: {e}")
        raise
    
    if rosters is None or len(rosters) == 0:
        logger.warning(f"No roster data for {season}")
        return 0
    
    logger.info(f"Fetched {len(rosters)} roster entries")
    
    # Deduplicate — keep latest entry per player
    if 'week' in rosters.columns:
        rosters = rosters.sort_values('week', ascending=False).drop_duplicates(
            subset=['player_id'], keep='first'
        )
    else:
        rosters = rosters.drop_duplicates(subset=['player_id'], keep='first')
    
    rows = []
    for _, player in rosters.iterrows():
        pid = player.get('player_id', '')
        if not pid or pd.isna(pid):
            continue
        
        position = player.get('position', '')
        if pd.isna(position):
            position = ''
        
        # Get age directly from data, or calculate from birth_date
        age = None
        if 'age' in player and pd.notna(player.get('age')):
            age = int(player['age'])
        elif 'birth_date' in player and pd.notna(player.get('birth_date')):
            try:
                birth = pd.to_datetime(player['birth_date'])
                age = int((pd.Timestamp.now() - birth).days / 365.25)
            except Exception:
                pass
        
        # Calculate experience
        experience = None
        if 'years_exp' in player and pd.notna(player.get('years_exp')):
            experience = int(player['years_exp'])
        else:
            draft_year = player.get('rookie_year') or player.get('entry_year')
            if draft_year and pd.notna(draft_year):
                experience = season - int(draft_year) + 1
        
        # Handle team abbreviation — nflverse uses 'LA' for Rams
        team = player.get('team', '')
        if pd.isna(team):
            team = ''
        if team == 'LA':
            team = 'LAR'
        
        # Draft info
        draft_number = player.get('draft_number')
        draft_round = None
        draft_pick = None
        if pd.notna(draft_number):
            draft_pick = int(draft_number)
            draft_round = (int(draft_number) - 1) // 32 + 1
        
        rows.append({
            'player_id': str(pid),
            'name': player.get('player_name', ''),
            'team_id': team,
            'position': position,
            'position_group': get_position_group(position),
            'age': age,
            'experience': experience,
            'height': str(player.get('height', '')) if pd.notna(player.get('height')) else None,
            'weight': int(player.get('weight', 0)) if pd.notna(player.get('weight')) else None,
            'draft_round': draft_round,
            'draft_pick': draft_pick,
            'draft_year': int(player.get('rookie_year', 0)) if pd.notna(player.get('rookie_year')) else None,
            'college': player.get('college', '') if pd.notna(player.get('college')) else None,
            'status': player.get('status', 'ACT') if pd.notna(player.get('status')) else 'ACT',
            'jersey_number': int(player.get('jersey_number', 0)) if pd.notna(player.get('jersey_number')) else None,
        })
    
    with get_connection() as conn:
        conn.execute("DELETE FROM players")
        
        columns = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_str = ", ".join(columns)
        sql = f"INSERT OR REPLACE INTO players ({col_str}) VALUES ({placeholders})"
        
        values = [tuple(r.get(c) for c in columns) for r in rows]
        conn.executemany(sql, values)
    
    logger.info(f"Ingested {len(rows)} players")
    return len(rows)


def build_player_stats_from_pbp(season: int = None):
    """
    Build player weekly and season stats from play-by-play data.
    Since import_weekly_data may not be available for the current season,
    we derive stats directly from PBP data.
    """
    season = season or CURRENT_SEASON
    logger.info(f"Building player stats from PBP data for {season}...")
    
    with get_connection() as conn:
        # Get all plays for the season
        cursor = conn.execute("""
            SELECT * FROM play_by_play WHERE season = ?
            AND play_type IN ('pass', 'run')
        """, (season,))
        columns = [desc[0] for desc in cursor.description]
        plays = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    if not plays:
        logger.warning("No PBP data to build stats from")
        return 0
    
    df = pd.DataFrame(plays)
    logger.info(f"Processing {len(df)} plays for player stats")
    
    # Build weekly stats per player
    weekly_rows = []
    
    # Passers
    passer_plays = df[df['passer_player_id'].notna() & (df['passer_player_id'] != '')].copy()
    if len(passer_plays) > 0:
        passer_weekly = passer_plays.groupby(['passer_player_id', 'week', 'team_id']).agg(
            completions=('pass_or_run', lambda x: ((x == 'pass') & (passer_plays.loc[x.index, 'yards_gained'] > 0)).sum()),
            attempts=('pass_or_run', lambda x: (x == 'pass').sum()),
            passing_yards=('yards_gained', lambda x: x[passer_plays.loc[x.index, 'pass_or_run'] == 'pass'].sum()),
            passing_tds=('touchdown', 'sum'),
            interceptions=('interception', 'sum'),
            sacks_taken=('sack', 'sum'),
            passing_epa=('epa', lambda x: x[passer_plays.loc[x.index, 'pass_or_run'] == 'pass'].sum()),
        ).reset_index()
        
        for _, row in passer_weekly.iterrows():
            weekly_rows.append({
                'player_id': row['passer_player_id'],
                'season': season,
                'week': int(row['week']),
                'team_id': row['team_id'] if row['team_id'] != 'LA' else 'LAR',
                'position': 'QB',
                'games': 1,
                'completions': int(row.get('completions', 0)),
                'attempts': int(row.get('attempts', 0)),
                'passing_yards': float(row.get('passing_yards', 0)),
                'passing_tds': int(row.get('passing_tds', 0)),
                'interceptions': int(row.get('interceptions', 0)),
                'sacks_taken': int(row.get('sacks_taken', 0)),
                'passing_epa': float(row.get('passing_epa', 0)),
            })
    
    # Rushers
    rusher_plays = df[df['rusher_player_id'].notna() & (df['rusher_player_id'] != '')].copy()
    if len(rusher_plays) > 0:
        rusher_weekly = rusher_plays.groupby(['rusher_player_id', 'week', 'team_id']).agg(
            carries=('pass_or_run', 'count'),
            rushing_yards=('yards_gained', 'sum'),
            rushing_tds=('touchdown', 'sum'),
            rushing_epa=('epa', 'sum'),
        ).reset_index()
        
        for _, row in rusher_weekly.iterrows():
            # Check if this player already has a weekly row (QB who also rushes)
            existing = [r for r in weekly_rows 
                        if r['player_id'] == row['rusher_player_id'] 
                        and r['week'] == int(row['week'])]
            
            if existing:
                existing[0]['carries'] = int(row.get('carries', 0))
                existing[0]['rushing_yards'] = float(row.get('rushing_yards', 0))
                existing[0]['rushing_tds'] = int(row.get('rushing_tds', 0))
                existing[0]['rushing_epa'] = float(row.get('rushing_epa', 0))
            else:
                weekly_rows.append({
                    'player_id': row['rusher_player_id'],
                    'season': season,
                    'week': int(row['week']),
                    'team_id': row['team_id'] if row['team_id'] != 'LA' else 'LAR',
                    'position': '',
                    'games': 1,
                    'carries': int(row.get('carries', 0)),
                    'rushing_yards': float(row.get('rushing_yards', 0)),
                    'rushing_tds': int(row.get('rushing_tds', 0)),
                    'rushing_epa': float(row.get('rushing_epa', 0)),
                })
    
    # Receivers
    receiver_plays = df[df['receiver_player_id'].notna() & (df['receiver_player_id'] != '')].copy()
    if len(receiver_plays) > 0:
        receiver_weekly = receiver_plays.groupby(['receiver_player_id', 'week', 'team_id']).agg(
            targets=('pass_or_run', 'count'),
            receptions=('yards_gained', lambda x: (x > 0).sum()),
            receiving_yards=('yards_gained', lambda x: x[x > 0].sum()),
            receiving_tds=('touchdown', 'sum'),
            receiving_epa=('epa', 'sum'),
        ).reset_index()
        
        for _, row in receiver_weekly.iterrows():
            existing = [r for r in weekly_rows 
                        if r['player_id'] == row['receiver_player_id'] 
                        and r['week'] == int(row['week'])]
            
            if existing:
                existing[0]['targets'] = int(row.get('targets', 0))
                existing[0]['receptions'] = int(row.get('receptions', 0))
                existing[0]['receiving_yards'] = float(row.get('receiving_yards', 0))
                existing[0]['receiving_tds'] = int(row.get('receiving_tds', 0))
                existing[0]['receiving_epa'] = float(row.get('receiving_epa', 0))
            else:
                weekly_rows.append({
                    'player_id': row['receiver_player_id'],
                    'season': season,
                    'week': int(row['week']),
                    'team_id': row['team_id'] if row['team_id'] != 'LA' else 'LAR',
                    'position': '',
                    'games': 1,
                    'targets': int(row.get('targets', 0)),
                    'receptions': int(row.get('receptions', 0)),
                    'receiving_yards': float(row.get('receiving_yards', 0)),
                    'receiving_tds': int(row.get('receiving_tds', 0)),
                    'receiving_epa': float(row.get('receiving_epa', 0)),
                })
    
    # Insert weekly stats
    logger.info(f"Inserting {len(weekly_rows)} weekly stat rows...")
    
    with get_connection() as conn:
        conn.execute("DELETE FROM player_weekly WHERE season = ?", (season,))
        
        # Define all columns with defaults
        all_cols = [
            'player_id', 'season', 'week', 'team_id', 'position', 'games', 'snaps', 'snap_share',
            'completions', 'attempts', 'passing_yards', 'passing_tds', 'interceptions',
            'sacks_taken', 'passing_epa', 'cpoe',
            'carries', 'rushing_yards', 'rushing_tds', 'rushing_epa',
            'targets', 'receptions', 'receiving_yards', 'receiving_tds', 'receiving_epa',
            'target_share', 'air_yards_share',
            'tackles', 'tackles_for_loss', 'sacks', 'interceptions_def',
            'pass_deflections', 'forced_fumbles', 'fumble_recoveries',
            'epa_per_play', 'fantasy_points', 'fantasy_points_ppr',
        ]
        
        placeholders = ", ".join(["?"] * len(all_cols))
        col_str = ", ".join(all_cols)
        sql = f"INSERT OR REPLACE INTO player_weekly ({col_str}) VALUES ({placeholders})"
        
        values = []
        for row in weekly_rows:
            values.append(tuple(row.get(c, 0) for c in all_cols))
        
        batch_size = 5000
        for i in range(0, len(values), batch_size):
            conn.executemany(sql, values[i:i + batch_size])
    
    logger.info(f"Inserted {len(weekly_rows)} weekly stat rows")
    return len(weekly_rows)


def ingest_snap_counts(season: int = None):
    """Ingest snap count data to enhance player stats."""
    season = season or CURRENT_SEASON
    logger.info(f"Ingesting snap count data for {season}...")
    
    try:
        snaps = nfl.import_snap_counts([season])
    except Exception as e:
        logger.warning(f"Could not fetch snap counts: {e}")
        return 0
    
    if snaps is None or len(snaps) == 0:
        logger.warning("No snap count data available")
        return 0
    
    logger.info(f"Fetched {len(snaps)} snap count records")
    
    # Update weekly stats with snap counts
    # We need to match by player name + team + week since snap data uses pfr_player_id
    with get_connection() as conn:
        updated = 0
        for _, snap in snaps.iterrows():
            team = snap.get('team', '')
            if team == 'LA':
                team = 'LAR'
            
            off_snaps = int(snap.get('offense_snaps', 0)) if pd.notna(snap.get('offense_snaps')) else 0
            def_snaps = int(snap.get('defense_snaps', 0)) if pd.notna(snap.get('defense_snaps')) else 0
            total_snaps = off_snaps + def_snaps
            off_pct = float(snap.get('offense_pct', 0)) if pd.notna(snap.get('offense_pct')) else 0
            
            week = int(snap.get('week', 0)) if pd.notna(snap.get('week')) else 0
            
            if total_snaps > 0:
                # Try to update existing weekly row
                conn.execute("""
                    UPDATE player_weekly 
                    SET snaps = ?, snap_share = ?
                    WHERE team_id = ? AND week = ? AND season = ?
                    AND player_id IN (
                        SELECT player_id FROM players WHERE name = ? AND team_id = ?
                    )
                """, (total_snaps, off_pct, team, week, season,
                      snap.get('player', ''), team))
                updated += conn.total_changes
    
    logger.info(f"Updated {updated} snap count records")
    return updated


def build_season_aggregates(season: int = None):
    """Build season-level aggregates from weekly data."""
    season = season or CURRENT_SEASON
    logger.info(f"Building season aggregates for {season}...")
    
    with get_connection() as conn:
        # Clear existing season data
        conn.execute("DELETE FROM player_season WHERE season = ?", (season,))
        
        # Aggregate from weekly data
        conn.execute("""
            INSERT INTO player_season (
                player_id, season, team_id, position, games, total_snaps, avg_snap_share,
                completions, attempts, passing_yards, passing_tds, interceptions, sacks_taken,
                total_passing_epa, avg_cpoe,
                carries, rushing_yards, rushing_tds, total_rushing_epa,
                targets, receptions, receiving_yards, receiving_tds, total_receiving_epa,
                avg_target_share,
                tackles, tackles_for_loss, sacks, interceptions_def,
                pass_deflections, forced_fumbles, fumble_recoveries,
                total_epa, fantasy_points, fantasy_points_ppr
            )
            SELECT
                player_id, ? as season, team_id, position,
                SUM(games) as games,
                SUM(snaps) as total_snaps,
                AVG(snap_share) as avg_snap_share,
                SUM(completions), SUM(attempts), SUM(passing_yards),
                SUM(passing_tds), SUM(interceptions), SUM(sacks_taken),
                SUM(passing_epa), AVG(cpoe),
                SUM(carries), SUM(rushing_yards), SUM(rushing_tds), SUM(rushing_epa),
                SUM(targets), SUM(receptions), SUM(receiving_yards),
                SUM(receiving_tds), SUM(receiving_epa), AVG(target_share),
                SUM(tackles), SUM(tackles_for_loss), SUM(sacks),
                SUM(interceptions_def), SUM(pass_deflections),
                SUM(forced_fumbles), SUM(fumble_recoveries),
                COALESCE(SUM(passing_epa), 0) + COALESCE(SUM(rushing_epa), 0) + COALESCE(SUM(receiving_epa), 0),
                SUM(fantasy_points), SUM(fantasy_points_ppr)
            FROM player_weekly
            WHERE season = ?
            GROUP BY player_id
        """, (season, season))
        
        # Calculate EPA per play for season
        conn.execute("""
            UPDATE player_season
            SET epa_per_play = CASE
                WHEN total_snaps > 0 THEN total_epa / total_snaps
                WHEN (COALESCE(attempts,0) + COALESCE(carries,0) + COALESCE(targets,0)) > 0 
                THEN total_epa / (COALESCE(attempts,0) + COALESCE(carries,0) + COALESCE(targets,0))
                ELSE 0
            END
            WHERE season = ?
        """, (season,))
        
        count = conn.execute(
            "SELECT COUNT(*) FROM player_season WHERE season = ?", (season,)
        ).fetchone()[0]
    
    logger.info(f"Built season aggregates for {count} players")
    return count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    ingest_rosters()
    build_player_stats_from_pbp()
    ingest_snap_counts()
    build_season_aggregates()
