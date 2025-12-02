"""Service for computing bite forecasts for time windows."""
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config import config
from app.models.schemas import ForecastWindow, SpeciesForecast, Alert
from app.rules import SPECIES_LIST, get_running_factor, is_species_running, calculate_bite_score, get_bite_label
from app.rules.bite_logic import get_bite_tier, _get_species_environmental_score, _calculate_tide_score, _calculate_wind_score, _calculate_temp_score, clamp
from app.rules.behavior import get_depth_behavior, format_depth_range
from app.rules.conditions_summary import generate_conditions_summary, get_top_active_species
from app.services.tide_service import get_tide_for_time
from app.services.weather_service import get_weather_for_time
from app.services.astronomical_service import get_time_of_day, get_moon_phase
from app.services.watertemp_service import get_water_temperature
from app.services.weather_observations import get_weather_observations
from app.services.advanced_features import (
    get_bite_tier_from_score,
    get_behavior_tier_from_bite_tier,
    predict_water_clarity,
    get_clarity_tip,
    calculate_confidence_score,
    get_rig_of_moment,
    get_best_zones_now,
    get_pro_tip,
    get_current_strength,
    get_moon_tide_window
)
import logging

logger = logging.getLogger(__name__)


def compute_forecasts(db: Session, hours_ahead: int = 24) -> bool:
    """
    Compute bite forecasts for 2-hour windows.

    Args:
        db: Database session
        hours_ahead: Hours ahead to forecast (default 24)

    Returns:
        True if successful, False otherwise
    """
    try:
        now = datetime.utcnow()

        # Round to nearest hour
        start_time = now.replace(minute=0, second=0, microsecond=0)

        # Clear old forecasts (delete individually to trigger cascade)
        end_time = start_time + timedelta(hours=hours_ahead)
        old_windows = db.query(ForecastWindow).filter(
            ForecastWindow.start_time >= start_time,
            ForecastWindow.start_time <= end_time
        ).all()

        for window in old_windows:
            db.delete(window)

        db.commit()

        # Generate 2-hour windows
        windows_created = 0
        for i in range(0, hours_ahead, 2):
            window_start = start_time + timedelta(hours=i)
            window_end = window_start + timedelta(hours=2)
            window_mid = window_start + timedelta(hours=1)

            # Get conditions for the middle of the window
            tide_data = get_tide_for_time(db, window_mid)
            weather_data = get_weather_for_time(db, window_mid)
            time_of_day = get_time_of_day(db, window_mid)
            moon_data = get_moon_phase(db, window_mid.date())

            # Get water temperature from NOAA (cached)
            water_temp_data = get_water_temperature()
            water_temp_f = water_temp_data['water_temp_f'] if water_temp_data else None

            # Build conditions dictionary for scoring
            conditions = {
                'tide_state': tide_data['state'],
                'tide_change_rate': tide_data['change_rate'],
                'time_of_day': time_of_day,
                'wind_speed': weather_data['wind_speed'],
                'wind_direction': weather_data['wind_direction'],
                'temperature': weather_data['temperature'],  # Air temperature
                'water_temperature': water_temp_f,  # Water temperature from NOAA
                'pressure_trend': weather_data['pressure_trend'],
                'cloud_cover': weather_data['cloud_cover'],
                'conditions': weather_data['conditions'],
                'moon_phase': moon_data['phase']
            }

            # Create forecast window
            forecast_window = ForecastWindow(
                start_time=window_start,
                end_time=window_end,
                tide_state=tide_data['state'],
                tide_height_avg=tide_data['height'],
                time_of_day=time_of_day,
                pressure_trend=weather_data['pressure_trend'],
                wind_speed=weather_data['wind_speed'],
                temperature=weather_data['temperature'],  # Air temperature
                water_temperature=water_temp_f,  # Water temperature from NOAA
                conditions_summary=weather_data['conditions'],
                computed_at=datetime.utcnow()
            )

            # Compute per-species forecasts
            species_scores = []
            for species in SPECIES_LIST:
                running_factor = get_running_factor(species, window_mid)
                is_running_bool = is_species_running(species, window_mid)

                bite_score = calculate_bite_score(species, running_factor, conditions)
                bite_label = get_bite_label(bite_score)

                species_forecast = SpeciesForecast(
                    species=species,
                    is_running=is_running_bool,
                    running_factor=running_factor,
                    bite_score=bite_score,
                    bite_label=bite_label
                )

                forecast_window.species_forecasts.append(species_forecast)
                species_scores.append(bite_score)

            # Overall score is average of running species
            running_scores = [s for i, s in enumerate(species_scores)
                            if forecast_window.species_forecasts[i].is_running]
            if running_scores:
                forecast_window.overall_score = sum(running_scores) / len(running_scores)
            else:
                forecast_window.overall_score = sum(species_scores) / len(species_scores)

            db.add(forecast_window)
            windows_created += 1

        db.commit()
        logger.info(f"Computed {windows_created} forecast windows")

        # Update alerts
        _update_alerts(db)

        return True

    except Exception as e:
        logger.error(f"Error computing forecasts: {e}")
        db.rollback()
        return False


