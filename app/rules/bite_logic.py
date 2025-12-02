"""Bite probability scoring logic based on environmental conditions.

This module implements species-specific rules for calculating bite scores (0-100)
based on a weighted average of environmental sub-scores.
"""
from typing import Dict, Any, Optional


# Species-specific environmental factor weights
SPECIES_ENV_WEIGHTS = {
    "speckled_trout": {
        "tide": 1.0, "wind": 1.0, "temp": 1.0, "pressure": 1.0, "moon": 0.9, "cloud": 0.9
    },
    "redfish": {
        "tide": 0.8, "wind": 0.6, "temp": 0.7, "pressure": 0.7, "moon": 0.7, "cloud": 0.7
    },
    "flounder": {
        "tide": 0.9, "wind": 0.8, "temp": 0.8, "pressure": 0.8, "moon": 0.7, "cloud": 0.7
    },
    "sheepshead": {
        "tide": 0.7, "wind": 0.4, "temp": 0.6, "pressure": 0.5, "moon": 0.4, "cloud": 0.3
    },
    "black_drum": {
        "tide": 0.2, "wind": 0.2, "temp": 0.4, "pressure": 0.3, "moon": 0.3, "cloud": 0.2
    },
    "white_trout": {
        "tide": 0.7, "wind": 0.8, "temp": 0.9, "pressure": 0.8, "moon": 0.8, "cloud": 0.6
    },
    "croaker": {
        "tide": 0.6, "wind": 0.6, "temp": 0.7, "pressure": 0.6, "moon": 0.5, "cloud": 0.4
    },
    "tripletail": {
        "tide": 0.2, "wind": 0.1, "temp": 0.7, "pressure": 0.5, "moon": 0.3, "cloud": 0.5
    },
    "blue_crab": {
        "tide": 1.0, "wind": 0.4, "temp": 0.8, "pressure": 0.4, "moon": 0.4, "cloud": 0.2
    },
    "mullet": {
        "tide": 0.4, "wind": 0.6, "temp": 0.5, "pressure": 0.4, "moon": 0.3, "cloud": 0.3
    },
    "jack_crevalle": {
        "tide": 0.8, "wind": 0.9, "temp": 0.6, "pressure": 0.7, "moon": 0.6, "cloud": 0.6
    },
    "mackerel": {
        "tide": 0.9, "wind": 1.0, "temp": 0.7, "pressure": 0.7, "moon": 0.7, "cloud": 0.6
    },
    "shark": {
        "tide": 0.7, "wind": 0.6, "temp": 0.5, "pressure": 0.5, "moon": 0.4, "cloud": 0.3
    },
    "stingray": {
        "tide": 0.1, "wind": 0.1, "temp": 0.2, "pressure": 0.2, "moon": 0.2, "cloud": 0.1
    }
}


def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def get_bite_label(score: float) -> str:
    """Convert bite score to label (unchanged from original)."""
    if score >= 71:
        return "Hot"
    elif score >= 41:
        return "Decent"
    elif score >= 21:
        return "Slow"
    else:
        return "Unlikely"


def get_bite_tier(score: float) -> str:
    """Get bite tier for depth behavior lookup."""
    if score >= 70:
        return "good"
    elif score >= 40:
        return "moderate"
    else:
        return "slow"


