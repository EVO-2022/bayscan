"""Service for astronomical data: sunrise, sunset, moon phase."""
from datetime import datetime, timedelta, date as dt_date
from typing import Dict
from sqlalchemy.orm import Session
from app.config import config
from app.models.schemas import AstronomicalData
import logging
import math

logger = logging.getLogger(__name__)


def fetch_astronomical_data(db: Session, days_ahead: int = 7) -> bool:
    """
    Calculate and store astronomical data (sunrise, sunset, moon phase).

    Args:
        db: Database session
        days_ahead: Number of days to compute (default 7)

    Returns:
        True if successful, False otherwise
    """
    try:
        today = datetime.utcnow().date()

        for i in range(days_ahead):
            target_date = today + timedelta(days=i)

            # Calculate sunrise and sunset
            sunrise, sunset = _calculate_sun_times(target_date)

            # Calculate moon phase
            moon_phase, moon_phase_name = _calculate_moon_phase(target_date)

            # Check if we already have data for this date
            existing = db.query(AstronomicalData).filter(
                AstronomicalData.date == datetime.combine(target_date, datetime.min.time())
            ).first()

            if existing:
                # Update existing
                existing.sunrise = sunrise
                existing.sunset = sunset
                existing.moon_phase = moon_phase
                existing.moon_phase_name = moon_phase_name
                existing.fetched_at = datetime.utcnow()
            else:
                # Create new
                astro_entry = AstronomicalData(
                    date=datetime.combine(target_date, datetime.min.time()),
                    sunrise=sunrise,
                    sunset=sunset,
                    moon_phase=moon_phase,
                    moon_phase_name=moon_phase_name,
                    fetched_at=datetime.utcnow()
                )
                db.add(astro_entry)

        db.commit()
        logger.info(f"Stored astronomical data for {days_ahead} days")
        return True

    except Exception as e:
        logger.error(f"Error fetching astronomical data: {e}")
        db.rollback()
        return False


def _calculate_sun_times(target_date: dt_date) -> tuple:
    """
    Calculate sunrise and sunset times using simplified algorithm.

    This uses a simplified calculation. For production, consider using
    a library like ephem or astral for more accuracy.
    """
    lat = config.latitude
    lon = config.longitude

    # Julian day
    year = target_date.year
    month = target_date.month
    day = target_date.day

    # Simplified sunrise/sunset calculation
    # Using approximate formulas - good enough for fishing app

    # Day of year
    N = target_date.timetuple().tm_yday

    # Convert longitude to hour value and calculate approximate time
    lngHour = lon / 15.0

    # Rising time
    t_rise = N + ((6 - lngHour) / 24)
    t_set = N + ((18 - lngHour) / 24)

    # Sun's mean anomaly
    M_rise = (0.9856 * t_rise) - 3.289
    M_set = (0.9856 * t_set) - 3.289

    # Sun's true longitude
    L_rise = M_rise + (1.916 * math.sin(math.radians(M_rise))) + (0.020 * math.sin(math.radians(2 * M_rise))) + 282.634
    L_set = M_set + (1.916 * math.sin(math.radians(M_set))) + (0.020 * math.sin(math.radians(2 * M_set))) + 282.634

    # Normalize to 0-360
    L_rise = L_rise % 360
    L_set = L_set % 360

    # Sun's right ascension
    RA_rise = math.degrees(math.atan(0.91764 * math.tan(math.radians(L_rise))))
    RA_rise = RA_rise % 360
    RA_set = math.degrees(math.atan(0.91764 * math.tan(math.radians(L_set))))
    RA_set = RA_set % 360

    # Right ascension value needs to be in same quadrant as L
    Lquadrant_rise = (math.floor(L_rise / 90)) * 90
    RAquadrant_rise = (math.floor(RA_rise / 90)) * 90
    RA_rise = RA_rise + (Lquadrant_rise - RAquadrant_rise)

    Lquadrant_set = (math.floor(L_set / 90)) * 90
    RAquadrant_set = (math.floor(RA_set / 90)) * 90
    RA_set = RA_set + (Lquadrant_set - RAquadrant_set)

    # Right ascension to hours
    RA_rise = RA_rise / 15
    RA_set = RA_set / 15

    # Sun's declination
    sinDec_rise = 0.39782 * math.sin(math.radians(L_rise))
    cosDec_rise = math.cos(math.asin(sinDec_rise))
    sinDec_set = 0.39782 * math.sin(math.radians(L_set))
    cosDec_set = math.cos(math.asin(sinDec_set))

    # Sun's local hour angle
    zenith = math.radians(90.833)  # Official zenith
    cosH_rise = (math.cos(zenith) - (sinDec_rise * math.sin(math.radians(lat)))) / (cosDec_rise * math.cos(math.radians(lat)))
    cosH_set = (math.cos(zenith) - (sinDec_set * math.sin(math.radians(lat)))) / (cosDec_set * math.cos(math.radians(lat)))

    # Clamp to valid range
    cosH_rise = max(-1, min(1, cosH_rise))
    cosH_set = max(-1, min(1, cosH_set))

    H_rise = 360 - math.degrees(math.acos(cosH_rise))
    H_set = math.degrees(math.acos(cosH_set))

    H_rise = H_rise / 15
    H_set = H_set / 15

    # Local mean time of rising/setting
    T_rise = H_rise + RA_rise - (0.06571 * t_rise) - 6.622
    T_set = H_set + RA_set - (0.06571 * t_set) - 6.622

    # Adjust to UTC
    UT_rise = T_rise - lngHour
    UT_set = T_set - lngHour

    # Normalize to 0-24
    UT_rise = UT_rise % 24
    UT_set = UT_set % 24

    # Convert to datetime
    sunrise_hour = int(UT_rise)
    sunrise_minute = int((UT_rise - sunrise_hour) * 60)
    sunset_hour = int(UT_set)
    sunset_minute = int((UT_set - sunset_hour) * 60)

    sunrise = datetime.combine(target_date, datetime.min.time()).replace(
        hour=sunrise_hour, minute=sunrise_minute
    )
    sunset = datetime.combine(target_date, datetime.min.time()).replace(
        hour=sunset_hour, minute=sunset_minute
    )

    return sunrise, sunset