def _update_alerts(db: Session):
    """Update alerts based on current forecasts and thresholds."""
    try:
        # Deactivate all existing alerts
        db.query(Alert).filter(Alert.is_active == True).update({'is_active': False})

        # Get alert thresholds from config
        thresholds = config.alert_thresholds

        # Get upcoming forecast windows (next 12 hours)
        now = datetime.utcnow()
        end_time = now + timedelta(hours=12)

        windows = db.query(ForecastWindow).filter(
            ForecastWindow.start_time >= now,
            ForecastWindow.start_time <= end_time
        ).all()

        alerts_created = 0
        for window in windows:
            for species_forecast in window.species_forecasts:
                species = species_forecast.species
                bite_score = species_forecast.bite_score

                # Check if species has a threshold
                threshold = thresholds.get(species)
                if threshold is None:
                    continue

                # Create alert if score exceeds threshold
                if bite_score >= threshold:
                    # Check if we already have an active alert for this species/window
                    existing = db.query(Alert).filter(
                        Alert.species == species,
                        Alert.window_start == window.start_time,
                        Alert.is_active == True
                    ).first()

                    if not existing:
                        from app.rules.seasonality import get_species_display_name
                        species_name = get_species_display_name(species)

                        # Format time for display
                        start_local = window.start_time  # You might want to convert to local timezone
                        end_local = window.end_time

                        message = (
                            f"HOT conditions for {species_name}! "
                            f"Bite score: {bite_score:.0f} ({species_forecast.bite_label}). "
                            f"Window: {start_local.strftime('%I:%M %p')} - {end_local.strftime('%I:%M %p')}"
                        )

                        alert = Alert(
                            species=species,
                            window_start=window.start_time,
                            window_end=window.end_time,
                            bite_score=bite_score,
                            message=message,
                            is_active=True,
                            created_at=datetime.utcnow()
                        )
                        db.add(alert)
                        alerts_created += 1

        db.commit()
        logger.info(f"Created {alerts_created} new alerts")

    except Exception as e:
        logger.error(f"Error updating alerts: {e}")
        db.rollback()


