"""Hyperlocal bite scoring engine for BayScan - BEHAVIOR SPEC IMPLEMENTATION.

NEW FORMULA (Nov 25, 2025):
BiteScore(S,Z,T) =
    SeasonalBaseline(S, month)
    + ConditionMatch(S,Z,T)
    + StructureMatch(S,Z,T)
    + ClaritySalinityModifier(S,Z,T)
    + RecentActivityModifier(S,Z,T)
    + PredatorModifier(S,Z,T)
    + ExternalIndicatorsModifier(S,Z,T)

Clamped 0-100.

All bite scores are zone-specific and species-behavior-aware.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.schemas import Catch, BaitLog, PredatorLog
from app.rules.uglyfishing_calendar import get_seasonal_baseline_score
from app.rules.species_tiers import should_use_full_scoring, get_species_tier
from app.rules.species_behavior_profiles import get_species_profile, is_prey_species
from app.services.confidence_scoring import calculate_species_zone_confidence
from app.services.advanced_features import DOCK_ZONES
import logging

logger = logging.getLogger(__name__)


def calculate_zone_bite_score(
    db: Session,
    species: str,
    zone_id: str,
    conditions: Dict[str, Any],
    date: datetime = None
) -> Dict[str, Any]:
    """
    Calculate hyperlocal bite score using BEHAVIOR SPEC formula.

    Args:
        db: Database session
        species: Species name (e.g., 'speckled_trout')
        zone_id: Zone identifier (e.g., 'Zone 3')
        conditions: Current environmental conditions dict
        date: Date for calculation (defaults to now)

    Returns:
        Dictionary with:
        - bite_score: Final 0-100 score
        - seasonal_baseline: UglyFishing baseline (0-90)
        - condition_match: Environmental condition scoring
        - structure_match: Zone structure bonus/penalty
        - clarity_salinity: Water quality modifier
        - recent_activity: Bonus from recent catches
        - predator_penalty: Penalty from recent predators
        - external_indicators: External data sources
        - confidence: Confidence level dict
        - breakdown: Detailed breakdown
    """
    if date is None:
        date = datetime.utcnow()

    # Step 1: Seasonal baseline (UglyFishing scale: 0-90)
    seasonal_baseline = get_seasonal_baseline_score(species, date)

    # Step 2: Get confidence
    confidence = calculate_species_zone_confidence(db, species, zone_id)

    # Step 3: Check tier and use appropriate scoring
    if should_use_full_scoring(species):
        # TIER 1: Full detailed scoring
        condition_match = calculate_condition_match(species, conditions)
        structure_match = calculate_structure_match(species, zone_id, conditions)
        clarity_salinity = calculate_clarity_salinity_modifier(species, conditions)
        recent_activity = calculate_recent_activity_modifier(db, species, zone_id, confidence)
        predator_penalty = calculate_predator_modifier(db, species, zone_id)
        external_indicators = calculate_external_indicators_modifier(species, conditions)

        final_score = (seasonal_baseline + condition_match + structure_match +
                      clarity_salinity + recent_activity + predator_penalty +
                      external_indicators)
    else:
        # TIER 2: Simplified scoring (seasonal + basic condition + structure)
        condition_match = calculate_simple_condition_match(species, conditions)
        structure_match = calculate_structure_match(species, zone_id, conditions)
        clarity_salinity = 0.0
        recent_activity = 0.0
        predator_penalty = 0.0
        external_indicators = 0.0

        final_score = seasonal_baseline + condition_match + structure_match

    # Clamp to 0-100
    final_score = max(0.0, min(100.0, final_score))

    return {
        'bite_score': round(final_score, 1),
        'seasonal_baseline': round(seasonal_baseline, 1),
        'condition_match': round(condition_match, 1),
        'structure_match': round(structure_match, 1),
        'clarity_salinity': round(clarity_salinity, 1),
        'recent_activity': round(recent_activity, 1),
        'predator_penalty': round(predator_penalty, 1),
        'external_indicators': round(external_indicators, 1),
        'zone_id': zone_id,
        'species': species,
        'confidence': confidence,
        'tier': get_species_tier(species),
        'breakdown': {
            'baseline_label': get_baseline_label(seasonal_baseline),
            'env_factors': get_env_breakdown(species, conditions),
            'recent_catches_count': get_recent_catches_count(db, species, zone_id, 6),
            'recent_predators': get_recent_predators(db, zone_id, 4)
        }
    }


def calculate_condition_match(species: str, conditions: Dict[str, Any]) -> float:
    """
    Score differences between current conditions and species preferences.
    Range: ±3 to ±10 (can exceed in extreme cases)

    Factors:
    - Water temperature vs ideal range
    - Tide stage vs preference
    - Current speed
    - Wind speed + direction
    - Pressure trend
    - Time of day
    - Moon phase / solunar
    """
    profile = get_species_profile(species)
    if not profile:
        return 0.0

    score = 0.0

    # WATER TEMPERATURE
    water_temp = conditions.get('water_temperature')
    if water_temp and 'water_temp' in profile:
        temp_prefs = profile['water_temp']

        if temp_prefs.get('ideal_min', 0) <= water_temp <= temp_prefs.get('ideal_max', 100):
            # In ideal range
            score += temp_prefs.get('bonus_in_ideal', 5)
        elif (water_temp < temp_prefs.get('workable_min', 0) or
              water_temp > temp_prefs.get('workable_max', 100)):
            # Outside workable range
            score += temp_prefs.get('penalty_out_of_workable', -4)

        # Check for cold snap penalty (flounder)
        if 'penalty_cold_snap' in temp_prefs:
            temp_change = conditions.get('temperature_change_24h', 0)
            if temp_change < -10:  # Dropped >10°F in 24h
                score += temp_prefs['penalty_cold_snap']

    # TIDE STAGE
    tide_stage = conditions.get('tide_stage', 'slack').lower()
    if 'tide_stage' in profile:
        score += profile['tide_stage'].get(tide_stage, 0)

    # CURRENT SPEED
    current_speed = conditions.get('current_speed', 0)
    if 'current_speed' in profile:
        curr_prefs = profile['current_speed']

        if curr_prefs.get('ideal_min', 0) <= current_speed <= curr_prefs.get('ideal_max', 999):
            # Good current speed
            score += curr_prefs.get('bonus_moving', 3)
        elif current_speed < 0.2:
            # Slack water
            score += curr_prefs.get('penalty_slack', -3)

    # WIND
    wind_speed = conditions.get('wind_speed', 0)
    wind_dir_raw = conditions.get('wind_direction')
    wind_dir = wind_dir_raw.upper() if wind_dir_raw else ''
    if 'wind' in profile:
        wind_prefs = profile['wind']

        if wind_dir and wind_dir in [d.upper() for d in wind_prefs.get('favorable_directions', [])]:
            score += wind_prefs.get('bonus_favorable', 2)
        elif (wind_dir and wind_dir in [d.upper() for d in wind_prefs.get('unfavorable_directions', [])] and
              wind_speed > 15):
            # Strong unfavorable wind (post-front N wind)
            score += wind_prefs.get('penalty_unfavorable_strong', -3)

    # BAROMETRIC PRESSURE TREND
    pressure_trend = conditions.get('pressure_trend', 'stable').lower()
    if 'pressure' in profile:
        score += profile['pressure'].get(pressure_trend, 0)

    # TIME OF DAY
    time_of_day = conditions.get('time_of_day', 'midday').lower()
    if 'time_of_day' in profile:
        score += profile['time_of_day'].get(time_of_day, 0)

    # SOLUNAR PERIOD
    solunar = conditions.get('solunar_period')
    if solunar and 'solunar' in profile:
        score += profile['solunar'].get(solunar, 0)

    return score


def calculate_simple_condition_match(species: str, conditions: Dict[str, Any]) -> float:
    """
    Simplified condition match for Tier 2 species.
    Basic tide and time of day only.
    """
    profile = get_species_profile(species)
    if not profile:
        return 0.0

    score = 0.0

    # Tide stage
    tide_stage = conditions.get('tide_stage', 'slack').lower()
    if 'tide_stage' in profile:
        score += profile['tide_stage'].get(tide_stage, 0)

    # Time of day (for white trout night preference)
    time_of_day = conditions.get('time_of_day', 'midday').lower()
    if 'time_of_day' in profile:
        score += profile['time_of_day'].get(time_of_day, 0)

    return score


def calculate_structure_match(species: str, zone_id: str, conditions: Dict[str, Any]) -> float:
    """
    Zone structure match based on species preferences and zone features.
    Range: ±5 to ±10

    Uses zone geometry + species structure preferences from behavior profiles.
    """
    profile = get_species_profile(species)
    if not profile:
        return 0.0

    # Extract zone number
    try:
        zone_num = int(zone_id.split()[-1]) if 'Zone' in zone_id else 3
    except:
        zone_num = 3

    zone_info = DOCK_ZONES.get(zone_num, {})
    score = 0.0
    structure_prefs = profile.get('structure', {})

    # Match zone features to species preferences
    if zone_num == 1:
        # Zone 1: Pilings + rubble (NW quadrant)
        score += structure_prefs.get('pilings', 0)
        score += structure_prefs.get('rubble', 0)

    elif zone_num == 2:
        # Zone 2: Open water, NO structure (SW quadrant)
        score += structure_prefs.get('open_water', 0)

    elif zone_num == 3:
        # Zone 3: Pilings (NE quadrant, most fished)
        score += structure_prefs.get('pilings', 0)
        # Slight bonus for high confidence zone
        score += 0.5

    elif zone_num == 4:
        # Zone 4: Green light (SE quadrant, most fished)
        time_of_day = conditions.get('time_of_day', 'midday').lower()
        clarity = conditions.get('water_clarity', 'slightly_stained').lower()

        if time_of_day in ['evening', 'night'] and 'light' in profile:
            # Light bonus (with clarity check)
            light_bonus = profile['light'].get('green_light_night_bonus', 0)

            # Reduce bonus in muddy water if species requires clarity
            if profile['light'].get('requires_decent_clarity', False) and clarity == 'muddy':
                light_bonus *= 0.3

            score += light_bonus

        # Slight bonus for high confidence zone
        score += 0.5

    elif zone_num == 5:
        # Zone 5: Dual pilings (strongest structure, deepest)
        # Apply 1.5x multiplier for dual structure
        piling_score = structure_prefs.get('pilings', 0) * 1.5
        score += piling_score

        # Bonus for deep-preferring species
        if profile.get('depth_preference') == 'deep':
            score += 2.0

    # CURRENT + STRUCTURE BONUS (redfish, sheepshead)
    if 'current_structure_bonus' in profile:
        current_speed = conditions.get('current_speed', 0)
        if current_speed > 0.3 and zone_num in [1, 3, 5]:  # Structure zones with current
            score += profile['current_structure_bonus']

    return score


def calculate_clarity_salinity_modifier(species: str, conditions: Dict[str, Any]) -> float:
    """
    Water clarity and salinity adjustments.
    Range: ±3 to ±7
    """
    profile = get_species_profile(species)
    if not profile:
        return 0.0

    score = 0.0

    # WATER CLARITY
    clarity = conditions.get('water_clarity', 'slightly_stained').lower()
    if 'water_clarity' in profile:
        score += profile['water_clarity'].get(clarity, 0)

    # SALINITY
    salinity = conditions.get('salinity')
    if salinity and 'salinity' in profile:
        sal_prefs = profile['salinity']

        # Check if outside preferred range
        if not (sal_prefs.get('preferred_min', 0) <= salinity <= sal_prefs.get('preferred_max', 40)):
            # Apply penalty if not tolerant
            if not sal_prefs.get('tolerant', True):
                score -= 2.0

        # Rapid salinity change penalty
        salinity_change = conditions.get('salinity_change_24h', 0)
        if abs(salinity_change) > 5:  # >5 ppt change in 24h
            score += sal_prefs.get('penalty_rapid_change', 0)

    return score


def calculate_recent_activity_modifier(
    db: Session,
    species: str,
    zone_id: str,
    confidence: Dict
) -> float:
    """
    Look back 4-6 hours in zone.
    Each catch adds base value, decaying 25% per hour.
    Range: 0 to +10

    Confidence affects weight:
    - LOW confidence: 0.3x weight
    - MEDIUM confidence: 0.6x weight
    - HIGH confidence: 1.0x weight
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=6)

    try:
        recent_catches = db.query(Catch).filter(
            Catch.species == species,
            Catch.zone_id == zone_id,
            Catch.timestamp >= cutoff
        ).all()

        score = 0.0
        for catch in recent_catches:
            hours_ago = (now - catch.timestamp).total_seconds() / 3600

            # Base value per catch
            base_value = 4.0

            # Apply 25% decay per hour
            decay_factor = 0.75 ** hours_ago

            score += base_value * decay_factor * catch.quantity

        # Apply confidence weight
        weight = confidence.get('recent_activity_weight', 1.0)
        score *= weight

        # Cap at +10
        return min(10.0, score)

    except Exception as e:
        logger.error(f"Error calculating recent activity: {e}")
        return 0.0


