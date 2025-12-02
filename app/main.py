"""BayScan - Main FastAPI application for fishing forecast."""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging
from pathlib import Path

from app.database import get_db, init_db
from app.config import config
from app.scheduler import start_scheduler, stop_scheduler
from app.models.schemas import ForecastWindow, Alert, Catch, WeatherData, TideData, BaitLog, PredatorLog, LearningBucket
from app.services.tide_service import get_current_tide_state
from app.services.scoring_service import get_current_conditions
from app.services.advanced_features import get_bite_tier_from_score, get_species_behavior_cheatsheet
from app.rules.seasonality import get_species_display_name
from app.rules.regulations import get_regulations
# Bait scoring imports moved to function level to avoid circular imports
from app.rules.bait_profiles import BAIT_PROFILES, get_bait_display_name
from app.utils.timezone import get_central_isoformat, central_to_utc, central_now
from app.services.learning_service import get_learning_delta, get_zone_data_sufficiency

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response
class CatchCreate(BaseModel):
    """Request model for logging a catch - NEW HYPERLOCAL SPEC."""
    species: str
    zone_id: str  # NEW - Required (Zone 1-5)
    distance_from_dock: Optional[str] = None  # NEW - at dock, 50-100 ft, 100-150 ft, 150+ ft
    depth_estimate: Optional[str] = None  # NEW - shallow, medium, deep
    structure_type: Optional[str] = None  # NEW - pilings, grass edge, open water, channel edge
    size_length_in: Optional[int] = None
    size_bucket: Optional[str] = None
    quantity: Optional[int] = 1
    bait_used: Optional[str] = None  # RENAMED from bait_type
    presentation: Optional[str] = None  # RENAMED from method (jig, cork, carolina, free-lined)
    predator_seen_recently: bool = False  # NEW - predator flag
    kept: bool = False
    notes: Optional[str] = None
    days_since_last_checked: Optional[int] = None  # For traps - days between setting and checking
    timestamp: Optional[datetime] = None  # If not provided, uses current time

    class Config:
        json_schema_extra = {
            "example": {
                "species": "speckled_trout",
                "zone_id": "Zone 3",
                "distance_from_dock": "at dock",
                "depth_estimate": "shallow",
                "structure_type": "pilings",
                "size_length_in": 16,
                "size_bucket": "keeper",
                "quantity": 1,
                "bait_used": "live shrimp",
                "presentation": "jig",
                "predator_seen_recently": False,
                "kept": True,
                "notes": "Caught on incoming tide"
            }
        }


class BaitLogCreate(BaseModel):
    """Request model for logging bait caught - NEW HYPERLOCAL SPEC."""
    bait_species: str  # shrimp, menhaden, mullet, fiddler, pinfish
    method: str  # REQUIRED - cast net, trap
    zone_id: str  # NEW - Required (Zone 1-5)
    quantity_estimate: Optional[str] = None  # NEW - none, few, plenty
    structure_type: Optional[str] = None  # NEW - pilings, grass edge, open water, channel edge
    notes: Optional[str] = None
    days_since_last_checked: Optional[int] = None  # For traps - days between setting and checking
    timestamp: Optional[datetime] = None  # If not provided, uses current time

    class Config:
        json_schema_extra = {
            "example": {
                "bait_species": "live_shrimp",
                "method": "cast net",
                "zone_id": "Zone 3",
                "quantity_estimate": "plenty",
                "structure_type": "pilings",
                "notes": "Near dock pilings"
            }
        }


class PredatorLogCreate(BaseModel):
    """Request model for logging predator sighting."""
    predator: str
    zone: str
    time: Optional[datetime] = None
    behavior: str
    tide: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "predator": "dolphin",
                "zone": "Zone 4",
                "behavior": "feeding",
                "tide": "rising",
                "notes": "Pod of 3 dolphins"
            }
        }


# Create FastAPI app
app = FastAPI(
    title="BayScan API",
    description="Smart fishing forecasts for Mobile Bay - predicts best fishing times based on tide, weather, and seasonal patterns",
    version="1.0.0"
)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on startup."""
    logger.info("Starting BayScan application...")
    init_db()
    logger.info("Database initialized")
    start_scheduler()
    logger.info("BayScan started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown."""
    logger.info("Shutting down application...")
    stop_scheduler()
    logger.info("Application shut down")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main dashboard HTML."""
    template_path = Path(__file__).parent / "templates" / "index.html"
    with open(template_path, 'r') as f:
        return f.read()


@app.get("/api/current")
async def get_current(db: Session = Depends(get_db)) -> Dict:
    """
    Get current fishing conditions.

    Returns current bite scores, tide state, weather, and species forecasts.
    """
    try:
        conditions = get_current_conditions(db)
        tide_state = get_current_tide_state(db)

        # Add tide details
        conditions['tide_details'] = tide_state

        return conditions
    except Exception as e:
        logger.error(f"Error getting current conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/zone-bite-scores")
async def get_zone_bite_scores(
    species: str,
    zone_id: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get detailed zone-specific bite score for a species - READS FROM CACHE.

    Args:
        species: Species key (e.g., 'speckled_trout')
        zone_id: Zone identifier (e.g., 'Zone 3')

    Returns:
        Cached bite score with rating, confidence, reason, and tip
    """
    try:
        from app.services.score_cache_service import get_cached_bite_score, recalculate_bite_score
        from app.services.tip_generation_service import get_tip_for_zone

        # Get cached score
        cached = get_cached_bite_score(db, species, zone_id)

        # If not cached yet, calculate it now
        if not cached:
            logger.info(f"No cached score for {species} {zone_id}, calculating now...")
            recalculate_bite_score(db, species, zone_id)
            cached = get_cached_bite_score(db, species, zone_id)

        if not cached:
            raise HTTPException(status_code=404, detail=f"Unable to calculate score for {species} in {zone_id}")

        # Get tip if available
        tip = get_tip_for_zone(db, species, zone_id)

        # Build response
        result = {
            'species': species,
            'species_name': get_species_display_name(species),
            'zone_id': zone_id,
            'bite_score': cached['score'],
            'rating': cached['rating'],
            'confidence': cached['confidence'],
            'reason_summary': cached['reason_summary'],
            'tip': tip,
            'last_updated': cached['last_updated'].isoformat() if cached.get('last_updated') else None,
            'data_source': 'cached'
        }

        return result

    except Exception as e:
        logger.error(f"Error calculating zone bite score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast")
