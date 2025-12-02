"""Enhanced bait activity scoring for BayScan - BEHAVIOR SPEC IMPLEMENTATION.

FORMULA:
BaitRating(bait, Z, T) =
    SeasonalBaselineForBait(bait, month)
    + ConditionMatchForBait(bait, Z, T)
    + RecentBaitLogsModifier(bait, Z, T)
    + LightModifierForBait(bait, Z, T)

Clamped 0-100.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.schemas import BaitLog
from app.rules.uglyfishing_calendar import get_seasonal_baseline_score
from app.rules.species_behavior_profiles import get_species_profile
import logging

logger = logging.getLogger(__name__)


def calculate_bait_rating(
    db: Session,
    bait_species: str,
    zone_id: str,
    conditions: Dict,
    date: datetime = None
) -> Dict:
    """
    Calculate bait rating for Bait tab using BEHAVIOR SPEC.

    Args:
        db: Database session
        bait_species: Bait species key (e.g., 'live_shrimp', 'menhaden')
        zone_id: Zone identifier (e.g., 'Zone 3')
        conditions: Current environmental conditions
        date: Date for calculation (defaults to now)

    Returns:
        Dictionary with:
        - bait_species: Bait species key
        - zone_id: Zone identifier
        - rating: Final 0-100 score
        - tier_label: Poor/Fair/Good/Great/Excellent
        - seasonal_baseline: Seasonal score
        - condition_match: Environmental match score
        - light_bonus: Light attraction bonus
        - recent_logs_bonus: Recent bait log activity
    """
    if date is None:
        date = datetime.utcnow()

    # Step 1: Seasonal baseline
    seasonal_baseline = get_seasonal_baseline_score(bait_species, date)

    # Step 2: Condition match for bait
    condition_match = calculate_bait_condition_match(bait_species, zone_id, conditions)

    # Step 3: Recent bait logs modifier
    recent_logs = calculate_recent_bait_logs_modifier(db, bait_species, zone_id)

    # Step 4: Light modifier (Zone 4 specific)
    light_bonus = calculate_light_modifier_for_bait(bait_species, zone_id, conditions)

    # Final score
    final_score = seasonal_baseline + condition_match + recent_logs + light_bonus
    final_score = max(0.0, min(100.0, final_score))

    return {
        'bait_species': bait_species,
        'zone_id': zone_id,
        'rating': round(final_score, 1),
        'tier_label': get_tier_label_from_score(final_score),
        'seasonal_baseline': round(seasonal_baseline, 1),
        'condition_match': round(condition_match, 1),
        'light_bonus': round(light_bonus, 1),
        'recent_logs_bonus': round(recent_logs, 1),
    }


def calculate_bait_condition_match(bait_species: str, zone_id: str, conditions: Dict) -> float:
    """
    Condition match for bait species.
    Range: ±5 to ±15

    Key logic per bait species:
    - SHRIMP: Big boost at night in Zone 4 with green light + incoming tide
    - MENHADEN: Boost with favorable wind/current in structure zones (1,3,5)
    - MULLET: Boost on shallow/tidal edges
    - FIDDLERS: Boost in winter for sheepshead windows
    """
    profile = get_species_profile(bait_species)
    if not profile:
        return 0.0

    try:
        zone_num = int(zone_id.split()[-1]) if 'Zone' in zone_id else 3
    except:
        zone_num = 3

    score = 0.0

    # LIVE SHRIMP
    if bait_species == 'live_shrimp':
        time_of_day = conditions.get('time_of_day', 'midday').lower()
        tide_stage = conditions.get('tide_stage', 'slack').lower()
        water_temp = conditions.get('water_temperature', 70)

        # Zone 4 at night = huge bonus
        if zone_num == 4 and time_of_day in ['evening', 'night']:
            score += 10.0  # Green light attracts shrimp heavily

        # Incoming tide bonus
        if tide_stage == 'incoming':
            score += 5.0

        # Temperature sensitivity
        if water_temp < 55:
            score -= 8.0  # Cold kills shrimp activity fast
        elif water_temp >= 65:
            score += 3.0  # Warm water = active shrimp

    # MENHADEN
    elif bait_species == 'menhaden':
        wind_dir_raw = conditions.get('wind_direction')
        wind_dir = wind_dir_raw.upper() if wind_dir_raw else ''
        current_speed = conditions.get('current_speed', 0)

        # Favorable wind + structure zones
        if wind_dir in ['SE', 'S', 'SW'] and zone_num in [1, 3, 5]:
            score += 8.0  # Wind pushes bait to structure

        # Current edges
        if current_speed > 0.4 and zone_num in [1, 3, 5]:
            score += 5.0

    # MULLET
    elif bait_species == 'mullet':
        tide_stage = conditions.get('tide_stage', 'slack').lower()
        water_temp = conditions.get('water_temperature', 70)

        # Shallow zones + incoming tide
        if zone_num in [1, 2] and tide_stage == 'incoming':
            score += 8.0  # Mullet push shallow on tide

        # Warm water positive
        if water_temp >= 70:
            score += 4.0

    # FIDDLER CRAB
    elif bait_species == 'fiddler_crab':
        month = datetime.utcnow().month

        # Winter availability (Dec-Mar)
        if month in [12, 1, 2, 3]:
            score += 10.0  # Peak fiddler availability
        else:
            score -= 5.0  # Off-season

        # Structure zones (where sheepshead are)
        if zone_num in [1, 3, 5]:
            score += 3.0

    return score


def calculate_recent_bait_logs_modifier(db: Session, bait_species: str, zone_id: str) -> float:
    """
    Recent bait log activity bonus.
    Range: 0 to +8

    Recent logs of "plenty" or "some" add bonus with decay.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=4)

    try:
        recent_logs = db.query(BaitLog).filter(
            BaitLog.bait_species == bait_species,
            BaitLog.zone_id == zone_id,
            BaitLog.timestamp >= cutoff
        ).all()

        score = 0.0
        for log in recent_logs:
            hours_ago = (now - log.timestamp).total_seconds() / 3600

            # Base value depends on quantity
            if log.quantity_estimate and 'plenty' in log.quantity_estimate.lower():
                base_value = 4.0
            elif log.quantity_estimate and 'some' in log.quantity_estimate.lower():
                base_value = 2.0
            else:
                base_value = 1.0

            # 25% decay per hour
            decay_factor = 0.75 ** hours_ago

            score += base_value * decay_factor

        return min(8.0, score)

    except Exception as e:
        logger.error(f"Error calculating recent bait logs: {e}")
        return 0.0


