"""
NOAA Water Temperature Service

Fetches observed water temperature from NOAA CO-OPS for Mobile Bay.
Primary station: 8736897 (Middle Bay Light, AL) - Real-time conditions station
Backup station: 8735180 (Bayou La Batre, AL) - Tide prediction station

This module provides cached water temperature readings to avoid
repeated API calls during forecast generation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import requests
from sqlalchemy.orm import Session
from app.config import config
from app.utils.location_manager import get_current_location
from app.utils.location_registry import get_location

logger = logging.getLogger(__name__)

# NOAA CO-OPS API endpoint
NOAA_COOPS_BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

# Cache settings
CACHE_DURATION_MINUTES = 30  # Refresh water temp every 30 minutes
_cached_water_temp: Optional[Dict] = None
_cache_timestamp: Optional[datetime] = None


def _get_primary_station() -> str:
    """
    Get primary station ID (realtime conditions) for current location.
    
    Reads from location registry, falls back to config.yaml if unavailable.
    """
    try:
        location_id = get_current_location()
        location_data = get_location(location_id)
        if location_data:
            station = location_data.get("noaa", {}).get("realtime_station")
            if station:
                return station
    except Exception as e:
        logger.warning(f"Error reading location realtime station, using default: {e}")
    return config.realtime_conditions_station_id


def _get_backup_station() -> str:
    """
    Get backup station ID (tide prediction) for current location.
    
    Reads from location registry, falls back to config.yaml if unavailable.
    """
    try:
        location_id = get_current_location()
        location_data = get_location(location_id)
        if location_data:
            station = location_data.get("noaa", {}).get("tide_prediction_station")
            if station:
                return station
    except Exception as e:
        logger.warning(f"Error reading location tide station, using default: {e}")
    return config.tide_prediction_station_id


def fetch_water_temperature_from_noaa(station_id: str) -> Optional[Dict]:
    """
    Fetch latest water temperature from NOAA CO-OPS station.

    Args:
        station_id: NOAA CO-OPS station identifier

    Returns:
        Dict with water_temp_f and timestamp, or None if unavailable
    """
    try:
        # NOAA CO-OPS parameters
        # Product: water_temperature
        # Datum: MLLW (not relevant for temp but required)
        # Units: english (Fahrenheit)
        # Time zone: GMT
        # Format: JSON

        # Get last 24 hours of data to find most recent reading
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)

        params = {
            'product': 'water_temperature',
            'application': 'BayScan',
            'begin_date': start_time.strftime('%Y%m%d %H:%M'),
            'end_date': end_time.strftime('%Y%m%d %H:%M'),
            'station': station_id,
            'time_zone': 'gmt',
            'units': 'english',  # Returns Fahrenheit
            'format': 'json'
        }

        response = requests.get(NOAA_COOPS_BASE_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Check for errors in NOAA response
        if 'error' in data:
            logger.warning(f"NOAA CO-OPS error for station {station_id}: {data['error']}")
            return None

        # Extract most recent water temperature reading
        if 'data' in data and len(data['data']) > 0:
            # Get most recent reading (last item in array)
            latest_reading = data['data'][-1]

            # Parse temperature value
            temp_f = float(latest_reading['v'])  # Value in Fahrenheit
            timestamp_str = latest_reading['t']  # ISO format timestamp

            # Parse timestamp
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M')

            logger.info(f"Retrieved water temp from station {station_id}: {temp_f}°F at {timestamp}")

            return {
                'water_temp_f': temp_f,
                'timestamp': timestamp,
                'station_id': station_id
            }
        else:
            logger.warning(f"No water temperature data available from station {station_id}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching water temperature from NOAA station {station_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching water temperature from NOAA station {station_id}: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        logger.error(f"Error parsing NOAA water temperature data for station {station_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching water temperature: {e}")
        return None


def get_water_temperature() -> Optional[Dict]:
    """
    Get cached water temperature or fetch from NOAA if cache expired.

    Tries primary station first, falls back to backup if unavailable.

    Returns:
        Dict with water_temp_f and timestamp, or None if unavailable
    """
    global _cached_water_temp, _cache_timestamp

    # Check if cache is still valid
    if _cached_water_temp and _cache_timestamp:
        age = datetime.utcnow() - _cache_timestamp
        if age < timedelta(minutes=CACHE_DURATION_MINUTES):
            logger.debug(f"Using cached water temperature (age: {age.total_seconds():.0f}s)")
            return _cached_water_temp

    # Cache expired or empty, fetch fresh data
    logger.info("Fetching fresh water temperature from NOAA...")

    # Try primary station first (realtime conditions station)
    primary_station = _get_primary_station()
    result = fetch_water_temperature_from_noaa(primary_station)

    # If primary fails, try backup (tide prediction station)
    if result is None:
        backup_station = _get_backup_station()
        logger.info(f"Primary station {primary_station} unavailable, trying backup {backup_station}")
        result = fetch_water_temperature_from_noaa(backup_station)

    # Update cache if successful
    if result:
        _cached_water_temp = result
        _cache_timestamp = datetime.utcnow()
        logger.info(f"Water temperature cached: {result['water_temp_f']:.1f}°F")
    else:
        logger.warning("Failed to retrieve water temperature from all stations")
        # Keep old cache if available rather than returning None immediately
        if _cached_water_temp:
            logger.info("Returning stale cached water temperature")
            return _cached_water_temp

    return result


def update_water_temperature_cache() -> bool:
    """
    Force update of water temperature cache.

    Called by scheduler to periodically refresh water temp.

    Returns:
        True if successfully updated, False otherwise
    """
    global _cached_water_temp, _cache_timestamp

    logger.info("Scheduled water temperature update...")

    # Try primary station (realtime conditions)
    primary_station = _get_primary_station()
    result = fetch_water_temperature_from_noaa(primary_station)

    # Try backup if primary fails
    if result is None:
        backup_station = _get_backup_station()
        result = fetch_water_temperature_from_noaa(backup_station)

    if result:
        _cached_water_temp = result
        _cache_timestamp = datetime.utcnow()
        logger.info(f"Water temperature updated: {result['water_temp_f']:.1f}°F")
        return True
    else:
        logger.error("Failed to update water temperature cache")
        return False


def clear_cache():
    """Clear the water temperature cache (useful for testing)."""
    global _cached_water_temp, _cache_timestamp
    _cached_water_temp = None
    _cache_timestamp = None
    logger.info("Water temperature cache cleared")
