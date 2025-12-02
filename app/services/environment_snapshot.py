"""Service for capturing and storing environment snapshots every 5-15 minutes.

This allows BayScan to learn "no-bite conditions" even when no fish are caught.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.schemas import EnvironmentSnapshot
from app.services.tide_service import get_tide_for_time
from app.services.weather_service import get_weather_for_time
from app.services.watertemp_service import get_water_temperature
from app.services.astronomical_service import get_time_of_day, get_moon_phase
from app.services.weather_observations import get_weather_observations
import logging

logger = logging.getLogger(__name__)


def capture_environment_snapshot(db: Session) -> bool:
    """
    Capture current environment conditions and store as snapshot.

    Returns:
        True if successful, False otherwise
    """
    try:
        now = datetime.utcnow()

        # Check if we already have a recent snapshot (within 5 minutes)
        cutoff = now - timedelta(minutes=5)
        recent_snapshot = db.query(EnvironmentSnapshot).filter(
            EnvironmentSnapshot.timestamp >= cutoff
        ).first()

        if recent_snapshot:
            logger.debug("Recent snapshot exists, skipping")
            return True

        # Get current conditions
        tide_data = get_tide_for_time(db, now)
        weather_data = get_weather_for_time(db, now)
        time_of_day = get_time_of_day(db, now)
        moon_data = get_moon_phase(db, now.date())
        water_temp_data = get_water_temperature()
        noaa_obs = get_weather_observations()

        # Use NOAA observations if available
        if noaa_obs:
            air_temp = noaa_obs.get('air_temp_f')
            wind_speed = noaa_obs.get('wind_speed_mph')
            wind_direction = noaa_obs.get('wind_direction_cardinal')
            humidity = noaa_obs.get('relative_humidity')
            pressure = noaa_obs.get('pressure_mb')
        else:
            air_temp = weather_data.get('temperature')
            wind_speed = weather_data.get('wind_speed')
            wind_direction = weather_data.get('wind_direction')
            humidity = None
            pressure = None

        # Determine tide stage from state
        tide_stage = map_tide_state_to_stage(
            tide_data['state'],
            tide_data['height']
        )

        # Check if dock lights should be on (after sunset)
        dock_lights_on = time_of_day in ['dusk', 'night']

        # Create snapshot
        snapshot = EnvironmentSnapshot(
            timestamp=now,
            water_temp=water_temp_data['water_temp_f'] if water_temp_data else None,
            air_temp=air_temp,
            humidity=humidity,
            barometric_pressure=pressure,
            tide_height=tide_data['height'],
            tide_stage=tide_stage,
            current_speed=tide_data.get('change_rate'),
            current_direction=None,  # Not available from current data
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            weather=weather_data.get('conditions'),
            time_of_day=time_of_day,
            moon_phase=moon_data.get('phase'),
            dock_lights_on=dock_lights_on
        )

        db.add(snapshot)
        db.commit()

        logger.info(f"Captured environment snapshot at {now}")
        return True

    except Exception as e:
        logger.error(f"Error capturing environment snapshot: {e}")
        db.rollback()
        return False


def get_latest_snapshot(db: Session) -> EnvironmentSnapshot:
    """Get the most recent environment snapshot."""
    return db.query(EnvironmentSnapshot).order_by(
        EnvironmentSnapshot.timestamp.desc()
    ).first()


def get_snapshot_as_dict(snapshot: EnvironmentSnapshot) -> dict:
    """Convert snapshot to dictionary for scoring."""
    if not snapshot:
        return {}

    return {
        'water_temperature': snapshot.water_temp,
        'air_temperature': snapshot.air_temp,
        'humidity': snapshot.humidity,
        'barometric_pressure': snapshot.barometric_pressure,
        'tide_height': snapshot.tide_height,
        'tide_stage': snapshot.tide_stage,
        'current_speed': snapshot.current_speed,
        'current_direction': snapshot.current_direction,
        'wind_speed': snapshot.wind_speed,
        'wind_direction': snapshot.wind_direction,
        'weather': snapshot.weather,
        'time_of_day': snapshot.time_of_day,
        'moon_phase': snapshot.moon_phase,
        'dock_lights_on': snapshot.dock_lights_on
    }


def map_tide_state_to_stage(tide_state: str, tide_height: float) -> str:
    """
    Map tide state to tide stage.

    tide_state from service: 'rising', 'falling', 'slack'
    tide_stage for scoring: 'incoming', 'outgoing', 'slack', 'high', 'low'
    """
    if tide_state == 'slack':
        # Determine if high or low slack based on height
        if tide_height >= 1.5:
            return 'high'
        else:
            return 'low'
    elif tide_state == 'rising':
        return 'incoming'
    elif tide_state == 'falling':
        return 'outgoing'
    else:
        return 'slack'


def cleanup_old_snapshots(db: Session, days_to_keep: int = 30) -> int:
    """
    Clean up old snapshots to prevent database bloat.

    Args:
        db: Database session
        days_to_keep: Number of days of snapshots to keep

    Returns:
        Number of snapshots deleted
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

        deleted = db.query(EnvironmentSnapshot).filter(
            EnvironmentSnapshot.timestamp < cutoff
        ).delete()

        db.commit()
        logger.info(f"Deleted {deleted} old environment snapshots")
        return deleted

    except Exception as e:
        logger.error(f"Error cleaning up snapshots: {e}")
        db.rollback()
        return 0
