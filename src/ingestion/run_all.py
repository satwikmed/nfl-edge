"""
Master ingestion orchestrator.
Runs all data ingestion scripts in the correct order.
Usage: python -m src.ingestion.run_all
"""

import logging
import sys
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.utils.db import init_db, get_table_count, DB_PATH
from src.ingestion.teams import ingest_teams
from src.ingestion.play_by_play import ingest_play_by_play, ingest_games
from src.ingestion.player_stats import (
    ingest_rosters, build_player_stats_from_pbp,
    ingest_snap_counts, build_season_aggregates
)
from src.ingestion.contracts import ingest_contracts
from src.ingestion.injuries import ingest_injuries

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_all():
    """Run the complete data ingestion pipeline."""
    start = time.time()
    logger.info("=" * 60)
    logger.info("NFL Team Intelligence - Data Ingestion Pipeline")
    logger.info("=" * 60)
    
    # Step 0: Initialize database
    logger.info("\n[Step 0] Initializing database...")
    init_db()
    logger.info(f"Database: {DB_PATH}")
    
    # Step 1: Team metadata
    logger.info("\n[Step 1] Ingesting team metadata...")
    try:
        team_count = ingest_teams()
        logger.info(f"  ✓ {team_count} teams ingested")
    except Exception as e:
        logger.error(f"  ✗ Team ingestion failed: {e}")
        raise
    
    # Step 2: Game results
    logger.info("\n[Step 2] Ingesting game results...")
    try:
        game_count = ingest_games()
        logger.info(f"  ✓ {game_count} games ingested")
    except Exception as e:
        logger.error(f"  ✗ Game ingestion failed: {e}")
        game_count = 0
    
    # Step 3: Player rosters (uses import_seasonal_rosters)
    logger.info("\n[Step 3] Ingesting player rosters...")
    try:
        player_count = ingest_rosters()
        logger.info(f"  ✓ {player_count} players ingested")
    except Exception as e:
        logger.error(f"  ✗ Roster ingestion failed: {e}")
        player_count = 0
    
    # Step 4: Play-by-play data (largest dataset)
    logger.info("\n[Step 4] Ingesting play-by-play data...")
    try:
        pbp_count = ingest_play_by_play()
        logger.info(f"  ✓ {pbp_count} plays ingested")
    except Exception as e:
        logger.error(f"  ✗ Play-by-play ingestion failed: {e}")
        pbp_count = 0
    
    # Step 5: Build player stats from PBP data
    logger.info("\n[Step 5] Building player stats from play-by-play...")
    try:
        weekly_count = build_player_stats_from_pbp()
        logger.info(f"  ✓ {weekly_count} weekly stat rows built")
    except Exception as e:
        logger.error(f"  ✗ Player stats build failed: {e}")
        import traceback
        traceback.print_exc()
        weekly_count = 0
    
    # Step 6: Snap counts
    logger.info("\n[Step 6] Ingesting snap counts...")
    try:
        snap_count = ingest_snap_counts()
        logger.info(f"  ✓ {snap_count} snap count records updated")
    except Exception as e:
        logger.error(f"  ✗ Snap count ingestion failed: {e}")
        snap_count = 0
    
    # Step 7: Build season aggregates
    logger.info("\n[Step 7] Building season aggregates...")
    try:
        season_count = build_season_aggregates()
        logger.info(f"  ✓ {season_count} player season aggregates built")
    except Exception as e:
        logger.error(f"  ✗ Season aggregates failed: {e}")
        season_count = 0
    
    # Step 8: Contract data (uses nfl_data_py import_contracts)
    logger.info("\n[Step 8] Ingesting contract data...")
    try:
        contract_count = ingest_contracts()
        logger.info(f"  ✓ {contract_count} contracts ingested")
    except Exception as e:
        logger.error(f"  ✗ Contract ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        contract_count = 0
    
    # Step 9: Injury data
    logger.info("\n[Step 9] Ingesting injury data...")
    try:
        injury_count = ingest_injuries()
        logger.info(f"  ✓ {injury_count} injury records ingested")
    except Exception as e:
        logger.error(f"  ✗ Injury ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        injury_count = 0
    
    # Summary
    elapsed = time.time() - start
    logger.info("\n" + "=" * 60)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Teams:           {get_table_count('teams')}")
    logger.info(f"  Games:           {get_table_count('games')}")
    logger.info(f"  Players:         {get_table_count('players')}")
    logger.info(f"  Play-by-play:    {get_table_count('play_by_play')}")
    logger.info(f"  Weekly stats:    {get_table_count('player_weekly')}")
    logger.info(f"  Season stats:    {get_table_count('player_season')}")
    logger.info(f"  Contracts:       {get_table_count('contracts')}")
    logger.info(f"  Injuries:        {get_table_count('injuries')}")
    logger.info(f"  Time elapsed:    {elapsed:.1f}s")
    logger.info(f"  DB size:         {DB_PATH.stat().st_size / (1024*1024):.1f} MB")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_all()