def calculate_bite_score(
    species: str,
    running_factor: float,
    conditions: Dict[str, Any],
    safety_level: Optional[str] = None,
    safety_score: Optional[int] = None
) -> float:
    """
    Calculate bite score (0-100) for a species given environmental conditions.

    Args:
        species: Species name (lowercase with underscores)
        running_factor: Seasonal running factor (0-1)
        conditions: Dictionary with environmental data:
            - tide_state: 'rising', 'falling', 'slack'
            - tide_change_rate: 0-1 (how fast tide is moving)
            - time_of_day: 'night', 'dawn', 'day', 'dusk'
            - wind_speed: mph (IMPORTANT: always mph, never knots)
            - wind_direction: compass direction
            - temperature: Fahrenheit
            - pressure_trend: 'rising', 'falling', 'stable'
            - cloud_cover: 'clear', 'partly_cloudy', 'overcast'
            - conditions: weather condition string
            - moon_phase: 0-1 (0=new, 0.5=full)
        safety_level: Optional marine safety level ('SAFE', 'CAUTION', 'UNSAFE')
        safety_score: Optional marine safety score (0-100)

    Returns:
        Bite score from 0-100
    """
    # Start with base score from seasonality
    if running_factor < 0.1:
        return 0.0  # Species not present

    # Get species-specific environmental score using weighted sub-scores
    env_score = _get_species_environmental_score(species, conditions)

    # Multiply seasonality by environmental conditions
    # bite_score = running_factor * environmental_score * 100
    total_score = running_factor * env_score * 100

    # Apply safety penalty if provided
    if safety_level and safety_score is not None:
        total_score = apply_safety_penalty(total_score, safety_level, safety_score)

    # Clamp to 0-100
    return clamp(total_score, 0.0, 100.0)


def _get_species_environmental_score(species: str, conditions: Dict[str, Any]) -> float:
    """
    Get environmental suitability score (0-1) for a species.

    Uses weighted average of sub-scores:
    env_score = (w_tide * tide_score + w_wind * wind_score + w_temp * temp_score +
                 w_pressure * pressure_score + w_moon * moon_score + w_cloud * cloud_score)
                / (w_tide + w_wind + w_temp + w_pressure + w_moon + w_cloud)

    Each sub-score is clamped to [0.0, 1.0] before weighting.
    Final environmental_score is clamped to [0.0, 1.0].
    """
    # Get weights for this species (default to all 0.5 if species not found)
    weights = SPECIES_ENV_WEIGHTS.get(species, {
        "tide": 0.5, "wind": 0.5, "temp": 0.5,
        "pressure": 0.5, "moon": 0.5, "cloud": 0.5
    })

    # Extract conditions
    tide_state = conditions.get('tide_state', 'slack')
    tide_change_rate = conditions.get('tide_change_rate', 0.0)
    time_of_day = conditions.get('time_of_day', 'day')
    wind_speed = conditions.get('wind_speed', 0.0)  # ALWAYS in MPH
    temperature = conditions.get('temperature', 70.0)  # Air temperature
    water_temperature = conditions.get('water_temperature', None)  # Water temperature (may be None)
    pressure_trend = conditions.get('pressure_trend', 'stable')
    cloud_cover = conditions.get('cloud_cover', 'clear')
    weather_conditions = conditions.get('conditions', '').lower()
    moon_phase = conditions.get('moon_phase', 0.0)

    # Calculate each sub-score (0-1) based on species
    tide_score = clamp(_calculate_tide_score(species, tide_state, tide_change_rate, time_of_day))
    wind_score = clamp(_calculate_wind_score(species, wind_speed, weather_conditions))
    temp_score = clamp(_calculate_temp_score(species, temperature, water_temperature))
    pressure_score = clamp(_calculate_pressure_score(species, pressure_trend))
    moon_score = clamp(_calculate_moon_score(species, moon_phase))
    cloud_score = clamp(_calculate_cloud_score(species, cloud_cover))

    # Weighted average
    w_tide = weights["tide"]
    w_wind = weights["wind"]
    w_temp = weights["temp"]
    w_pressure = weights["pressure"]
    w_moon = weights["moon"]
    w_cloud = weights["cloud"]

    total_weight = w_tide + w_wind + w_temp + w_pressure + w_moon + w_cloud

    if total_weight == 0:
        return 0.5  # Default if no weights

    env_score = (
        w_tide * tide_score +
        w_wind * wind_score +
        w_temp * temp_score +
        w_pressure * pressure_score +
        w_moon * moon_score +
        w_cloud * cloud_score
    ) / total_weight

    # Clamp final environmental score
    return clamp(env_score, 0.0, 1.0)


# ============================================================================
# SUB-SCORE FUNCTIONS (each returns 0-1 score before clamping)
# ============================================================================