def calculate_light_modifier_for_bait(bait_species: str, zone_id: str, conditions: Dict) -> float:
    """
    Light attraction bonus for bait (Zone 4 specific).
    Range: 0 to +10

    Shrimp especially attracted to green light at night.
    """
    profile = get_species_profile(bait_species)
    if not profile or 'light' not in profile:
        return 0.0

    try:
        zone_num = int(zone_id.split()[-1]) if 'Zone' in zone_id else 3
    except:
        zone_num = 3

    # Only Zone 4 has the green light
    if zone_num != 4:
        return 0.0

    time_of_day = conditions.get('time_of_day', 'midday').lower()
    if time_of_day not in ['evening', 'night']:
        return 0.0

    # Get light bonus from profile
    light_bonus = profile['light'].get('green_light_night_bonus', 0)

    # Check clarity requirement
    if profile['light'].get('requires_decent_clarity', False):
        clarity = conditions.get('water_clarity', 'slightly_stained').lower()
        if clarity == 'muddy':
            light_bonus *= 0.3  # Reduce bonus in muddy water

    return light_bonus


def get_tier_label_from_score(score: float) -> str:
    """
    Convert numeric score to tier label.

    Args:
        score: Numeric score (0-100)

    Returns:
        Tier label: Poor, Fair, Good, Great, Excellent
    """
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Great"
    elif score >= 40:
        return "Good"
    elif score >= 20:
        return "Fair"
    else:
        return "Poor"


def get_bait_forecast_all_zones(db: Session, conditions: Dict) -> List[Dict]:
    """
    Get bait ratings for all bait species across all zones.

    Args:
        db: Database session
        conditions: Current environmental conditions

    Returns:
        List of dicts with bait ratings, sorted by best rating
    """
    # Only the 5 catchable bait species for the Bait tab (no mullet, croaker, or blue crab)
    bait_species_list = ['live_shrimp', 'menhaden', 'pinfish', 'mud_minnows', 'fiddler_crabs']
    results = []

    for bait in bait_species_list:
        # Calculate for each zone
        zone_ratings = []
        for zone_num in [1, 2, 3, 4, 5]:
            zone_id = f"Zone {zone_num}"
            rating = calculate_bait_rating(db, bait, zone_id, conditions)
            zone_ratings.append(rating)

        # Use best zone for this bait
        best = max(zone_ratings, key=lambda x: x['rating'])
        results.append(best)

    # Sort by rating descending
    return sorted(results, key=lambda x: x['rating'], reverse=True)


def get_zone_specific_bait_forecast(db: Session, zone_id: str, conditions: Dict) -> List[Dict]:
    """
    Get bait ratings for all bait species in a specific zone.

    Args:
        db: Database session
        zone_id: Zone identifier
        conditions: Current environmental conditions

    Returns:
        List of bait ratings for the zone, sorted by rating
    """
    # Only the 5 catchable bait species for the Bait tab (no mullet, croaker, or blue crab)
    bait_species_list = ['live_shrimp', 'menhaden', 'pinfish', 'mud_minnows', 'fiddler_crabs']
    results = []

    for bait in bait_species_list:
        rating = calculate_bait_rating(db, bait, zone_id, conditions)
        results.append(rating)

    return sorted(results, key=lambda x: x['rating'], reverse=True)