def _calculate_moon_phase(target_date: dt_date) -> tuple:
    """
    Calculate moon phase for a given date.

    Returns:
        (phase_value, phase_name) where phase_value is 0-1
    """
    # Known new moon date
    known_new_moon = datetime(2000, 1, 6, 18, 14)

    # Calculate days since known new moon
    date_dt = datetime.combine(target_date, datetime.min.time())
    days_since = (date_dt - known_new_moon).days

    # Lunar cycle is approximately 29.53059 days
    lunar_cycle = 29.53059

    # Calculate phase
    phase = (days_since % lunar_cycle) / lunar_cycle

    # Determine phase name
    if phase < 0.0625:
        phase_name = "New"
    elif phase < 0.1875:
        phase_name = "Waxing Crescent"
    elif phase < 0.3125:
        phase_name = "First Quarter"
    elif phase < 0.4375:
        phase_name = "Waxing Gibbous"
    elif phase < 0.5625:
        phase_name = "Full"
    elif phase < 0.6875:
        phase_name = "Waning Gibbous"
    elif phase < 0.8125:
        phase_name = "Last Quarter"
    elif phase < 0.9375:
        phase_name = "Waning Crescent"
    else:
        phase_name = "New"

    return round(phase, 3), phase_name


def get_time_of_day(db: Session, target_time: datetime) -> str:
    """
    Determine time of day category: night, dawn, day, dusk.

    Args:
        db: Database session
        target_time: Time to categorize

    Returns:
        'night', 'dawn', 'day', or 'dusk'
    """
    try:
        target_date = target_time.date()

        # Get astronomical data for this date
        astro = db.query(AstronomicalData).filter(
            AstronomicalData.date == datetime.combine(target_date, datetime.min.time())
        ).first()

        if not astro:
            # Default to day if no data
            hour = target_time.hour
            if 6 <= hour < 18:
                return 'day'
            else:
                return 'night'

        sunrise = astro.sunrise
        sunset = astro.sunset

        # Dawn: 30 min before to 30 min after sunrise
        dawn_start = sunrise - timedelta(minutes=30)
        dawn_end = sunrise + timedelta(minutes=30)

        # Dusk: 30 min before to 30 min after sunset
        dusk_start = sunset - timedelta(minutes=30)
        dusk_end = sunset + timedelta(minutes=30)

        if dawn_start <= target_time <= dawn_end:
            return 'dawn'
        elif dusk_start <= target_time <= dusk_end:
            return 'dusk'
        elif sunrise < target_time < sunset:
            return 'day'
        else:
            return 'night'

    except Exception as e:
        logger.error(f"Error determining time of day: {e}")
        # Default based on hour
        hour = target_time.hour
        if 6 <= hour < 18:
            return 'day'
        else:
            return 'night'


def get_moon_phase(db: Session, target_date: dt_date = None) -> Dict:
    """Get moon phase for a given date."""
    if target_date is None:
        target_date = datetime.utcnow().date()

    try:
        astro = db.query(AstronomicalData).filter(
            AstronomicalData.date == datetime.combine(target_date, datetime.min.time())
        ).first()

        if astro:
            return {
                'phase': astro.moon_phase,
                'name': astro.moon_phase_name
            }

        # Calculate if not in DB
        phase, name = _calculate_moon_phase(target_date)
        return {'phase': phase, 'name': name}

    except Exception as e:
        logger.error(f"Error getting moon phase: {e}")
        return {'phase': 0.0, 'name': 'Unknown'}