async def get_forecast(hours: int = 24, db: Session = Depends(get_db)) -> List[Dict]:
    """
    Get upcoming forecast windows.

    Args:
        hours: Number of hours ahead to forecast (default 24, max 48)

    Returns:
        List of forecast windows with bite scores per species
    """
    try:
        hours = min(hours, 48)  # Cap at 48 hours
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)

        windows = db.query(ForecastWindow).filter(
            ForecastWindow.start_time >= now,
            ForecastWindow.start_time <= end_time
        ).order_by(ForecastWindow.start_time.asc()).all()

        result = []
        for window in windows:
            species_data = []
            for sf in window.species_forecasts:
                tier = get_bite_tier_from_score(sf.bite_score)
                species_data.append({
                    'name': get_species_display_name(sf.species),
                    'key': sf.species,
                    'is_running': sf.is_running,
                    'bite_score': round(sf.bite_score, 1),  # Keep for sorting
                    'bite_label': sf.bite_label,
                    'tier': tier  # Add tier for UI display
                })

            # Sort by bite score
            species_data.sort(key=lambda x: x['bite_score'], reverse=True)

            # Get overall tier for this window based on top 3 species (not all species average)
            # This reflects what's actually biting well, not the average of everything
            if species_data:
                top_3_scores = [sp['bite_score'] for sp in species_data[:3]]
                top_3_avg = sum(top_3_scores) / len(top_3_scores)
                overall_tier = get_bite_tier_from_score(top_3_avg)
            else:
                overall_tier = "SLOW"

            result.append({
                'start_time': get_central_isoformat(window.start_time),
                'end_time': get_central_isoformat(window.end_time),
                'overall_score': round(window.overall_score, 1),
                'overall_tier': overall_tier,  # Add tier for window
                'tide_state': window.tide_state,
                'tide_height': window.tide_height_avg,
                'time_of_day': window.time_of_day,
                'temperature': window.temperature,
                'wind_speed': window.wind_speed,
                'pressure_trend': window.pressure_trend,
                'conditions': window.conditions_summary,
                'species': species_data,
                'top_species': species_data[:3]  # Top 3 species for this window
            })

        return result

    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hourly-outlook")
async def get_hourly_outlook(hours: int = 12, db: Session = Depends(get_db)) -> List[Dict]:
    """
    Get hourly bite tier outlook for the next N hours.

    Args:
        hours: Number of hours ahead (default 12, max 24)

    Returns:
        List of hourly forecasts with tier and conditions
    """
    try:
        hours = min(hours, 24)  # Cap at 24 hours
        now = datetime.utcnow()

        # Get forecast windows
        end_time = now + timedelta(hours=hours)
        windows = db.query(ForecastWindow).filter(
            ForecastWindow.start_time >= now,
            ForecastWindow.start_time <= end_time
        ).order_by(ForecastWindow.start_time.asc()).all()

        hourly_data = []
        for window in windows:
            # Get top species bite score for this window
            top_bite_score = window.overall_score
            if window.species_forecasts:
                scores = [sf.bite_score for sf in window.species_forecasts]
                top_bite_score = max(scores) if scores else window.overall_score

            tier = get_bite_tier_from_score(top_bite_score)

            # Create entries for each hour in this 2-hour window
            hour_start = window.start_time
            hour_end = window.end_time
            current_hour = hour_start

            while current_hour < hour_end:
                hourly_data.append({
                    'hour': get_central_isoformat(current_hour),
                    'tier': tier,
                    'bite_score': round(top_bite_score, 1),
                    'tide_state': window.tide_state,
                    'temperature': window.temperature,
                    'wind_speed': window.wind_speed,
                    'time_of_day': window.time_of_day
                })
                current_hour += timedelta(hours=1)

        # Limit to requested hours
        return hourly_data[:hours]

    except Exception as e:
        logger.error(f"Error getting hourly outlook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts")
async def get_alerts(db: Session = Depends(get_db)) -> List[Dict]:
    """
    Get active fishing alerts.

    Returns list of species and time windows with hot bite conditions.
    """
    try:
        now = datetime.utcnow()

        alerts = db.query(Alert).filter(
            Alert.is_active == True,
            Alert.window_end >= now
        ).order_by(Alert.window_start.asc()).all()

        result = []
        for alert in alerts:
            result.append({
                'species': get_species_display_name(alert.species),
                'species_key': alert.species,
                'window_start': get_central_isoformat(alert.window_start),
                'window_end': get_central_isoformat(alert.window_end),
                'bite_score': round(alert.bite_score, 1),
                'message': alert.message,
                'created_at': get_central_isoformat(alert.created_at)
            })

        return result

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tide")
async def get_tide(db: Session = Depends(get_db)) -> Dict:
    """
    Get current tide information and upcoming high/low tides.
    """
    try:
        tide_state = get_current_tide_state(db)
        return tide_state
    except Exception as e:
        logger.error(f"Error getting tide info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/species/{species_key}")
