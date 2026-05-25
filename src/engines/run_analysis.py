"""
Master analysis orchestrator.
Runs all profiling and analysis engines, then exports the data for the frontend.
Usage: python -m src.engines.run_analysis
"""

import logging
import sys
import time
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.profiling.offensive_identity import profile_all_offenses
from src.profiling.defensive_identity import profile_all_defenses
from src.profiling.roster_composition import profile_all_rosters
from src.engines.play_calling import run_play_calling_engine
from src.engines.roster_value import run_roster_value_engine
from src.engines.in_game_decisions import run_in_game_decisions_engine
from src.export_data import export_all

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_all_analysis():
    """Run all profiling and analysis engines, and export JSON data."""
    start = time.time()
    logger.info("=" * 60)
    logger.info("NFL Team Intelligence - Analytical Pipelines")
    logger.info("=" * 60)
    
    # Step 1: Profiling Modules
    logger.info("\n[Step 1] Running Profiling Modules...")
    try:
        profile_all_offenses()
        profile_all_defenses()
        profile_all_rosters()
        logger.info("  ✓ Profiling complete")
    except Exception as e:
        logger.error(f"  ✗ Profiling failed: {e}")
        raise
    
    # Step 2: Analytical Engines
    logger.info("\n[Step 2] Running Analytical Engines...")
    try:
        run_play_calling_engine()
        run_roster_value_engine()
        run_in_game_decisions_engine()
        logger.info("  ✓ Analytical Engines complete")
    except Exception as e:
        logger.error(f"  ✗ Analysis failed: {e}")
        raise
        
    # Step 3: Export static files for Dashboard
    logger.info("\n[Step 3] Exporting data to Next.js dashboard...")
    try:
        export_all()
        logger.info("  ✓ Data export complete")
    except Exception as e:
        logger.error(f"  ✗ Data export failed: {e}")
        raise
    
    elapsed = time.time() - start
    logger.info("\n" + "=" * 60)
    logger.info("ANALYSIS & EXPORT COMPLETE")
    logger.info(f"Time elapsed: {elapsed:.1f}s")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_all_analysis()
