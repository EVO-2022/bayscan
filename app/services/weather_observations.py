"""
NOAA Weather Observations Service

Fetches real-time weather observations from NOAA CO-OPS meteorological stations.
Provides observed air temperature, wind speed, wind direction, wind gusts, and pressure.

Primary Station: 8736897 (Middle Bay Light, AL) - Real-time conditions
Backup: 8735180 (Bayou La Batre, AL) - Tide prediction station
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import requests
from app.config import config

logger = logging.getLogger(__name__)

NOAA_COOPS_BASE_URL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"

# Cache settings
CACHE_DURATION_MINUTES = 15  # Refresh every 15 minutes
_cached_observations: Optional[Dict] = None
_cache_timestamp: Optional[datetime] = None

def _get_primary_station() -> str:
    """Get primary station ID from config (realtime conditions station)"""
    return config.realtime_conditions_station_id

def _get_backup_station() -> str:
    """Get backup station ID from config (tide prediction station)"""
    return config.tide_prediction_station_id


def fetch_weather_observations_from_noaa(station_id: str) -> Optional[Dict]:
    """
    Fetch latest weather observations from NOAA CO-OPS station.

    Args:
        station_id: NOAA CO-OPS station identifier

    Returns:
        Dict with weather observations, or None if unavailable
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=2)  # Get last 2 hours

        observations = {}

        # Fetch multiple meteorological products
        products = {
            'air_temperature': 'air_temperature',
            'wind': 'wind',
            'air_pressure': 'air_pressure'
        }

        for product_name, product_code in products.items():
            try:
                params = {
                    'product': product_code,
                    'application': 'BayScan',
                    'begin_date': start_time.strftime('%Y%m%d %H:%M'),
                    'end_date': end_time.strftime('%Y%m%d %H:%M'),
                    'station': station_id,
                    'time_zone': 'gmt',
                    'units': 'english',
                    'format': 'json'
                }

                response = requests.get(NOAA_COOPS_BASE_URL, params=params, timeout=10)
                response.raise_for_status()

                data = response.json()

                if 'error' in data:
                    logger.warning(f"NOAA error for {product_name} at station {station_id}: {data['error']}")
                    continue

                if 'data' in data and len(data['data']) > 0:
                    latest = data['data'][-1]  # Get most recent reading

                    if product_code == 'air_temperature':
                        observations['air_temp_f'] = float(latest['v'])
                        observations['air_temp_timestamp'] = datetime.strptime(latest['t'], '%Y-%m-%d %H:%M')

                    elif product_code == 'wind':
                        observations['wind_speed_mph'] = float(latest['s'])
                        observations['wind_direction_deg'] = float(latest['d'])
                        observations['wind_gust_mph'] = float(latest['g']) if 'g' in latest and latest['g'] else None
                        observations['wind_timestamp'] = datetime.strptime(latest['t'], '%Y-%m-%d %H:%M')

                        # Convert wind direction from degrees to cardinal
                        observations['wind_direction_cardinal'] = _degrees_to_cardinal(float(latest['d']))

                    elif product_code == 'air_pressure':
                        observations['pressure_mb'] = float(latest['v'])
                        observations['pressure_timestamp'] = datetime.strptime(latest['t'], '%Y-%m-%d %H:%M')

            except Exception as e:
                logger.warning(f"Error fetching {product_name} from station {station_id}: {e}")
                continue

        if observations:
            observations['station_id'] = station_id
            observations['fetch_time'] = datetime.utcnow()
            logger.info(f"Retrieved weather observations from station {station_id}")
            return observations
        else:
            logger.warning(f"No weather observations available from station {station_id}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching weather observations from station {station_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather observations from station {station_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching weather observations: {e}")
        return None


def _degrees_to_cardinal(degrees: float) -> str:
    """Convert wind direction in degrees to cardinal direction."""
    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

    # Normalize to 0-360
    degrees = degrees % 360

    # Calculate index (16 directions = 22.5 degrees each)
    index = round(degrees / 22.5) % 16

    return directions[index]


def get_weather_observations() -> Optional[Dict]:
    """
    Get cached weather observations or fetch from NOAA if cache expired.

    Returns:
        Dict with weather observations, or None if unavailable
    """
    global _cached_observations, _cache_timestamp

    # Check if cache is still valid
    if _cached_observations and _cache_timestamp:
        age = datetime.utcnow() - _cache_timestamp
        if age < timedelta(minutes=CACHE_DURATION_MINUTES):
            logger.debug(f"Using cached weather observations (age: {age.total_seconds():.0f}s)")
            return _cached_observations

    # Cache expired or empty, fetch fresh data
    logger.info("Fetching fresh weather observations from NOAA...")

    # Try primary station first (realtime conditions station)
    primary_station = _get_primary_station()
    result = fetch_weather_observations_from_noaa(primary_station)

    # If primary fails, try backup (tide prediction station)
    if result is None:
        backup_station = _get_backup_station()
        logger.info(f"Primary station {primary_station} unavailable, trying backup {backup_station}")
        result = fetch_weather_observations_from_noaa(backup_station)

    # Update cache if successful
    if result:
        _cached_observations = result
        _cache_timestamp = datetime.utcnow()
        logger.info(f"Weather observations cached from station {result['station_id']}")
    else:
        logger.warning("Failed to retrieve weather observations from all stations")
        # Keep old cache if available
        if _cached_observations:
            logger.info("Returning stale cached weather observations")
            return _cached_observations

    return result


def update_weather_observations_cache() -> bool:
    """
    Force update of weather observations cache.

    Called by scheduler to periodically refresh observations.

    Returns:
        True if successfully updated, False otherwise
    """
    global _cached_observations, _cache_timestamp

    logger.info("Scheduled weather observations update...")

    # Try primary station (realtime conditions)
    primary_station = _get_primary_station()
    result = fetch_weather_observations_from_noaa(primary_station)

    # Try backup if primary fails
    if result is None:
        backup_station = _get_backup_station()
        result = fetch_weather_observations_from_noaa(backup_station)

    if result:
        _cached_observations = result
        _cache_timestamp = datetime.utcnow()

        air_temp = result.get('air_temp_f', 'N/A')
        wind = f"{result.get('wind_speed_mph', 'N/A')} mph {result.get('wind_direction_cardinal', '')}"
        logger.info(f"Weather observations updated: {air_temp}°F, Wind: {wind}")
        return True
    else:
        logger.error("Failed to update weather observations cache")
        return False


def clear_cache():
    """Clear the weather observations cache (useful for testing)."""
    global _cached_observations, _cache_timestamp
    _cached_observations = None
    _cache_timestamp = None
    logger.info("Weather observations cache cleared")