async def get_species_forecast(
    species_key: str,
    hours: int = 24,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get detailed forecast for a specific species.

    Args:
        species_key: Species identifier (e.g., 'speckled_trout', 'redfish')
        hours: Hours ahead to forecast (default 24)

    Returns:
        Detailed forecast for the species
    """
    try:
        now = datetime.utcnow()
        end_time = now + timedelta(hours=hours)

        windows = db.query(ForecastWindow).filter(
            ForecastWindow.start_time >= now,
            ForecastWindow.start_time <= end_time
        ).order_by(ForecastWindow.start_time.asc()).all()

        forecast_periods = []
        for window in windows:
            # Find species forecast in this window
            sf = next((s for s in window.species_forecasts if s.species == species_key), None)
            if sf:
                forecast_periods.append({
                    'start_time': get_central_isoformat(window.start_time),
                    'end_time': get_central_isoformat(window.end_time),
                    'bite_score': round(sf.bite_score, 1),
                    'bite_label': sf.bite_label,
                    'is_running': sf.is_running,
                    'running_factor': sf.running_factor,
                    'tide_state': window.tide_state,
                    'time_of_day': window.time_of_day,
                    'temperature': window.temperature,
                    'conditions': window.conditions_summary
                })

        # Get regulations for this species
        regulations = get_regulations(species_key)

        # Get behavior cheat sheet data with CURRENT CONDITIONS for dynamic zones/depth
        from app.services.scoring_service import get_current_conditions
        current_data = get_current_conditions(db)

        # Get current bite tier for this species
        current_species = next((s for s in current_data.get('species', []) if s['key'] == species_key), None)
        current_bite_tier = current_species.get('tier', 'SLOW') if current_species else 'SLOW'

        # Get static behavior data
        behavior_data = get_species_behavior_cheatsheet(species_key)

        # Make zones dynamic based on CURRENT conditions
        from app.services.advanced_features import get_best_zones_now
        top_species_for_zones = [{'key': species_key, 'tier': current_bite_tier}]
        dynamic_zones = get_best_zones_now(
            top_species_list=top_species_for_zones,
            tide_state=current_data.get('tide_state', 'unknown'),
            clarity=current_data.get('clarity', 'Clear')
        )
        behavior_data['best_zones'] = dynamic_zones

        # Make depth dynamic - only show the CURRENT tier's depth
        from app.rules.behavior import get_depth_behavior, format_depth_range
        from app.services.advanced_features import get_behavior_tier_from_bite_tier
        behavior_tier = get_behavior_tier_from_bite_tier(current_bite_tier)
        current_depth = get_depth_behavior(species_key, behavior_tier)

        if current_depth:
            behavior_data['best_depth'] = {
                'current': {
                    'depth': current_depth['depth'],
                    'range': format_depth_range(current_depth['range_ft']),
                    'note': current_depth['note'],
                    'tier': current_bite_tier
                }
            }

        return {
            'species': get_species_display_name(species_key),
            'species_key': species_key,
            'size_limit': regulations['size_display'],
            'creel_limit': regulations['creel_display'],
            'regulations': regulations['regulations'],
            'forecast': forecast_periods,
            'behavior': behavior_data
        }

    except Exception as e:
        logger.error(f"Error getting species forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bait-forecast")
async def get_bait_forecast(db: Session = Depends(get_db)) -> Dict:
    """
    Get current bait activity forecast for all bait species - BEHAVIOR SPEC.

    Returns sorted list of bait species with activity scores, tiers, and details.
    Uses new bait scoring formula with zone-specific ratings.
    """
    try:
        from app.services.bait_scoring import get_bait_forecast_all_zones
        from app.services.environment_snapshot import get_latest_snapshot, get_snapshot_as_dict

        # Get latest environment snapshot
        snapshot = get_latest_snapshot(db)
        conditions = get_snapshot_as_dict(snapshot) if snapshot else {}

        # If no snapshot, get basic conditions from current forecast
        if not conditions:
            current_data = get_current_conditions(db)
            conditions = {
                'water_temperature': current_data.get('water_temp_f'),
                'tide_stage': current_data.get('tide_state'),
                'wind_speed': current_data.get('wind_speed'),
                'wind_direction': current_data.get('wind_direction'),
                'time_of_day': current_data.get('time_of_day'),
                'water_clarity': current_data.get('clarity', '').lower().replace(' ', '_'),
                'current_speed': current_data.get('tide_rate', 0) * 0.5,  # Approximate
            }

        # Calculate bait forecasts using new formula
        bait_forecasts = get_bait_forecast_all_zones(db, conditions)

        return {
            'bait_forecasts': bait_forecasts,
            'conditions': {
                'tide_stage': conditions.get('tide_stage', 'unknown'),
                'clarity': conditions.get('water_clarity', 'unknown'),
                'time_of_day': conditions.get('time_of_day', 'unknown'),
                'wind_speed': conditions.get('wind_speed', 0),
                'water_temp': conditions.get('water_temperature', 0)
            },
            'updated_at': get_central_isoformat(datetime.utcnow())
        }

    except Exception as e:
        logger.error(f"Error getting bait forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bait/{bait_key}")
async def get_bait_detail(bait_key: str, db: Session = Depends(get_db)) -> Dict:
    """
    Get detailed information for a specific bait species.

    Args:
        bait_key: Bait identifier (e.g., 'live_shrimp', 'finger_mullet')

    Returns:
        Detailed bait profile with current activity score
    """
    try:
        # Get bait profile
        profile = BAIT_PROFILES.get(bait_key)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Bait species '{bait_key}' not found")

        # Get current conditions for activity score
        from app.services.bait_scoring import calculate_bait_rating
        from app.services.environment_snapshot import get_latest_snapshot, get_snapshot_as_dict

        # Get environment snapshot
        snapshot = get_latest_snapshot(db)
        conditions = get_snapshot_as_dict(snapshot) if snapshot else {}

        # Get current conditions for UI display (always needed)
        current_data = get_current_conditions(db)

        # If no snapshot, build conditions from current_data
        if not conditions:
            conditions = {
                'water_temperature': current_data.get('water_temp_f'),
                'tide_stage': current_data.get('tide_state'),
                'wind_speed': current_data.get('wind_speed'),
                'wind_direction': current_data.get('wind_direction'),
                'time_of_day': current_data.get('time_of_day'),
                'water_clarity': current_data.get('clarity', '').lower().replace(' ', '_'),
                'current_speed': current_data.get('tide_rate', 0) * 0.5,
            }

        # Calculate rating across all zones and use best
        zone_ratings = []
        for zone_num in [1, 2, 3, 4, 5]:
            zone_id = f"Zone {zone_num}"
            rating = calculate_bait_rating(db, bait_key, zone_id, conditions)
            zone_ratings.append(rating)

        # Use best zone rating
        best_rating = max(zone_ratings, key=lambda x: x['rating'])
        activity_score = best_rating['rating']
        tier = best_rating['tier_label']

        return {
            'bait_key': bait_key,
            'display_name': get_bait_display_name(bait_key),
            'current_activity_score': round(activity_score, 1),
            'current_tier': tier,
            'description': profile.get('description', ''),
            'zones': profile.get('zones', []),
            'zone_notes': profile.get('zone_notes', ''),
            'tide_preference': profile.get('tide_preference', ''),
            'time_preference': profile.get('time_preference', ''),
            'clarity_notes': profile.get('clarity_notes', ''),
            'methods': profile.get('methods', []),
            'how_to_catch': profile.get('how_to_catch', []),
            'best_for': profile.get('best_for', []),
            'tips': profile.get('tips', []),
            'conditions': {
                'tide_state': current_data.get('tide_state'),
                'clarity': current_data.get('clarity'),
                'time_of_day': current_data.get('time_of_day')
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bait detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/catches")
async def log_catch(catch_data: CatchCreate, db: Session = Depends(get_db)) -> Dict:
    """
    Log a new catch to the fishing log - NEW HYPERLOCAL SPEC.

    Captures full environment snapshot with all new fields.
    """
    try:
        from app.services.environment_snapshot import get_latest_snapshot, get_snapshot_as_dict
        from app.services.astronomical_service import get_time_of_day, get_moon_phase
        from app.services.tide_service import get_tide_state_for_timestamp

        # Get latest environment snapshot (captured every 5-15 minutes)
        snapshot = get_latest_snapshot(db)
        snapshot_dict = get_snapshot_as_dict(snapshot) if snapshot else {}

        # Get time of day and moon phase
        # Convert CST input to UTC for database storage
        if catch_data.timestamp:
            catch_time = central_to_utc(catch_data.timestamp)
        else:
            catch_time = central_to_utc(central_now())
        time_of_day = get_time_of_day(db, catch_time)
        moon_data = get_moon_phase(db, catch_time.date())

        # AUTO-LOG TIDE: Get tide state for the catch timestamp
        tide_state_info = get_tide_state_for_timestamp(db, catch_time)

        # Map presentation to rig_type if rig_type not provided
        rig_type = catch_data.presentation  # For backward compatibility

        # Create catch record with all fields
        catch = Catch(
            timestamp=catch_time,
            species=catch_data.species,
            # Location fields
            zone_id=catch_data.zone_id,
            distance_from_dock=catch_data.distance_from_dock,
            depth_estimate=catch_data.depth_estimate,
            structure_type=catch_data.structure_type,
            # Size and quantity
            size_length_in=catch_data.size_length_in,
            size_bucket=catch_data.size_bucket,
            quantity=catch_data.quantity or 1,
            # Bait and rig
            bait_used=catch_data.bait_used,
            presentation=catch_data.presentation,
            rig_type=rig_type,
            kept=catch_data.kept,
            notes=catch_data.notes,
            days_since_last_checked=catch_data.days_since_last_checked,
            # Environment snapshot (auto-logged)
            water_temp=snapshot_dict.get('water_temperature'),
            air_temp=snapshot_dict.get('air_temperature'),
            humidity=snapshot_dict.get('humidity'),
            barometric_pressure=snapshot_dict.get('barometric_pressure'),
            tide_height=tide_state_info.get('tide_height'),
            tide_stage=tide_state_info.get('tide_stage'),
            current_speed=snapshot_dict.get('current_speed'),
            current_direction=snapshot_dict.get('current_direction'),
            wind_speed=snapshot_dict.get('wind_speed'),
            wind_direction=snapshot_dict.get('wind_direction'),
            weather=snapshot_dict.get('weather'),
            time_of_day=time_of_day,
            moon_phase=moon_data.get('phase') if moon_data else None,
            dock_lights_on=snapshot_dict.get('dock_lights_on', False)
        )

        db.add(catch)
        db.commit()
        db.refresh(catch)

        # ========== EVENT TRIGGERS ==========
        # Update learning tables and recalculate scores
        from app.services.rig_learning_service import update_rig_effect
        from app.services.condition_learning_service import (
            update_zone_condition_effect,
            update_rig_condition_effect
        )
        from app.services.score_cache_service import recalculate_bite_score
        from app.services.tip_generation_service import update_species_zone_tip

        try:
            # Detect crab trap entries for reduced condition weighting
            # Crab traps soak 12-24 hours, so exact time/conditions are fuzzy
            is_crab_trap = (
                catch.species == 'blue_crab' and
                rig_type and
                ('trap' in rig_type.lower() or 'pot' in rig_type.lower())
            )
            # Apply 15% weight for crab trap conditions, 100% for normal catches
            condition_weight = 0.15 if is_crab_trap else 1.0

            if is_crab_trap:
                logger.info(f"Detected crab trap entry - applying reduced condition weight (15%)")

            # 1. Update rig learning
            if rig_type:
                update_rig_effect(db, catch.species, catch.zone_id, rig_type)

            # 2. Update condition learning with weight multiplier for crab traps
            conditions_for_learning = {
                'tide_stage': catch.tide_stage,
                'clarity': snapshot_dict.get('clarity', 'clean'),
                'wind_direction': catch.wind_direction,
                'current_speed': catch.current_speed
            }
            update_zone_condition_effect(db, catch.species, catch.zone_id, conditions_for_learning, condition_weight)

            if rig_type:
                update_rig_condition_effect(db, catch.species, rig_type, conditions_for_learning, condition_weight)

            # 3. Recalculate bite score with smoothing
            recalculate_bite_score(db, catch.species, catch.zone_id)

            # 4. Update tip
            update_species_zone_tip(db, catch.species, catch.zone_id)

            logger.info(f"Completed learning updates for {catch.species} in {catch.zone_id}")

        except Exception as e:
            # Don't fail the whole catch logging if learning fails
            logger.error(f"Error in catch learning triggers: {e}")
        # ========== END TRIGGERS ==========

        logger.info(f"Logged catch: {catch.species} in {catch.zone_id} at {catch.timestamp}")

        return {
            'id': catch.id,
            'species': get_species_display_name(catch.species),
            'species_key': catch.species,
            'zone_id': catch.zone_id,
            'timestamp': catch.timestamp.isoformat(),
            'size_bucket': catch.size_bucket,
            'kept': catch.kept,
            'message': 'Catch logged successfully with full environment snapshot'
        }

    except Exception as e:
        logger.error(f"Error logging catch: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catches")
async def get_catches(
    limit: int = 50,
    species: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Get recent catches from the fishing log.

    Args:
        limit: Maximum number of catches to return (default 50, max 200)
        species: Optional filter by species key

    Returns:
        List of catch records
    """
    try:
        limit = min(limit, 200)  # Cap at 200

        query = db.query(Catch).order_by(Catch.timestamp.desc())

        if species:
            query = query.filter(Catch.species == species)

        catches = query.limit(limit).all()

        result = []
        for catch in catches:
            result.append({
                'id': catch.id,
                'timestamp': get_central_isoformat(catch.timestamp),
                'species': get_species_display_name(catch.species),
                'species_key': catch.species,
                'species_display': get_species_display_name(catch.species),
                'zone_id': catch.zone_id,
                'size_length_in': catch.size_length_in,
                'size_bucket': catch.size_bucket,
                'quantity': catch.quantity,
                'bait_used': catch.bait_used,
                'presentation': catch.presentation or catch.rig_type,
                'kept': catch.kept,
                'notes': catch.notes,
                # Conditions at time of catch
                'tide_stage': catch.tide_stage,
                'tide_height': catch.tide_height,
                'water_temp': catch.water_temp,
                'air_temp': catch.air_temp,
                'wind_speed': catch.wind_speed,
                'weather': catch.weather
            })

        return result

    except Exception as e:
        logger.error(f"Error getting catches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/catches/{catch_id}")
async def delete_catch(
    catch_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Delete a catch entry by ID.

    Args:
        catch_id: ID of the catch to delete

    Returns:
        Success message
    """
    try:
        catch = db.query(Catch).filter(Catch.id == catch_id).first()

        if not catch:
            raise HTTPException(status_code=404, detail="Catch not found")

        db.delete(catch)
        db.commit()

        return {'success': True, 'message': 'Catch deleted successfully'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting catch: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/catches/stats")
async def get_catch_stats(
    days: int = 30,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get catch statistics for analysis.

    Args:
        days: Number of days to look back (default 30, max 365)

    Returns:
        Catch statistics and patterns
    """
    try:
        days = min(days, 365)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        catches = db.query(Catch).filter(
            Catch.timestamp >= cutoff_date
        ).all()

        if not catches:
            return {
                'total_catches': 0,
                'days_analyzed': days,
                'species_breakdown': {},
                'bait_success': {},
                'method_success': {},
                'message': 'No catches in this time period'
            }

        # Species breakdown (account for quantity)
        species_counts = {}
        total_fish = 0
        total_kept_fish = 0
        for catch in catches:
            qty = catch.quantity or 1
            total_fish += qty
            if catch.kept:
                total_kept_fish += qty

            species_name = get_species_display_name(catch.species)
            if species_name not in species_counts:
                species_counts[species_name] = {'total': 0, 'kept': 0}
            species_counts[species_name]['total'] += qty
            if catch.kept:
                species_counts[species_name]['kept'] += qty

        # Bait success (count by catch entries, not individual fish)
        bait_counts = {}
        for catch in catches:
            if catch.bait_used:
                if catch.bait_used not in bait_counts:
                    bait_counts[catch.bait_used] = 0
                bait_counts[catch.bait_used] += 1

        # Method success (count by catch entries, not individual fish)
        method_counts = {}
        for catch in catches:
            if catch.presentation:
                if catch.presentation not in method_counts:
                    method_counts[catch.presentation] = 0
                method_counts[catch.presentation] += 1

        return {
            'total_catches': total_fish,
            'kept_count': total_kept_fish,
            'released_count': total_fish - total_kept_fish,
            'days_analyzed': days,
            'species_breakdown': species_counts,
            'by_species': [
                {'species_display': k, 'count': v['total']}
                for k, v in sorted(species_counts.items(), key=lambda x: x[1]['total'], reverse=True)
            ],
            'bait_success': dict(sorted(bait_counts.items(), key=lambda x: x[1], reverse=True)),
            'method_success': dict(sorted(method_counts.items(), key=lambda x: x[1], reverse=True))
        }

    except Exception as e:
        logger.error(f"Error getting catch stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Bait Log Endpoints =====

@app.post("/api/bait-logs")
async def log_bait(bait_data: BaitLogCreate, db: Session = Depends(get_db)) -> Dict:
    """
    Log a new bait catch - NEW HYPERLOCAL SPEC.

    Captures full environment snapshot with all new fields.
    """
    try:
        from app.services.environment_snapshot import get_latest_snapshot, get_snapshot_as_dict
        from app.services.astronomical_service import get_time_of_day, get_moon_phase
        from app.services.tide_service import get_tide_state_for_timestamp

        # Get latest environment snapshot
        snapshot = get_latest_snapshot(db)
        snapshot_dict = get_snapshot_as_dict(snapshot) if snapshot else {}

        # Get time of day and moon phase
        # Convert CST input to UTC for database storage
        if bait_data.timestamp:
            log_time = central_to_utc(bait_data.timestamp)
        else:
            log_time = central_to_utc(central_now())
        time_of_day = get_time_of_day(db, log_time)
        moon_data = get_moon_phase(db, log_time.date())

        # AUTO-LOG TIDE: Get tide state for the bait log timestamp
        tide_state_info = get_tide_state_for_timestamp(db, log_time)

        # Create bait log with all fields
        bait_log = BaitLog(
            timestamp=log_time,
            bait_species=bait_data.bait_species,
            method=bait_data.method,
            zone_id=bait_data.zone_id,
            quantity_estimate=bait_data.quantity_estimate,
            structure_type=bait_data.structure_type,
            notes=bait_data.notes,
            days_since_last_checked=bait_data.days_since_last_checked,
            # Environment snapshot (auto-logged)
            water_temp=snapshot_dict.get('water_temperature'),
            air_temp=snapshot_dict.get('air_temperature'),
            humidity=snapshot_dict.get('humidity'),
            barometric_pressure=snapshot_dict.get('barometric_pressure'),
            tide_height=tide_state_info.get('tide_height'),
            tide_stage=tide_state_info.get('tide_stage'),
            current_speed=snapshot_dict.get('current_speed'),
            current_direction=snapshot_dict.get('current_direction'),
            wind_speed=snapshot_dict.get('wind_speed'),
            wind_direction=snapshot_dict.get('wind_direction'),
            weather=snapshot_dict.get('weather'),
            time_of_day=time_of_day,
            moon_phase=moon_data.get('phase') if moon_data else None,
            dock_lights_on=snapshot_dict.get('dock_lights_on', False)
        )

        db.add(bait_log)
        db.commit()
        db.refresh(bait_log)

        # ========== EVENT TRIGGERS ==========
        # Recalculate bait score and predator species scores
        from app.services.score_cache_service import recalculate_bait_score, recalculate_bite_score

        try:
            # 1. Recalculate bait score
            recalculate_bait_score(db, bait_log.bait_species, bait_log.zone_id)

            # 2. Recalculate relevant predator species
            # Shrimp -> Trout, Redfish, Flounder, Sheepshead, Drum
            # Menhaden/Mullet -> Redfish, Trout, Jack Crevalle
            predator_map = {
                'live_shrimp': ['speckled_trout', 'redfish', 'flounder', 'sheepshead', 'black_drum'],
                'shrimp': ['speckled_trout', 'redfish', 'flounder', 'sheepshead', 'black_drum'],
                'menhaden': ['redfish', 'speckled_trout', 'jack_crevalle'],
                'mullet': ['redfish', 'speckled_trout', 'jack_crevalle'],
                'fiddler_crab': ['sheepshead', 'black_drum'],
                'fiddler': ['sheepshead', 'black_drum']
            }

            predators = predator_map.get(bait_log.bait_species.lower(), [])
            for predator in predators:
                try:
                    recalculate_bite_score(db, predator, bait_log.zone_id)
                except Exception as e:
                    logger.error(f"Error recalculating {predator} score: {e}")

            logger.info(f"Completed bait learning updates for {bait_log.bait_species} in {bait_log.zone_id}")

        except Exception as e:
            # Don't fail the whole bait logging if learning fails
            logger.error(f"Error in bait learning triggers: {e}")
        # ========== END TRIGGERS ==========

        logger.info(f"Logged bait: {bait_log.bait_species} in {bait_log.zone_id} via {bait_log.method}")

        return {
            'id': bait_log.id,
            'bait_species': bait_log.bait_species,
            'zone_id': bait_log.zone_id,
            'method': bait_log.method,
            'timestamp': bait_log.timestamp.isoformat(),
            'message': 'Bait logged successfully with full environment snapshot'
        }

    except Exception as e:
        logger.error(f"Error logging bait: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bait-logs")
async def get_bait_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Get recent bait logs.
    """
    try:
        limit = min(limit, 200)  # Cap at 200

        logs = db.query(BaitLog).order_by(BaitLog.timestamp.desc()).limit(limit).all()

        return [
            {
                'id': log.id,
                'bait_species': log.bait_species,
                'zone': log.zone_id,
                'time': log.timestamp.isoformat(),
                'quantity': log.quantity_estimate,
                'how_caught': log.method,
                'notes': log.notes,
                'created_at': log.timestamp.isoformat()
            }
            for log in logs
        ]

    except Exception as e:
        logger.error(f"Error getting bait logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/bait-logs/{log_id}")
async def delete_bait_log(
    log_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Delete a bait log entry by ID.

    Args:
        log_id: ID of the bait log to delete

    Returns:
        Success message
    """
    try:
        log = db.query(BaitLog).filter(BaitLog.id == log_id).first()

        if not log:
            raise HTTPException(status_code=404, detail="Bait log not found")

        db.delete(log)
        db.commit()

        return {'success': True, 'message': 'Bait log deleted successfully'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting bait log: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===== Predator Log Endpoints =====

@app.post("/api/predator-logs")
async def log_predator(predator_data: PredatorLogCreate, db: Session = Depends(get_db)) -> Dict:
    """
    Log a new predator sighting.
    """
    try:
        from app.services.tide_service import get_tide_state_for_timestamp

        # Get predator sighting time
        # Convert CST input to UTC for database storage
        if predator_data.time:
            sighting_time = central_to_utc(predator_data.time)
        else:
            sighting_time = central_to_utc(central_now())

        # AUTO-LOG TIDE: Get tide state for the predator sighting timestamp
        tide_state_info = get_tide_state_for_timestamp(db, sighting_time)

        predator_log = PredatorLog(
            predator=predator_data.predator,
            zone=predator_data.zone,
            time=sighting_time,
            behavior=predator_data.behavior,
            tide=tide_state_info.get('tide_stage'),  # Auto-logged from timestamp
            notes=predator_data.notes
        )

        db.add(predator_log)
        db.commit()
        db.refresh(predator_log)

        # ========== EVENT TRIGGERS ==========
        # Recalculate prey species scores in this zone
        from app.services.score_cache_service import recalculate_bite_score

        try:
            # Prey species affected by predators
            prey_species = ['speckled_trout', 'white_trout', 'menhaden', 'mullet']

            for prey in prey_species:
                try:
                    recalculate_bite_score(db, prey, predator_log.zone)
                except Exception as e:
                    logger.error(f"Error recalculating {prey} score after predator: {e}")

            logger.info(f"Recalculated prey species scores for {predator_log.zone} after predator sighting")

        except Exception as e:
            # Don't fail the whole predator logging if learning fails
            logger.error(f"Error in predator learning triggers: {e}")
        # ========== END TRIGGERS ==========

        logger.info(f"Logged predator: {predator_log.predator} in {predator_log.zone}")

        return {
            'id': predator_log.id,
            'predator': predator_log.predator,
            'zone': predator_log.zone,
            'time': predator_log.time.isoformat(),
            'message': 'Predator sighting logged successfully'
        }

    except Exception as e:
        logger.error(f"Error logging predator: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/predator-logs")
async def get_predator_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict]:
    """
    Get recent predator logs.
    Returns logs with recent activity flag (within 4 hours).
    """
    try:
        limit = min(limit, 200)  # Cap at 200

        logs = db.query(PredatorLog).order_by(PredatorLog.time.desc()).limit(limit).all()

        now = datetime.utcnow()

        return [
            {
                'id': log.id,
                'predator': log.predator,
                'zone': log.zone,
                'time': log.time.isoformat(),
                'behavior': log.behavior,
                'tide': log.tide,
                'notes': log.notes,
                'created_at': log.created_at.isoformat(),
                'is_recent': (now - log.time).total_seconds() / 3600 <= 4  # Within 4 hours
            }
            for log in logs
        ]

    except Exception as e:
        logger.error(f"Error getting predator logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/predator-logs/{log_id}")
async def delete_predator_log(
    log_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Delete a predator log entry by ID.

    Args:
        log_id: ID of the predator log to delete

    Returns:
        Success message
    """
    try:
        log = db.query(PredatorLog).filter(PredatorLog.id == log_id).first()

        if not log:
            raise HTTPException(status_code=404, detail="Predator log not found")

        db.delete(log)
        db.commit()

        return {'success': True, 'message': 'Predator log deleted successfully'}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting predator log: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===== Learning Delta Endpoint =====

@app.get("/api/learning-delta")
async def get_learning_delta_api(
    species: str,
    zone: str,
    tide_stage: str,
    time_block: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get learning delta and metadata for a specific bucket.

    Args:
        species: Species key
        zone: Zone identifier
        tide_stage: Tide stage (low, rising, high, falling)
        time_block: Time of day block (morning, midday, evening)

    Returns:
        Learning delta information
    """
    try:
        return get_learning_delta(db, species, zone, tide_stage, time_block)
    except Exception as e:
        logger.error(f"Error getting learning delta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/zone-data-sufficiency")
async def get_zone_data_sufficiency_api(
    zone: str,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Check if a zone has sufficient data for reliable predictions.
    """
    try:
        return get_zone_data_sufficiency(db, zone)
    except Exception as e:
        logger.error(f"Error checking zone data sufficiency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weekly-summary")
async def get_weekly_summary(db: Session = Depends(get_db)) -> Dict:
    """
    Get comprehensive weekly summary with catch patterns and forecast insights.

    Returns:
        Weekly aggregated data including best species, zones, conditions, etc.
    """
    try:
        # Look back 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        # Get all catches from the past week
        catches = db.query(Catch).filter(
            Catch.timestamp >= cutoff_date
        ).all()

        # Get all forecast windows from the past week
        forecast_windows = db.query(ForecastWindow).filter(
            ForecastWindow.start_time >= cutoff_date
        ).all()

        # Initialize result structure
        result = {
            'week_start': get_central_isoformat(cutoff_date),
            'week_end': get_central_isoformat(datetime.utcnow()),
            'total_catches': 0,
            'best_species': None,
            'best_zones': [],
            'best_clarity': None,
            'best_hours': [],
            'best_tide_stage': None,
            'best_bait': None,
            'user_catch_summary': {}
        }

        # If no catches, return empty summary
        if not catches:
            result['message'] = 'No catches logged this week'
            return result

        # === CATCH LOG ANALYSIS ===

        # Species breakdown (account for quantity)
        species_counts = {}
        total_fish = 0
        for catch in catches:
            qty = catch.quantity or 1
            total_fish += qty
            species_name = get_species_display_name(catch.species)
            if species_name not in species_counts:
                species_counts[species_name] = 0
            species_counts[species_name] += qty

        result['total_catches'] = total_fish
        result['user_catch_summary'] = {
            'by_species': [
                {'species': k, 'count': v}
                for k, v in sorted(species_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        }

        # Best species of week (most caught)
        if species_counts:
            best_species = max(species_counts.items(), key=lambda x: x[1])
            result['best_species'] = {
                'species': best_species[0],
                'count': best_species[1]
            }

        # Best zones (from zone_id field - count catches by zone)
        zone_counts = {}
        for catch in catches:
            if catch.zone_id:
                zone = catch.zone_id
                if zone not in zone_counts:
                    zone_counts[zone] = 0
                qty = catch.quantity or 1
                zone_counts[zone] += qty

        if zone_counts:
            # Sort zones by count and return top 3
            sorted_zones = sorted(zone_counts.items(), key=lambda x: x[1], reverse=True)
            result['best_zones'] = [
                {'zone': zone, 'catches': count}
                for zone, count in sorted_zones[:3]
            ]

        # Best bait (most successful)
        bait_counts = {}
        for catch in catches:
            if catch.bait_used:
                if catch.bait_used not in bait_counts:
                    bait_counts[catch.bait_used] = 0
                bait_counts[catch.bait_used] += 1

        if bait_counts:
            best_bait = max(bait_counts.items(), key=lambda x: x[1])
            result['best_bait'] = {
                'bait': best_bait[0],
                'catches': best_bait[1]
            }

        # Best tide stage (from catch conditions snapshot)
        tide_counts = {}
        for catch in catches:
            if catch.tide_state:
                tide = catch.tide_state
                if tide not in tide_counts:
                    tide_counts[tide] = 0
                qty = catch.quantity or 1
                tide_counts[tide] += qty

        if tide_counts:
            best_tide = max(tide_counts.items(), key=lambda x: x[1])
            result['best_tide_stage'] = {
                'tide': best_tide[0],
                'catches': best_tide[1]
            }

        # === FORECAST ANALYSIS ===

        # Best hours/time of day (from forecast windows with highest scores)
        if forecast_windows:
            # Group by time of day and calculate average score
            time_of_day_scores = {}
            for window in forecast_windows:
                tod = window.time_of_day
                if tod and window.overall_score:
                    if tod not in time_of_day_scores:
                        time_of_day_scores[tod] = []
                    time_of_day_scores[tod].append(window.overall_score)

            # Calculate averages
            time_of_day_avg = {
                tod: sum(scores) / len(scores)
                for tod, scores in time_of_day_scores.items()
            }

            # Sort by average score
            sorted_times = sorted(time_of_day_avg.items(), key=lambda x: x[1], reverse=True)
            result['best_hours'] = [
                {'time_of_day': tod, 'avg_score': round(score, 1)}
                for tod, score in sorted_times
            ]

        # Best clarity conditions (simulate - we don't have clarity in DB yet)
        # For now, use wind speed as proxy: low wind = clearer water
        if forecast_windows:
            wind_clarity_map = []
            for window in forecast_windows:
                if window.wind_speed is not None:
                    if window.wind_speed < 8:
                        clarity = "Clear"
                    elif window.wind_speed < 15:
                        clarity = "Lightly Stained"
                    else:
                        clarity = "Muddy"
                    wind_clarity_map.append(clarity)

            if wind_clarity_map:
                # Count occurrences
                clarity_counts = {}
                for clarity in wind_clarity_map:
                    if clarity not in clarity_counts:
                        clarity_counts[clarity] = 0
                    clarity_counts[clarity] += 1

                # Most common clarity
                best_clarity = max(clarity_counts.items(), key=lambda x: x[1])
                result['best_clarity'] = {
                    'clarity': best_clarity[0],
                    'occurrences': best_clarity[1]
                }

        return result

    except Exception as e:
        logger.error(f"Error getting weekly summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check(db: Session = Depends(get_db)) -> Dict:
    """
    Health check endpoint.

    Returns system status and last data update time.
    """
    try:
        # Check if we have recent forecast data
        latest_window = db.query(ForecastWindow).order_by(
            ForecastWindow.computed_at.desc()
        ).first()

        if latest_window:
            last_update = latest_window.computed_at
            status = "healthy"
        else:
            last_update = None
            status = "no_data"

        return {
            'status': status,
            'last_forecast_update': get_central_isoformat(last_update) if last_update else None,
            'location': config.location['name'],
            'server_time': get_central_isoformat(datetime.utcnow())
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.debug
    )