def _calculate_tide_score(species: str, tide_state: str, tide_change_rate: float, time_of_day: str) -> float:
    """Calculate tide sub-score (0-1) based on species preferences."""
    score = 0.5  # baseline

    # Species-specific tide preferences
    if species == 'speckled_trout':
        # Love moving water
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.3:
            score = 0.9
        elif tide_state in ['rising', 'falling']:
            score = 0.7
        elif tide_state == 'slack':
            score = 0.3

    elif species == 'redfish':
        # Moving water is key
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.2:
            score = 0.85
        elif tide_state in ['rising', 'falling']:
            score = 0.65
        elif tide_state == 'slack':
            score = 0.4

    elif species == 'flounder':
        # LOVE falling tide
        if tide_state == 'falling' and tide_change_rate > 0.3:
            score = 0.95
        elif tide_state == 'falling':
            score = 0.75
        elif tide_state == 'rising' and tide_change_rate > 0.3:
            score = 0.65
        elif tide_state == 'slack':
            score = 0.3

    elif species == 'sheepshead':
        # Prefer gentle movement or slack around structure
        if tide_change_rate < 0.4:
            score = 0.75
        if tide_state == 'slack':
            score = 0.70
        else:
            score = 0.55

    elif species == 'black_drum':
        # Less tide dependent
        if tide_state in ['rising', 'falling']:
            score = 0.65
        else:
            score = 0.55

    elif species == 'white_trout':
        # Prefer moving water
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.25:
            score = 0.8
        elif tide_state == 'slack':
            score = 0.4

    elif species == 'croaker':
        # Moderate movement
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.2:
            score = 0.75
        else:
            score = 0.55

    elif species == 'tripletail':
        # Not very tide dependent
        if tide_state in ['rising', 'falling']:
            score = 0.6
        else:
            score = 0.5

    elif species == 'blue_crab':
        # Prefer moving water (crabs move with tide)
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.2:
            score = 0.9
        elif tide_state == 'slack':
            score = 0.4

    elif species == 'mullet':
        # Like moving water
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.2:
            score = 0.7
        else:
            score = 0.5

    elif species == 'jack_crevalle':
        # Love moving water
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.3:
            score = 0.85
        elif tide_state == 'slack':
            score = 0.35

    elif species == 'mackerel':
        # Like moving water
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.3:
            score = 0.85
        elif tide_state == 'slack':
            score = 0.35

    elif species == 'shark':
        # Prefer moving water
        if tide_state in ['rising', 'falling'] and tide_change_rate > 0.2:
            score = 0.8
        elif tide_state == 'slack':
            score = 0.4

    elif species == 'stingray':
        # Like some movement
        if tide_state in ['rising', 'falling']:
            score = 0.65
        else:
            score = 0.5

    return score


