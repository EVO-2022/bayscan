"""Service for fetching weather data from NWS API."""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.config import config
from app.models.schemas import WeatherData
import logging

logger = logging.getLogger(__name__)

# Cache for NWS grid points
_grid_cache = None


def fetch_weather_data(db: Session) -> bool:
    """
    Fetch weather forecast from NWS API and store in database.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get grid point for our location
        grid = _get_grid_point()
        if not grid:
            logger.error("Failed to get NWS grid point")
            return False

        # Fetch hourly forecast
        forecast_url = grid['forecast_hourly_url']
        headers = {'User-Agent': config.weather_user_agent}

        response = requests.get(forecast_url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if 'properties' not in data or 'periods' not in data['properties']:
            logger.error("Invalid forecast response")
            return False

        periods = data['properties']['periods']

        # Clear old forecast data
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=48)
        db.query(WeatherData).filter(
            WeatherData.timestamp >= start_time,
            WeatherData.timestamp <= end_time,
            WeatherData.is_forecast == True
        ).delete()

        # Store forecast periods
        stored_count = 0
        for period in periods[:48]:  # Limit to 48 hours
            try:
                timestamp = datetime.fromisoformat(period['startTime'].replace('Z', '+00:00'))
                timestamp = timestamp.replace(tzinfo=None)  # Convert to naive UTC

                # Parse wind
                wind_speed, wind_direction = _parse_wind(period.get('windSpeed', ''), period.get('windDirection', ''))

                # Determine cloud cover from short forecast
                cloud_cover = _parse_cloud_cover(period.get('shortForecast', ''))

                # Parse conditions
                conditions = period.get('shortForecast', 'Unknown')

                weather_entry = WeatherData(
                    timestamp=timestamp,
                    temperature=period.get('temperature'),
                    wind_speed=wind_speed,
                    wind_direction=wind_direction,
                    wind_gust=None,  # Not always available in hourly
                    pressure=None,  # Not in basic hourly forecast
                    pressure_trend='stable',  # Will compute later
                    humidity=period.get('relativeHumidity', {}).get('value'),
                    cloud_cover=cloud_cover,
                    precipitation_probability=period.get('probabilityOfPrecipitation', {}).get('value'),
                    conditions=conditions,
                    is_forecast=True,
                    fetched_at=datetime.utcnow()
                )
                db.add(weather_entry)
                stored_count += 1

            except Exception as e:
                logger.warning(f"Error parsing weather period: {e}")
                continue

        db.commit()
        logger.info(f"Stored {stored_count} weather forecast periods")

        # Compute pressure trends (if we had obs data, we'd use it)
        _compute_pressure_trends(db)

        return True

    except Exception as e:
        logger.error(f"Error fetching weather data: {e}")
        db.rollback()
        return False


def _get_grid_point() -> Optional[Dict]:
    """Get NWS grid point for our location."""
    global _grid_cache

    if _grid_cache:
        return _grid_cache

    try:
        # Get grid point from lat/lon
        url = f"{config.weather_api_url}/points/{config.latitude},{config.longitude}"
        headers = {'User-Agent': config.weather_user_agent}

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if 'properties' not in data:
            return None

        props = data['properties']
        _grid_cache = {
            'forecast_url': props.get('forecast'),
            'forecast_hourly_url': props.get('forecastHourly'),
            'grid_id': props.get('gridId'),
            'grid_x': props.get('gridX'),
            'grid_y': props.get('gridY')
        }

        return _grid_cache

    except Exception as e:
        logger.error(f"Error getting grid point: {e}")
        return None


def _parse_wind(wind_speed_str: str, wind_direction: str) -> tuple:
    """Parse wind speed string like '10 mph' or '5 to 10 mph'."""
    try:
        if not wind_speed_str:
            return 0.0, wind_direction

        # Remove 'mph' and handle ranges
        speed_str = wind_speed_str.lower().replace('mph', '').strip()

        if 'to' in speed_str:
            # Handle range like "5 to 10"
            parts = speed_str.split('to')
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            speed = (low + high) / 2
        else:
            speed = float(speed_str)

        return speed, wind_direction

    except Exception:
        return 0.0, wind_direction


def _parse_cloud_cover(short_forecast: str) -> str:
    """Determine cloud cover from short forecast text."""
    forecast_lower = short_forecast.lower()

    if any(word in forecast_lower for word in ['sunny', 'clear']):
        return 'clear'
    elif any(word in forecast_lower for word in ['partly', 'mostly sunny', 'mostly clear']):
        return 'partly_cloudy'
    elif any(word in forecast_lower for word in ['cloudy', 'overcast']):
        return 'overcast'
    else:
        return 'partly_cloudy'  # default


def _compute_pressure_trends(db: Session):
    """
    Compute pressure trends from forecast data.
    Note: NWS hourly doesn't include pressure, so we'd need observations.
    For now, we'll leave trends as 'stable' or infer from conditions.
    """
    # This is a simplified version - in production you'd fetch observation data
    # from NOAA or another source for actual pressure readings
    try:
        forecasts = db.query(WeatherData).filter(
            WeatherData.is_forecast == True
        ).order_by(WeatherData.timestamp.asc()).all()

        for i, forecast in enumerate(forecasts):
            # Infer trend from conditions
            conditions_lower = forecast.conditions.lower() if forecast.conditions else ''

            # Falling pressure indicators
            if any(word in conditions_lower for word in ['storm', 'approaching', 'deteriorating']):
                forecast.pressure_trend = 'falling'
            # Rising pressure indicators
            elif any(word in conditions_lower for word in ['clearing', 'improving']):
                forecast.pressure_trend = 'rising'
            else:
                forecast.pressure_trend = 'stable'

        db.commit()

    except Exception as e:
        logger.error(f"Error computing pressure trends: {e}")


def get_pressure_trend(db: Session, target_time: datetime = None) -> str:
    """
    Get pressure trend for a specific time.

    Returns:
        'rising', 'falling', or 'stable'
    """
    if target_time is None:
        target_time = datetime.utcnow()

    try:
        weather = db.query(WeatherData).filter(
            WeatherData.timestamp >= target_time,
            WeatherData.is_forecast == True
        ).order_by(WeatherData.timestamp.asc()).first()

        if weather:
            return weather.pressure_trend

        return 'stable'

    except Exception as e:
        logger.error(f"Error getting pressure trend: {e}")
        return 'stable'


def get_weather_for_time(db: Session, target_time: datetime) -> Dict:
    """
    Get weather conditions for a specific time.

    Returns:
        Dictionary with weather data
    """
    try:
        # Get closest forecast
        weather = db.query(WeatherData).filter(
            WeatherData.timestamp >= target_time,
            WeatherData.is_forecast == True
        ).order_by(WeatherData.timestamp.asc()).first()

        if not weather:
            # Try getting most recent
            weather = db.query(WeatherData).filter(
                WeatherData.is_forecast == True
            ).order_by(WeatherData.timestamp.desc()).first()

        if not weather:
            return {
                'temperature': 70.0,
                'wind_speed': 5.0,
                'wind_direction': 'Variable',
                'pressure_trend': 'stable',
                'cloud_cover': 'clear',
                'conditions': 'Unknown',
                'precipitation_probability': 0
            }

        return {
            'temperature': weather.temperature or 70.0,
            'wind_speed': weather.wind_speed or 5.0,
            'wind_direction': weather.wind_direction or 'Variable',
            'pressure_trend': weather.pressure_trend or 'stable',
            'cloud_cover': weather.cloud_cover or 'clear',
            'conditions': weather.conditions or 'Unknown',
            'precipitation_probability': weather.precipitation_probability or 0
        }

    except Exception as e:
        logger.error(f"Error getting weather for time {target_time}: {e}")
        return {
            'temperature': 70.0,
            'wind_speed': 5.0,
            'wind_direction': 'Variable',
            'pressure_trend': 'stable',
            'cloud_cover': 'clear',
            'conditions': 'Unknown',
            'precipitation_probability': 0
        }
