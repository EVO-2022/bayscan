"""Service for fetching tide data from NOAA CO-OPS API."""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from app.config import config
from app.models.schemas import TideData
from app.utils.timezone import get_central_isoformat
from app.utils.location_manager import get_current_location
from app.utils.location_registry import get_location
import logging

logger = logging.getLogger(__name__)


def _get_tide_station_id() -> str:
    """
    Get the tide prediction station ID for the current location.
    
    Reads from the location registry based on current active location.
    Falls back to config.tide_station_id if location has no station configured.
    
    Returns:
        NOAA station ID string (e.g., "8735180")
    """
    try:
        location_id = get_current_location()
        location_data = get_location(location_id)
        
        if location_data:
            noaa_config = location_data.get("noaa", {})
            station_id = noaa_config.get("tide_prediction_station")
            if station_id:
                return station_id
    except Exception as e:
        logger.warning(f"Error reading location tide station, using default: {e}")
    
    # Fallback to config.yaml setting
    return config.tide_station_id


def fetch_tide_data(db: Session, hours_ahead: int = 48) -> bool:
    """
    Fetch tide predictions from NOAA CO-OPS API and store in database.

    Args:
        db: Database session
        hours_ahead: Hours of tide data to fetch (default 48)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Fetch predictions
        predictions = _fetch_predictions(hours_ahead)
        if not predictions:
            logger.error("No tide predictions received")
            return False

        # Fetch high/low tide times
        hi_low = _fetch_high_low_tides(hours_ahead)

        # Clear old predictions for the time range
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=hours_ahead)
        db.query(TideData).filter(
            TideData.timestamp >= start_time,
            TideData.timestamp <= end_time,
            TideData.is_prediction == True
        ).delete()

        # Store predictions
        for pred in predictions:
            tide_entry = TideData(
                timestamp=pred['timestamp'],
                height=pred['height'],
                is_prediction=True,
                tide_type=None,
                fetched_at=datetime.utcnow()
            )
            db.add(tide_entry)

        # Store high/low markers
        for hl in hi_low:
            # Check if we already have this exact time
            existing = db.query(TideData).filter(
                TideData.timestamp == hl['timestamp'],
                TideData.is_prediction == True
            ).first()

            if existing:
                existing.tide_type = hl['type']
            else:
                tide_entry = TideData(
                    timestamp=hl['timestamp'],
                    height=hl['height'],
                    is_prediction=True,
                    tide_type=hl['type'],
                    fetched_at=datetime.utcnow()
                )
                db.add(tide_entry)

        db.commit()
        logger.info(f"Stored {len(predictions)} tide predictions and {len(hi_low)} high/low markers")
        return True

    except Exception as e:
        logger.error(f"Error fetching tide data: {e}")
        db.rollback()
        return False


def _fetch_predictions(hours_ahead: int) -> List[Dict]:
    """Fetch tide height predictions from NOAA."""
    try:
        begin_date = datetime.utcnow().strftime('%Y%m%d %H:%M')
        end_date = (datetime.utcnow() + timedelta(hours=hours_ahead)).strftime('%Y%m%d %H:%M')

        params = {
            'station': _get_tide_station_id(),
            'begin_date': begin_date,
            'end_date': end_date,
            'product': 'predictions',
            'datum': 'MLLW',  # Mean Lower Low Water
            'time_zone': 'gmt',
            'units': 'english',
            'interval': '6',  # 6-minute intervals
            'format': 'json'
        }

        response = requests.get(config.tide_api_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if 'predictions' not in data:
            logger.error(f"No predictions in response: {data}")
            return []

        predictions = []
        for item in data['predictions']:
            predictions.append({
                'timestamp': datetime.strptime(item['t'], '%Y-%m-%d %H:%M'),
                'height': float(item['v'])
            })

        return predictions

    except Exception as e:
        logger.error(f"Error fetching tide predictions: {e}")
        return []


def _fetch_high_low_tides(hours_ahead: int) -> List[Dict]:
    """Fetch high and low tide times from NOAA."""
    try:
        begin_date = datetime.utcnow().strftime('%Y%m%d')
        end_date = (datetime.utcnow() + timedelta(hours=hours_ahead)).strftime('%Y%m%d')

        params = {
            'station': _get_tide_station_id(),
            'begin_date': begin_date,
            'end_date': end_date,
            'product': 'predictions',
            'datum': 'MLLW',
            'time_zone': 'gmt',
            'units': 'english',
            'interval': 'hilo',  # High/low only
            'format': 'json'
        }

        response = requests.get(config.tide_api_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if 'predictions' not in data:
            return []

        hi_low = []
        for item in data['predictions']:
            hi_low.append({
                'timestamp': datetime.strptime(item['t'], '%Y-%m-%d %H:%M'),
                'height': float(item['v']),
                'type': item['type']  # 'H' or 'L'
            })

        return hi_low

    except Exception as e:
        logger.error(f"Error fetching high/low tides: {e}")
        return []


def get_tide_state_for_timestamp(db: Session, timestamp: datetime) -> Dict:
    """
    Get tide state for a specific timestamp: height, direction, and state.

    Args:
        db: Database session
        timestamp: The datetime to get tide state for

    Returns:
        Dictionary with tide state information
    """
    try:
        # Get recent tide data points to determine trend
        recent_tides = db.query(TideData).filter(
            TideData.timestamp <= timestamp,
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.desc()).limit(3).all()

        # Get upcoming tide data
        upcoming_tides = db.query(TideData).filter(
            TideData.timestamp >= timestamp,
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.asc()).limit(3).all()

        if not recent_tides and not upcoming_tides:
            return {
                'tide_height': None,
                'tide_stage': 'unknown'
            }

        # Interpolate tide height
        if recent_tides and upcoming_tides:
            before = recent_tides[0]
            after = upcoming_tides[0]
            time_diff = (after.timestamp - before.timestamp).total_seconds()
            time_since = (timestamp - before.timestamp).total_seconds()
            if time_diff > 0:
                ratio = time_since / time_diff
                tide_height = before.height + (after.height - before.height) * ratio
            else:
                tide_height = before.height
        elif recent_tides:
            tide_height = recent_tides[0].height
        else:
            tide_height = upcoming_tides[0].height

        # Determine if rising or falling
        tide_stage = 'slack'
        if len(recent_tides) >= 1 and len(upcoming_tides) >= 1:
            before = recent_tides[0]
            after = upcoming_tides[0]
            height_change = after.height - before.height
            if height_change > 0.01:
                tide_stage = 'incoming'
            elif height_change < -0.01:
                tide_stage = 'outgoing'

        return {
            'tide_height': round(tide_height, 2),
            'tide_stage': tide_stage
        }

    except Exception as e:
        logger.error(f"Error getting tide state for timestamp: {e}")
        return {
            'tide_height': None,
            'tide_stage': 'unknown'
        }


def get_current_tide_state(db: Session) -> Dict:
    """
    Get current tide state: height, direction, and next high/low.

    Returns:
        Dictionary with tide state information
    """
    try:
        now = datetime.utcnow()

        # Get recent tide data points to determine trend
        recent_tides = db.query(TideData).filter(
            TideData.timestamp <= now,
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.desc()).limit(3).all()

        # Get upcoming tide data
        upcoming_tides = db.query(TideData).filter(
            TideData.timestamp >= now,
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.asc()).limit(3).all()

        if not recent_tides and not upcoming_tides:
            return {
                'current_height': None,
                'state': 'unknown',
                'change_rate': 0.0,
                'next_high': None,
                'next_low': None
            }

        # Interpolate current height
        if recent_tides and upcoming_tides:
            before = recent_tides[0]
            after = upcoming_tides[0]
            time_diff = (after.timestamp - before.timestamp).total_seconds()
            time_since = (now - before.timestamp).total_seconds()
            if time_diff > 0:
                ratio = time_since / time_diff
                current_height = before.height + (after.height - before.height) * ratio
            else:
                current_height = before.height
        elif recent_tides:
            current_height = recent_tides[0].height
        else:
            current_height = upcoming_tides[0].height

        # Determine if rising or falling
        # Compare points before and after current time for better trend detection
        state = 'slack'
        change_rate = 0.0
        if len(recent_tides) >= 1 and len(upcoming_tides) >= 1:
            before = recent_tides[0]
            after = upcoming_tides[0]
            height_change = after.height - before.height
            time_change = (after.timestamp - before.timestamp).total_seconds() / 3600  # hours
            if time_change > 0:
                change_rate = abs(height_change / time_change)  # feet per hour
                # Lower threshold since we're looking at 6-12 minute intervals
                if height_change > 0.01:
                    state = 'rising'
                elif height_change < -0.01:
                    state = 'falling'

        # Normalize change rate to 0-1 scale (assume max 2 ft/hr)
        change_rate_normalized = min(change_rate / 2.0, 1.0)

        # Get next high and low
        next_high = db.query(TideData).filter(
            TideData.timestamp >= now,
            TideData.tide_type == 'H'
        ).order_by(TideData.timestamp.asc()).first()

        next_low = db.query(TideData).filter(
            TideData.timestamp >= now,
            TideData.tide_type == 'L'
        ).order_by(TideData.timestamp.asc()).first()

        return {
            'current_height': round(current_height, 2),
            'state': state,
            'change_rate': change_rate_normalized,
            'next_high': {
                'time': get_central_isoformat(next_high.timestamp),
                'height': next_high.height
            } if next_high else None,
            'next_low': {
                'time': get_central_isoformat(next_low.timestamp),
                'height': next_low.height
            } if next_low else None
        }

    except Exception as e:
        logger.error(f"Error getting current tide state: {e}")
        return {
            'current_height': None,
            'state': 'unknown',
            'change_rate': 0.0,
            'next_high': None,
            'next_low': None
        }


def get_tide_for_time(db: Session, target_time: datetime) -> Dict:
    """
    Get tide state for a specific time.

    Returns:
        Dictionary with tide height and state
    """
    try:
        # Get tide data around the target time
        before = db.query(TideData).filter(
            TideData.timestamp <= target_time,
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.desc()).first()

        after = db.query(TideData).filter(
            TideData.timestamp >= target_time,
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.asc()).first()

        if not before or not after:
            return {'height': None, 'state': 'unknown', 'change_rate': 0.0}

        # Interpolate height
        time_diff = (after.timestamp - before.timestamp).total_seconds()
        time_since = (target_time - before.timestamp).total_seconds()
        if time_diff > 0:
            ratio = time_since / time_diff
            height = before.height + (after.height - before.height) * ratio
        else:
            height = before.height

        # Determine state
        # For better accuracy, look at wider time window (±30 min from target)
        before_wide = db.query(TideData).filter(
            TideData.timestamp <= target_time - timedelta(minutes=30),
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.desc()).first()

        after_wide = db.query(TideData).filter(
            TideData.timestamp >= target_time + timedelta(minutes=30),
            TideData.is_prediction == True
        ).order_by(TideData.timestamp.asc()).first()

        # Use wider window if available, otherwise use immediate before/after
        before_compare = before_wide if before_wide else before
        after_compare = after_wide if after_wide else after

        height_change = after_compare.height - before_compare.height
        time_diff_compare = (after_compare.timestamp - before_compare.timestamp).total_seconds()
        change_rate = abs(height_change / (time_diff_compare / 3600)) if time_diff_compare > 0 else 0.0
        change_rate_normalized = min(change_rate / 2.0, 1.0)

        # Lower threshold since Mobile Bay has smaller tidal range
        if height_change > 0.02:
            state = 'rising'
        elif height_change < -0.02:
            state = 'falling'
        else:
            state = 'slack'

        return {
            'height': round(height, 2),
            'state': state,
            'change_rate': change_rate_normalized
        }

    except Exception as e:
        logger.error(f"Error getting tide for time {target_time}: {e}")
        return {'height': None, 'state': 'unknown', 'change_rate': 0.0}