def _calculate_wind_score(species: str, wind_speed: float, weather_conditions: str) -> float:
    """Calculate wind sub-score (0-1). Wind speed is ALWAYS in MPH."""
    score = 0.5

    # Penalize severe weather for all species
    if any(word in weather_conditions for word in ['storm', 'thunder', 'severe']):
        return 0.1

    # Species-specific wind preferences (wind in MPH)
    if species == 'speckled_trout':
        if wind_speed < 10:
            score = 0.8
        elif wind_speed < 15:
            score = 0.6
        elif wind_speed < 20:
            score = 0.4
        else:
            score = 0.2

    elif species == 'redfish':
        # Can handle more wind
        if wind_speed < 15:
            score = 0.75
        elif wind_speed < 20:
            score = 0.6
        elif wind_speed < 25:
            score = 0.45
        else:
            score = 0.3

    elif species == 'flounder':
        if wind_speed < 12:
            score = 0.75
        elif wind_speed < 20:
            score = 0.55
        else:
            score = 0.3

    elif species == 'sheepshead':
        # Can handle wind well
        if wind_speed < 30:
            score = 0.7
        else:
            score = 0.3

    elif species == 'black_drum':
        # Can handle wind well
        if wind_speed < 20:
            score = 0.75
        elif wind_speed < 30:
            score = 0.6
        else:
            score = 0.35

    elif species == 'white_trout':
        # Prefer calm to moderate
        if wind_speed < 10:
            score = 0.8
        elif wind_speed < 20:
            score = 0.55
        else:
            score = 0.35

    elif species == 'croaker':
        if wind_speed < 12:
            score = 0.75
        elif wind_speed < 20:
            score = 0.55
        else:
            score = 0.3

    elif species == 'tripletail':
        # Calm to light wind is best for sight fishing
        if wind_speed < 10:
            score = 0.85
        elif wind_speed < 20:
            score = 0.45
        else:
            score = 0.25

    elif species == 'blue_crab':
        # Can handle moderate wind
        if wind_speed < 15:
            score = 0.75
        elif wind_speed < 25:
            score = 0.55
        else:
            score = 0.35

    elif species == 'mullet':
        # Moderate wind can stir surface
        if 5 < wind_speed < 15:
            score = 0.8
        elif wind_speed < 5:
            score = 0.6
        elif wind_speed < 25:
            score = 0.45
        else:
            score = 0.3

    elif species == 'jack_crevalle':
        # Can handle moderate wind, stirs bait
        if 5 < wind_speed < 20:
            score = 0.8
        elif wind_speed < 5:
            score = 0.6
        elif wind_speed < 25:
            score = 0.5
        else:
            score = 0.3

    elif species == 'mackerel':
        if wind_speed < 15:
            score = 0.8
        elif wind_speed < 20:
            score = 0.5
        else:
            score = 0.25

    elif species == 'shark':
        # Moderate wind can stir baitfish
        if 5 < wind_speed < 20:
            score = 0.75
        elif wind_speed < 25:
            score = 0.6
        else:
            score = 0.35

    elif species == 'stingray':
        # Not very sensitive
        if wind_speed < 25:
            score = 0.65
        else:
            score = 0.4

    return score


def _calculate_temp_score(species: str, temperature: float, water_temperature: float = None) -> float:
    """
    Calculate temperature sub-score (0-1).

    Args:
        species: Species name
        temperature: Air temperature in Fahrenheit
        water_temperature: Water temperature in Fahrenheit (if available)

    Returns:
        Temperature score (0-1)

    Note:
        If water_temperature is provided, it is used for scoring.
        Otherwise, falls back to air temperature.
        Fish are sensitive to WATER temperature, not air temperature.
    """
    # Use water temp if available, otherwise fall back to air temp
    effective_temp = water_temperature if water_temperature is not None else temperature

    score = 0.5

    if species == 'speckled_trout':
        if 60 <= effective_temp <= 80:
            score = 0.9
        elif 55 <= effective_temp <= 90:
            score = 0.65
        else:
            score = 0.3

    elif species == 'redfish':
        if 55 <= effective_temp <= 85:
            score = 0.85
        elif effective_temp >= 50 and effective_temp <= 95:
            score = 0.6
        elif effective_temp < 50:
            score = 0.3
        else:
            score = 0.4

    elif species == 'flounder':
        if 60 <= effective_temp <= 80:
            score = 0.85
        elif 55 <= effective_temp <= 90:
            score = 0.65
        else:
            score = 0.35

    elif species == 'sheepshead':
        if effective_temp >= 50:
            score = 0.75
        elif effective_temp >= 45:
            score = 0.55
        else:
            score = 0.3

    elif species == 'black_drum':
        # Tolerant of cold water
        if 50 <= effective_temp <= 75:
            score = 0.85
        elif effective_temp >= 45 and effective_temp <= 85:
            score = 0.65
        else:
            score = 0.4

    elif species == 'white_trout':
        if 55 <= effective_temp <= 85:
            score = 0.8
        elif effective_temp >= 50 and effective_temp <= 95:
            score = 0.55
        else:
            score = 0.25

    elif species == 'croaker':
        # Like warm
        if effective_temp > 70:
            score = 0.85
        elif effective_temp >= 60:
            score = 0.65
        else:
            score = 0.3

    elif species == 'tripletail':
        # Warm water species
        if effective_temp > 75:
            score = 0.9
        elif effective_temp > 70:
            score = 0.75
        elif effective_temp >= 65:
            score = 0.5
        else:
            score = 0.2

    elif species == 'blue_crab':
        # Warm water species, very active in heat
        if effective_temp > 75:
            score = 0.95
        elif effective_temp > 70:
            score = 0.8
        elif effective_temp >= 60:
            score = 0.5
        else:
            score = 0.2

    elif species == 'mullet':
        # Love warm
        if effective_temp > 75:
            score = 0.9
        elif effective_temp >= 60:
            score = 0.65
        else:
            score = 0.25

    elif species == 'jack_crevalle':
        # Warm water
        if effective_temp > 75:
            score = 0.9
        elif effective_temp > 70:
            score = 0.75
        elif effective_temp >= 65:
            score = 0.5
        else:
            score = 0.25

    elif species == 'mackerel':
        if 65 <= effective_temp <= 85:
            score = 0.8
        elif effective_temp >= 60 and effective_temp <= 90:
            score = 0.6
        else:
            score = 0.4

    elif species == 'shark':
        # Warm water species
        if effective_temp > 75:
            score = 0.9
        elif effective_temp > 70:
            score = 0.75
        elif effective_temp >= 65:
            score = 0.55
        else:
            score = 0.2

    elif species == 'stingray':
        # Very warm-water dependent
        if effective_temp > 75:
            score = 0.9
        elif effective_temp >= 65:
            score = 0.6
        else:
            score = 0.2

    return score