def calculate_predator_modifier(db: Session, species: str, zone_id: str) -> float:
    """
    For prey species (trout, white trout, bait), apply penalty for recent predators.
    Penalty decays linearly to 0 over 4 hours.
    Range: 0 to -8

    Prey species: trout, white_trout, menhaden, mullet, shrimp
    """
    if not is_prey_species(species):
        return 0.0

    now = datetime.utcnow()
    cutoff = now - timedelta(hours=4)

    try:
        recent_predators = db.query(PredatorLog).filter(
            PredatorLog.zone == zone_id,
            PredatorLog.time >= cutoff
        ).all()

        if not recent_predators:
            return 0.0

        # Find most recent predator
        most_recent = max(recent_predators, key=lambda p: p.time)
        hours_ago = (now - most_recent.time).total_seconds() / 3600

        # Base penalty
        base_penalty = -8.0

        # Linear decay over 4 hours
        decay_factor = max(0.0, 1.0 - (hours_ago / 4.0))

        return base_penalty * decay_factor

    except Exception as e:
        logger.error(f"Error calculating predator penalty: {e}")
        return 0.0


def calculate_external_indicators_modifier(species: str, conditions: Dict[str, Any]) -> float:
    """
    From external sources (FishingPoints, Tides4Fishing, solunar, etc.).
    Range: ±3 to ±5

    PLACEHOLDER: Implement when external data sources are integrated.
    """
    # Future implementation
    # - FishingPoints activity level
    # - Tides4Fishing rating
    # - Additional solunar data
    # - NOAA fishing forecasts
    return 0.0


