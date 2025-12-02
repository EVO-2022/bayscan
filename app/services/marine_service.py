"""Marine forecast and safety data service.

Fetches marine conditions, hazards, and safety information from NWS/NOAA APIs
for Mobile Bay and nearshore Gulf areas.
"""
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Mobile Bay Marine Zone
MARINE_ZONE = "AMZ250"  # Coastal waters from Pensacola FL to Pascagoula MS out 20 NM

# NWS API endpoints
NWS_BASE = "https://api.weather.gov"
MARINE_FORECAST_URL = f"{NWS_BASE}/zones/forecast/{MARINE_ZONE}/forecast"
ALERTS_URL = f"{NWS_BASE}/alerts/active/zone/{MARINE_ZONE}"


def fetch_marine_forecast() -> Optional[Dict[str, Any]]:
    """
    Fetch marine forecast for Mobile Bay zone.

    Returns:
        Dictionary with marine forecast data or None if fetch fails
    """
    try:
        headers = {'User-Agent': 'BayScan Fishing Forecast'}
        response = requests.get(MARINE_FORECAST_URL, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract forecast periods (look for next 12-24 hours)
        periods = data.get('properties', {}).get('periods', [])
        if not periods:
            logger.warning("No forecast periods found in marine forecast")
            return None

        # Get the current/next period
        current_period = periods[0]

        marine_data = {
            'timestamp': datetime.utcnow(),
            'marine_summary': current_period.get('detailedForecast', ''),
            'short_forecast': current_period.get('shortForecast', ''),
            'is_forecast': True
        }

        # Parse wave height from text if available
        wave_height = _extract_wave_height(current_period.get('detailedForecast', ''))
        if wave_height:
            marine_data['wave_height'] = wave_height

        # Parse sea state from text
        sea_state = _extract_sea_state(current_period.get('detailedForecast', ''))
        if sea_state:
            marine_data['sea_state'] = sea_state

        # Wind data
        wind_speed_str = current_period.get('windSpeed', '')
        wind_gust = _extract_wind_gust(wind_speed_str)
        if wind_gust:
            marine_data['wind_gust'] = wind_gust

        logger.info(f"Successfully fetched marine forecast: {marine_data.get('short_forecast')}")
        return marine_data

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching marine forecast: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing marine forecast: {e}")
        return None


def fetch_marine_alerts() -> List[Dict[str, Any]]:
    """
    Fetch active marine alerts and hazards for Mobile Bay zone.

    Returns:
        List of alert dictionaries
    """
    try:
        headers = {'User-Agent': 'BayScan Fishing Forecast'}
        response = requests.get(ALERTS_URL, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        features = data.get('features', [])

        alerts = []
        for feature in features:
            props = feature.get('properties', {})

            alert = {
                'event': props.get('event', ''),
                'headline': props.get('headline', ''),
                'description': props.get('description', ''),
                'severity': props.get('severity', ''),
                'certainty': props.get('certainty', ''),
                'urgency': props.get('urgency', ''),
                'onset': props.get('onset'),
                'expires': props.get('expires')
            }
            alerts.append(alert)

        logger.info(f"Fetched {len(alerts)} active marine alerts")
        return alerts

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching marine alerts: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error parsing marine alerts: {e}")
        return []


def classify_hazards(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Classify alerts into hazard categories.

    Args:
        alerts: List of alert dictionaries from fetch_marine_alerts()

    Returns:
        Dictionary with hazard flags and classification
    """
    hazards = {
        'small_craft_advisory': False,
        'gale_warning': False,
        'thunderstorm_warning': False,
        'hazard_level': 'NONE',  # NONE, CAUTION, DANGEROUS
        'hazard_raw': ''
    }

    if not alerts:
        return hazards

    # Combine all alert headlines/events
    all_text = ' '.join([
        f"{a.get('event', '')} {a.get('headline', '')}"
        for a in alerts
    ]).lower()

    hazards['hazard_raw'] = '; '.join([a.get('headline', '') for a in alerts])

    # Check for specific hazards
    if 'small craft advisory' in all_text:
        hazards['small_craft_advisory'] = True
        hazards['hazard_level'] = 'CAUTION'

    if 'gale warning' in all_text or 'gale watch' in all_text:
        hazards['gale_warning'] = True
        hazards['hazard_level'] = 'DANGEROUS'

    if 'thunderstorm' in all_text or 'severe' in all_text:
        hazards['thunderstorm_warning'] = True
        if hazards['hazard_level'] == 'NONE':
            hazards['hazard_level'] = 'CAUTION'

    # Check for high severity alerts
    for alert in alerts:
        severity = alert.get('severity', '').lower()
        if severity in ['severe', 'extreme']:
            hazards['hazard_level'] = 'DANGEROUS'
            break

    return hazards


def calculate_safety_score(
    marine_data: Dict[str, Any],
    hazards: Dict[str, Any],
    weather_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Calculate safety score (0-100) and safety level.

    Args:
        marine_data: Marine forecast data
        hazards: Hazard classification from classify_hazards()
        weather_data: Optional current weather data for additional context

    Returns:
        Dictionary with safety_score and safety_level
    """
    score = 100  # Start at perfectly safe

    # Deduct for wave height
    wave_height = marine_data.get('wave_height')
    if wave_height:
        if wave_height > 6:
            score -= 50  # Very unsafe
        elif wave_height > 4:
            score -= 30  # Caution
        elif wave_height > 2:
            score -= 15  # Minor concern

    # Deduct for sea state text
    sea_state = marine_data.get('sea_state', '').lower()
    if 'rough' in sea_state or 'very' in sea_state:
        score -= 25
    elif 'choppy' in sea_state or 'moderate' in sea_state:
        score -= 10

    # Deduct for wind gusts
    wind_gust = marine_data.get('wind_gust')
    if wind_gust:
        if wind_gust > 35:
            score -= 40
        elif wind_gust > 25:
            score -= 25
        elif wind_gust > 20:
            score -= 10

    # Deduct for hazards
    if hazards.get('gale_warning'):
        score -= 50
    if hazards.get('small_craft_advisory'):
        score -= 25
    if hazards.get('thunderstorm_warning'):
        score -= 30

    # Additional weather context if available
    if weather_data:
        conditions = weather_data.get('conditions', '').lower()
        if 'storm' in conditions or 'severe' in conditions:
            score -= 20

    # Clamp to 0-100
    score = max(0, min(100, score))

    # Determine safety level
    if score >= 80:
        safety_level = 'SAFE'
    elif score >= 50:
        safety_level = 'CAUTION'
    else:
        safety_level = 'UNSAFE'

    # Override with hazard level if more severe
    if hazards.get('hazard_level') == 'DANGEROUS':
        safety_level = 'UNSAFE'
        score = min(score, 40)
    elif hazards.get('hazard_level') == 'CAUTION' and safety_level == 'SAFE':
        safety_level = 'CAUTION'

    return {
        'safety_score': score,
        'safety_level': safety_level
    }


def get_complete_marine_conditions(weather_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch and combine all marine data into complete conditions object.

    Args:
        weather_data: Optional current weather for additional context

    Returns:
        Complete marine conditions dictionary ready for database
    """
    # Fetch forecast and alerts
    marine_forecast = fetch_marine_forecast()
    alerts = fetch_marine_alerts()

    # Classify hazards
    hazards = classify_hazards(alerts)

    # Calculate safety
    if marine_forecast:
        safety = calculate_safety_score(marine_forecast, hazards, weather_data)
    else:
        # Fallback if forecast unavailable
        safety = {'safety_score': 50, 'safety_level': 'CAUTION'}
        marine_forecast = {
            'timestamp': datetime.utcnow(),
            'marine_summary': 'Marine forecast unavailable',
            'is_forecast': True
        }

    # Combine everything
    complete_data = {
        **marine_forecast,
        **hazards,
        **safety,
        'fetched_at': datetime.utcnow()
    }

    return complete_data


# Helper functions for parsing text-based data

def _extract_wave_height(text: str) -> Optional[float]:
    """Extract wave height in feet from forecast text."""
    import re

    # Look for patterns like "2 to 3 feet", "waves 3 feet", "3 ft"
    patterns = [
        r'waves?\s+(\d+)\s+(?:to\s+\d+\s+)?(?:feet|ft)',
        r'(\d+)\s+(?:to\s+\d+\s+)?(?:feet|ft)\s+waves?',
        r'seas?\s+(\d+)\s+(?:to\s+\d+\s+)?(?:feet|ft)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                continue

    return None


def _extract_sea_state(text: str) -> Optional[str]:
    """Extract sea state description from forecast text."""
    text_lower = text.lower()

    states = [
        'calm', 'light chop', 'choppy', 'moderate', 'rough',
        'very rough', 'high seas', 'smooth'
    ]

    for state in states:
        if state in text_lower:
            return state.title()

    return None


def _extract_wind_gust(wind_speed_str: str) -> Optional[float]:
    """Extract wind gust speed from wind speed string."""
    import re

    # Look for "15 to 20 mph with gusts up to 30 mph"
    gust_match = re.search(r'gusts?\s+(?:up\s+to\s+)?(\d+)\s*mph', wind_speed_str.lower())
    if gust_match:
        try:
            return float(gust_match.group(1))
        except ValueError:
            pass

    # If no explicit gust, look for range and take the high end
    range_match = re.search(r'(\d+)\s+to\s+(\d+)\s*mph', wind_speed_str.lower())
    if range_match:
        try:
            return float(range_match.group(2))
        except ValueError:
            pass

    return None