def get_current_conditions(db: Session) -> Dict:
    """
    Get current fishing conditions summary.

    Returns:
        Dictionary with current conditions and bite forecast
    """
    try:
        now = datetime.utcnow()

        # Get current window
        current_window = db.query(ForecastWindow).filter(
            ForecastWindow.start_time <= now,
            ForecastWindow.end_time >= now
        ).first()

        if not current_window:
            # Get nearest future window
            current_window = db.query(ForecastWindow).filter(
                ForecastWindow.start_time >= now
            ).order_by(ForecastWindow.start_time.asc()).first()

        if not current_window:
            return {'error': 'No forecast data available'}

        # Get real-time NOAA observations (air temp, wind, pressure)
        noaa_obs = get_weather_observations()

        # Get weather forecast data for this window
        from app.models.schemas import WeatherData
        weather_data = db.query(WeatherData).filter(
            WeatherData.timestamp <= current_window.end_time,
            WeatherData.timestamp >= current_window.start_time
        ).order_by(WeatherData.timestamp.asc()).first()

        # Use NOAA observations if available, otherwise fall back to forecast weather data
        if noaa_obs:
            air_temp = noaa_obs.get('air_temp_f', current_window.temperature)
            wind_speed = noaa_obs.get('wind_speed_mph', current_window.wind_speed)
            wind_direction = noaa_obs.get('wind_direction_cardinal')
            wind_gust = noaa_obs.get('wind_gust_mph')
            logger.info(f"Using NOAA observations: {air_temp}°F, Wind: {wind_speed} mph {wind_direction}")
        else:
            air_temp = current_window.temperature
            wind_speed = current_window.wind_speed
            wind_direction = None
            wind_gust = None
            logger.info("NOAA observations unavailable, using forecast data")

        # Get wind direction, gust, and cloud cover from WeatherData if not from NOAA
        if weather_data:
            if not wind_direction:
                wind_direction = weather_data.wind_direction
            if not wind_gust:
                wind_gust = weather_data.wind_gust
            cloud_cover = weather_data.cloud_cover
        else:
            cloud_cover = None

        # Build response
        species_list = []
        for sf in current_window.species_forecasts:
            from app.rules.seasonality import get_species_display_name

            # Get bite tier and depth behavior for this species
            bite_tier = get_bite_tier(sf.bite_score)
            depth_behavior = get_depth_behavior(
                sf.species,
                bite_tier,
                wind_direction=wind_direction,
                wind_speed=wind_speed,
                air_temp_f=air_temp,
                water_temp_f=current_window.water_temperature
            )

            # Get UI tier for frontend display
            ui_tier = get_bite_tier_from_score(sf.bite_score)

            species_data = {
                'name': get_species_display_name(sf.species),
                'key': sf.species,
                'is_running': sf.is_running,
                'bite_score': round(sf.bite_score, 1),
                'bite_label': sf.bite_label,
                'bite_tier': bite_tier,
                'tier': ui_tier,  # HOT/DECENT/SLOW/UNLIKELY for frontend
                'running_factor': sf.running_factor
            }

            # Add depth behavior if available
            if depth_behavior:
                species_data['depth'] = depth_behavior['depth']
                species_data['depth_range'] = format_depth_range(depth_behavior['range_ft'])
                species_data['depth_note'] = depth_behavior['note']

            species_list.append(species_data)

        # Sort by bite score descending
        species_list.sort(key=lambda x: x['bite_score'], reverse=True)

        # Get top active species for summary
        top_species = get_top_active_species(species_list, limit=2)

        # Calculate sub-scores for conditions summary
        # We'll use the top species' weights for the summary
        if top_species:
            top_species_key = top_species[0]['key']

            # Get moon phase from database
            from app.models.schemas import AstronomicalData
            moon_phase_value = 0.0
            moon_phase_name = "Unknown"
            today = datetime.utcnow().date()
            astro = db.query(AstronomicalData).filter(
                func.date(AstronomicalData.date) == today
            ).first()
            if astro:
                moon_phase_value = astro.moon_phase or 0.0
                moon_phase_name = astro.moon_phase_name or "Unknown"

            # Build conditions dict for calculating sub-scores (use NOAA obs if available)
            conditions = {
                'tide_state': current_window.tide_state,
                'tide_change_rate': 0.5,  # Default, we don't store this in window
                'time_of_day': current_window.time_of_day,
                'wind_speed': wind_speed,  # From NOAA observations or forecast
                'temperature': air_temp,  # From NOAA observations or forecast
                'water_temperature': current_window.water_temperature,  # Water temperature
                'pressure_trend': current_window.pressure_trend,
                'cloud_cover': cloud_cover or 'partly_cloudy',
                'conditions': current_window.conditions_summary,
                'moon_phase': moon_phase_value
            }

            # Calculate sub-scores for the top species
            tide_score = clamp(_calculate_tide_score(top_species_key, conditions['tide_state'],
                                                       conditions['tide_change_rate'],
                                                       conditions['time_of_day']))
            wind_score = clamp(_calculate_wind_score(top_species_key, wind_speed,
                                                       conditions['conditions']))
            temp_score = clamp(_calculate_temp_score(top_species_key, air_temp,
                                                      current_window.water_temperature))

            # Generate conditions summary
            conditions_summary = generate_conditions_summary(
                tide_score=tide_score,
                wind_score=wind_score,
                temp_score=temp_score,
                bite_score=top_species[0]['bite_score'],
                tide_state=current_window.tide_state,
                wind_speed=wind_speed,
                wind_direction=wind_direction,
                air_temp_f=air_temp,
                water_temp_f=current_window.water_temperature
            )

            # Get depth info for top species
            depth_info = None
            if top_species and 'depth' in top_species[0]:
                depth_info = {
                    'species': top_species[0]['name'],
                    'depth': top_species[0]['depth'],
                    'depth_range': top_species[0]['depth_range'],
                    'note': top_species[0]['depth_note']
                }

            # === ADVANCED FEATURES ===

            # Water clarity
            clarity = predict_water_clarity(
                wind_speed_mph=current_window.wind_speed,
                tide_rate=conditions['tide_change_rate'],
                recent_rain=False  # TODO: integrate rain data if available
            )
            clarity_tip = get_clarity_tip(clarity)

            # Confidence score
            # Simple approximations based on available data
            pressure_stability = 0.8 if current_window.pressure_trend == 'steady' else 0.5
            wind_stability = 0.9 if current_window.wind_speed < 10 else 0.6 if current_window.wind_speed < 15 else 0.3
            tide_predictability = 0.8  # Tides are generally predictable
            confidence = calculate_confidence_score(pressure_stability, wind_stability, tide_predictability)

            # Rig of the moment
            # Parse depth_range if it's a string like "2-4 ft"
            depth_range_str = depth_info.get('depth_range', '3-5 ft') if depth_info else '3-5 ft'
            try:
                parts = depth_range_str.replace(' ft', '').split('-')
                depth_range_tuple = (int(parts[0]), int(parts[1]))
            except:
                depth_range_tuple = (3, 5)

            rig_recommendation = get_rig_of_moment(
                clarity=clarity,
                wind_mph=current_window.wind_speed,
                tide_speed=conditions['tide_change_rate'],
                top_species=top_species_key,
                depth_range=depth_range_tuple,
                time_of_day=current_window.time_of_day
            )

            # Best zones
            # Convert species list to have tier info
            species_with_tiers = []
            for s in species_list[:5]:
                species_with_tiers.append({
                    'key': s['key'],
                    'tier': get_bite_tier_from_score(s['bite_score'])
                })
            best_zones = get_best_zones_now(
                top_species_list=species_with_tiers,
                tide_state=current_window.tide_state,
                clarity=clarity,
                time_of_day=current_window.time_of_day,
                wind_direction=wind_direction,
                wind_speed=wind_speed,
                air_temp_f=air_temp,
                water_temp_f=current_window.water_temperature
            )

            # Pro tip
            top_tier = get_bite_tier_from_score(top_species[0]['bite_score'])
            pro_tip = get_pro_tip(
                bite_tier=top_tier,
                clarity=clarity,
                tide_state=current_window.tide_state,
                wind_mph=current_window.wind_speed,
                time_of_day=current_window.time_of_day
            )

            # Current strength
            current_strength = get_current_strength(conditions['tide_change_rate'])

            # Moon/tide window
            moon_tide_info = get_moon_tide_window(
                moon_phase=moon_phase_name,
                tide_state=current_window.tide_state,
                time_of_day=current_window.time_of_day
            )

        else:
            conditions_summary = "Conditions data unavailable."
            depth_info = None
            clarity = "Lightly Stained"
            clarity_tip = "Balanced visibility."
            confidence = "MEDIUM"
            rig_recommendation = "Use a 1/4oz jig with soft plastic."
            best_zones = [3, 4, 5]
            pro_tip = "Stay persistent and adjust based on what you're seeing."
            current_strength = "Moderate"
            moon_tide_info = "Normal conditions."

        return {
            'window_start': current_window.start_time,
            'window_end': current_window.end_time,
            'overall_score': round(current_window.overall_score, 1),
            'tide_state': current_window.tide_state,
            'tide_height': current_window.tide_height_avg,
            'time_of_day': current_window.time_of_day,
            # Temperature (NOAA observations for air, stored for water)
            'air_temp_f': air_temp,  # Real-time NOAA observation or forecast
            'water_temp_f': current_window.water_temperature,  # NOAA water temp (may be None)
            'temperature': air_temp,  # Kept for backwards compatibility
            # Wind (NOAA observations)
            'wind_speed': wind_speed,  # Real-time NOAA observation or forecast
            'wind_direction': wind_direction,  # NOAA observation (N, NE, E, etc.)
            'wind_gust': wind_gust,  # NOAA observation (may be None)
            'cloud_cover': cloud_cover,  # From forecast (not in NOAA met data)
            # Moon phase
            'moon_phase': moon_phase_name if top_species else "Unknown",
            # Other conditions
            'pressure_trend': current_window.pressure_trend,
            'conditions': current_window.conditions_summary,
            'conditions_summary': conditions_summary,
            'depth_info': depth_info,
            'top_species': [{'name': s['name'], 'key': s['key'], 'bite_score': s['bite_score'],
                            'tier': get_bite_tier_from_score(s['bite_score'])}
                           for s in top_species[:2]] if top_species else [],
            'species': species_list,
            # Advanced features
            'clarity': clarity,
            'clarity_tip': clarity_tip,
            'confidence': confidence,
            'rig_of_moment': rig_recommendation,
            'best_zones': best_zones,
            'pro_tip': pro_tip,
            'current_strength': current_strength,
            'moon_tide_window': moon_tide_info
        }

    except Exception as e:
        logger.error(f"Error getting current conditions: {e}")
        return {'error': str(e)}