# HELPER FUNCTIONS

def get_baseline_label(baseline: float) -> str:
    """Get label for seasonal baseline score."""
    if baseline >= 85:
        return "Excellent"
    elif baseline >= 70:
        return "Great"
    elif baseline >= 50:
        return "Good"
    elif baseline >= 30:
        return "Fair"
    elif baseline >= 15:
        return "Poor"
    else:
        return "N/A"


def get_env_breakdown(species: str, conditions: Dict[str, Any]) -> Dict[str, str]:
    """Get human-readable breakdown of environmental factors."""
    breakdown = {}

    water_temp = conditions.get('water_temperature')
    if water_temp:
        breakdown['water_temp'] = f"{water_temp}°F"

    tide_stage = conditions.get('tide_stage', 'unknown')
    breakdown['tide'] = tide_stage

    wind_speed = conditions.get('wind_speed', 0)
    wind_dir = conditions.get('wind_direction', 'N')
    breakdown['wind'] = f"{wind_dir} {wind_speed} mph"

    time_of_day = conditions.get('time_of_day', 'unknown')
    breakdown['time'] = time_of_day

    clarity = conditions.get('water_clarity', 'unknown')
    breakdown['clarity'] = clarity

    return breakdown


def get_recent_catches_count(db: Session, species: str, zone_id: str, hours_back: int) -> int:
    """Get count of recent catches for display."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours_back)

    try:
        count = db.query(Catch).filter(
            Catch.species == species,
            Catch.zone_id == zone_id,
            Catch.timestamp >= cutoff
        ).count()
        return count
    except:
        return 0


def get_recent_predators(db: Session, zone_id: str, hours_back: int) -> List[Dict]:
    """Get list of recent predators for display."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours_back)

    try:
        predators = db.query(PredatorLog).filter(
            PredatorLog.zone == zone_id,
            PredatorLog.time >= cutoff
        ).all()

        return [{
            'type': p.predator,
            'behavior': p.behavior,
            'hours_ago': round((now - p.time).total_seconds() / 3600, 1)
        } for p in predators]
    except:
        return []