def _calculate_pressure_score(species: str, pressure_trend: str) -> float:
    """Calculate pressure sub-score (0-1)."""
    score = 0.5

    if species == 'speckled_trout':
        # Falling (pre-front) is good
        if pressure_trend == 'falling':
            score = 0.85
        elif pressure_trend == 'stable':
            score = 0.6
        else:  # rising
            score = 0.45

    elif species == 'redfish':
        # Stable or falling is good
        if pressure_trend in ['falling', 'stable']:
            score = 0.75
        else:
            score = 0.55

    elif species == 'flounder':
        # Stable is best
        if pressure_trend == 'stable':
            score = 0.85
        elif pressure_trend == 'falling':
            score = 0.65
        else:
            score = 0.55

    elif species == 'sheepshead':
        # Not very sensitive
        score = 0.6

    elif species == 'black_drum':
        # Stable or rising is good
        if pressure_trend in ['stable', 'rising']:
            score = 0.8
        else:
            score = 0.6

    elif species == 'white_trout':
        # Falling is excellent
        if pressure_trend == 'falling':
            score = 0.9
        elif pressure_trend == 'stable':
            score = 0.7
        else:
            score = 0.5

    elif species == 'croaker':
        # Stable is good
        if pressure_trend == 'stable':
            score = 0.75
        else:
            score = 0.6

    elif species == 'tripletail':
        # Stable is best
        if pressure_trend == 'stable':
            score = 0.8
        elif pressure_trend == 'falling':
            score = 0.65
        else:
            score = 0.55

    elif species == 'blue_crab':
        # Stable or rising is good
        if pressure_trend in ['stable', 'rising']:
            score = 0.75
        else:
            score = 0.45

    elif species == 'mullet':
        # Not very sensitive
        score = 0.6

    elif species == 'jack_crevalle':
        # Falling (pre-front) is good
        if pressure_trend == 'falling':
            score = 0.8
        elif pressure_trend == 'stable':
            score = 0.65
        else:
            score = 0.55

    elif species == 'mackerel':
        # Stable is good
        if pressure_trend == 'stable':
            score = 0.75
        elif pressure_trend == 'falling':
            score = 0.65
        else:
            score = 0.6

    elif species == 'shark':
        # Less sensitive, slight preference for falling
        if pressure_trend == 'falling':
            score = 0.65
        else:
            score = 0.6

    elif species == 'stingray':
        # Stable is better
        if pressure_trend == 'stable':
            score = 0.7
        else:
            score = 0.55

    return score


