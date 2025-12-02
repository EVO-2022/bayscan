"""Background scheduler for periodic data fetching and forecast updates."""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from app.database import SessionLocal
from app.services import (
    fetch_tide_data,
    fetch_weather_data,
    fetch_astronomical_data,
    compute_forecasts
)
from app.services.watertemp_service import update_water_temperature_cache
from app.services.weather_observations import update_weather_observations_cache
from app.config import config
import logging

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def fetch_water_temperature():
    """Fetch water temperature from NOAA (independent of main data fetch)."""
    logger.info("Fetching water temperature from NOAA...")
    try:
        success = update_water_temperature_cache()
        if success:
            logger.info("Water temperature updated successfully")
        else:
            logger.warning("Failed to update water temperature")
    except Exception as e:
        logger.error(f"Error fetching water temperature: {e}")


def fetch_weather_observations():
    """Fetch weather observations from NOAA (air temp, wind, pressure)."""
    logger.info("Fetching weather observations from NOAA...")
    try:
        success = update_weather_observations_cache()
        if success:
            logger.info("Weather observations updated successfully")
        else:
            logger.warning("Failed to update weather observations")
    except Exception as e:
        logger.error(f"Error fetching weather observations: {e}")


def capture_environment():
    """Capture environment snapshot - NEW HYPERLOCAL SPEC."""
    logger.info("Capturing environment snapshot...")
    db = SessionLocal()
    try:
        from app.services.environment_snapshot import capture_environment_snapshot

        success = capture_environment_snapshot(db)
        if success:
            logger.info("Environment snapshot captured successfully")
        else:
            logger.warning("Failed to capture environment snapshot")
    except Exception as e:
        logger.error(f"Error capturing environment snapshot: {e}")
    finally:
        db.close()


def periodic_score_recalculation():
    """
    Periodic score recalculation for decay and condition changes.

    Recalculates scores for species+zone pairs with recent activity to:
    - Apply decay to recent activity bonuses
    - Apply decay to predator penalties
    - Reflect changing environmental conditions
    """
    logger.info("Running periodic score recalculation...")
    db = SessionLocal()
    try:
        from datetime import timedelta
        from app.models.schemas import Catch, BaitLog, PredatorLog, BiteScore
        from app.services.score_cache_service import recalculate_bite_score
        from app.services.tip_generation_service import update_species_zone_tip
        from app.rules.species_tiers import TIER_1_SPECIES

        # Get species+zone pairs with recent activity (last 6 hours)
        cutoff = datetime.utcnow() - timedelta(hours=6)

        # Find zones with recent catches
        recent_catches = db.query(Catch.species, Catch.zone_id).filter(
            Catch.timestamp >= cutoff
        ).distinct().all()

        # Find zones with recent bait activity
        recent_bait = db.query(BaitLog.zone_id).filter(
            BaitLog.timestamp >= cutoff
        ).distinct().all()

        # Find zones with recent predator activity
        recent_predators = db.query(PredatorLog.zone).filter(
            PredatorLog.time >= cutoff
        ).distinct().all()

        # Collect unique species+zone pairs
        pairs_to_recalc = set()

        # Add from catches
        for species, zone in recent_catches:
            pairs_to_recalc.add((species, zone))

        # Add predator-affected zones (prey species)
        prey_species = ['speckled_trout', 'white_trout', 'menhaden', 'mullet']
        for (zone,) in recent_predators:
            for prey in prey_species:
                pairs_to_recalc.add((prey, zone))

        # If no recent activity, still recalculate all Tier 1 species periodically
        # to reflect environmental changes
        if not pairs_to_recalc:
            zones = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5']
            for species in TIER_1_SPECIES:
                for zone in zones:
                    pairs_to_recalc.add((species, zone))

        # Recalculate scores
        count = 0
        for species, zone in pairs_to_recalc:
            try:
                recalculate_bite_score(db, species, zone)
                update_species_zone_tip(db, species, zone)
                count += 1
            except Exception as e:
                logger.error(f"Error recalculating {species} {zone}: {e}")

        logger.info(f"Periodic recalculation complete: {count} species+zone pairs updated")

    except Exception as e:
        logger.error(f"Error in periodic score recalculation: {e}")
    finally:
        db.close()


def fetch_all_data():
    """Fetch all external data and compute forecasts."""
    logger.info("Starting scheduled data fetch...")
    db = SessionLocal()
    try:
        # Fetch tide data
        logger.info("Fetching tide data...")
        tide_success = fetch_tide_data(db, hours_ahead=48)

        # Fetch weather data
        logger.info("Fetching weather data...")
        weather_success = fetch_weather_data(db)

        # Fetch astronomical data
        logger.info("Fetching astronomical data...")
        astro_success = fetch_astronomical_data(db, days_ahead=7)

        # Fetch water temperature (updates cache for forecast computation)
        fetch_water_temperature()

        # Fetch weather observations (air temp, wind, pressure)
        fetch_weather_observations()

        # Compute forecasts
        logger.info("Computing forecasts...")
        forecast_success = compute_forecasts(db, hours_ahead=24)

        if all([tide_success, weather_success, astro_success, forecast_success]):
            logger.info("Data fetch and forecast computation completed successfully")
        else:
            logger.warning(
                f"Data fetch completed with issues: "
                f"tide={tide_success}, weather={weather_success}, "
                f"astro={astro_success}, forecast={forecast_success}"
            )

    except Exception as e:
        logger.error(f"Error in scheduled data fetch: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler."""
    # Add job to fetch data periodically
    scheduler.add_job(
        fetch_all_data,
        trigger=IntervalTrigger(minutes=config.fetch_interval_minutes),
        id='fetch_data',
        name='Fetch tide, weather, and compute forecasts',
        replace_existing=True
    )

    # Add job to capture environment snapshots every 10 minutes (NEW HYPERLOCAL SPEC)
    scheduler.add_job(
        capture_environment,
        trigger=IntervalTrigger(minutes=10),
        id='capture_environment',
        name='Capture environment snapshot',
        replace_existing=True
    )

    # Add job to recalculate scores periodically (decay & condition changes)
    scheduler.add_job(
        periodic_score_recalculation,
        trigger=IntervalTrigger(minutes=30),
        id='periodic_score_recalc',
        name='Periodic score recalculation for decay',
        replace_existing=True
    )

    # Run immediately on startup
    scheduler.add_job(
        fetch_all_data,
        id='fetch_data_startup',
        name='Initial data fetch on startup',
        replace_existing=True
    )

    # Capture environment snapshot immediately on startup
    scheduler.add_job(
        capture_environment,
        id='capture_environment_startup',
        name='Initial environment snapshot on startup',
        replace_existing=True
    )

    scheduler.start()
    logger.info(f"Scheduler started. Data will be fetched every {config.fetch_interval_minutes} minutes.")
    logger.info("Environment snapshots will be captured every 10 minutes.")
    logger.info("Score recalculation will run every 30 minutes for decay and condition changes.")


def stop_scheduler():
    """Stop the background scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped.")