def _calculate_moon_score(species: str, moon_phase: float) -> float:
    """Calculate moon phase sub-score (0-1).
    moon_phase: 0=new, 0.5=full, 1.0=new again
    """
    # For most species, new and full moon are better (stronger tides)
    # Distance from nearest new (0.0) or full (0.5) moon
    distance_to_new = min(abs(moon_phase - 0.0), abs(moon_phase - 1.0))
    distance_to_full = abs(moon_phase - 0.5)
    distance_to_extreme = min(distance_to_new, distance_to_full)

    # Convert to score (0 distance = 1.0 score, 0.25 distance = 0.5 score)
    moon_score = 1.0 - (distance_to_extreme * 2.0)
    moon_score = max(0.5, min(1.0, moon_score))  # Clamp between 0.5 and 1.0

    # Species adjustments
    if species in ['speckled_trout', 'redfish', 'flounder']:
        # Strong moon sensitivity
        return moon_score
    elif species in ['shark', 'jack_crevalle', 'mackerel']:
        # Moderate moon sensitivity
        return 0.5 + (moon_score - 0.5) * 0.7
    else:
        # Less moon sensitive
        return 0.5 + (moon_score - 0.5) * 0.5


def _calculate_cloud_score(species: str, cloud_cover: str) -> float:
    """Calculate cloud cover sub-score (0-1)."""
    score = 0.5

    if species == 'speckled_trout':
        # Prefer overcast/partly cloudy
        if cloud_cover == 'overcast':
            score = 0.85
        elif cloud_cover == 'partly_cloudy':
            score = 0.75
        else:
            score = 0.55

    elif species == 'redfish':
        # Less picky
        score = 0.65

    elif species == 'flounder':
        # Less dependent
        score = 0.6

    elif species == 'sheepshead':
        # Not very sensitive
        score = 0.6

    elif species == 'black_drum':
        # Not very sensitive
        score = 0.6

    elif species == 'white_trout':
        # Overcast is good
        if cloud_cover in ['overcast', 'mostly_cloudy']:
            score = 0.75
        else:
            score = 0.6

    elif species == 'croaker':
        # Overcast ok
        score = 0.65

    elif species == 'tripletail':
        # Clear to partly cloudy best for sight fishing
        if cloud_cover in ['clear', 'partly_cloudy']:
            score = 0.8
        else:
            score = 0.5

    elif species == 'blue_crab':
        # Not very sensitive
        score = 0.6

    elif species == 'mullet':
        # Not very sensitive
        score = 0.6

    elif species == 'jack_crevalle':
        # Slightly prefer overcast
        if cloud_cover == 'overcast':
            score = 0.7
        else:
            score = 0.6

    elif species == 'mackerel':
        # Prefer clearer conditions
        if cloud_cover == 'clear':
            score = 0.75
        elif cloud_cover == 'partly_cloudy':
            score = 0.65
        else:
            score = 0.5

    elif species == 'shark':
        # Not very sensitive
        score = 0.6

    elif species == 'stingray':
        # Not very sensitive
        score = 0.6

    return score


def apply_safety_penalty(bite_score: float, safety_level: str, safety_score: int) -> float:
    """
    Apply marine safety penalty to bite score.

    When conditions are unsafe, we reduce the bite score to reflect that
    fishing may not be advisable even if the fish are biting.

    Args:
        bite_score: Original bite score (0-100)
        safety_level: 'SAFE', 'CAUTION', or 'UNSAFE'
        safety_score: Marine safety score (0-100)

    Returns:
        Adjusted bite score with safety penalty applied
    """
    from app.config import config

    penalties = config.marine_bite_score_penalties

    if safety_level == 'UNSAFE':
        # Severe conditions - apply maximum penalty
        penalty = penalties['UNSAFE']
        return bite_score - penalty

    elif safety_level == 'CAUTION':
        # Moderate conditions - apply scaled penalty based on safety score
        max_penalty = penalties['CAUTION']
        # Scale penalty: lower safety score = higher penalty
        # Safety score 50-80 = CAUTION range
        # At 50 (low caution), apply full penalty
        # At 80 (high caution), apply minimal penalty
        if safety_score < 50:
            penalty = max_penalty
        else:
            # Linear scale from max_penalty at 50 to 0 at 80
            penalty = max_penalty * (80 - safety_score) / 30
        return bite_score - penalty

    else:
        # SAFE - no penalty
        return bite_score
