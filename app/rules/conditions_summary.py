"""Conditions summary generator for fishing forecasts.

This module generates human-readable two-sentence summaries of current
fishing conditions based on environmental sub-scores and bite score tiers.
"""
from typing import Dict, Any, Optional
from app.rules.cold_north_wind import has_strong_north_wind_penalty, is_north_wind, is_cold_temp


def generate_conditions_summary(
    tide_score: float,
    wind_score: float,
    temp_score: float,
    bite_score: float,
    tide_state: str = None,
    wind_speed: float = None,
    wind_direction: Optional[str] = None,
    air_temp_f: Optional[float] = None,
    water_temp_f: Optional[float] = None
) -> str:
    """
    Generate a two-sentence conditions summary.

    Sentence 1: Describes current conditions (tide, wind, temp)
    Sentence 2: Describes fish behavior based on bite tier

    Args:
        tide_score: Tide sub-score (0-1)
        wind_score: Wind sub-score (0-1)
        temp_score: Temperature sub-score (0-1)
        bite_score: Overall bite score (0-100)
        tide_state: Optional tide state for additional context
        wind_speed: Optional wind speed (mph) for additional context
        wind_direction: Optional wind direction for north wind detection
        air_temp_f: Optional air temperature for cold temp detection
        water_temp_f: Optional water temperature for cold temp detection

    Returns:
        Two-sentence summary string
    """
    # Generate sentence 1 (conditions)
    sentence1 = _generate_conditions_sentence(
        tide_score, wind_score, temp_score, tide_state, wind_speed,
        wind_direction, air_temp_f, water_temp_f
    )

    # Generate sentence 2 (fish behavior) based on bite tier
    sentence2 = _generate_behavior_sentence(
        bite_score, wind_direction, wind_speed, air_temp_f, water_temp_f
    )

    return f"{sentence1} {sentence2}"


def _generate_conditions_sentence(
    tide_score: float,
    wind_score: float,
    temp_score: float,
    tide_state: str = None,
    wind_speed: float = None,
    wind_direction: Optional[str] = None,
    air_temp_f: Optional[float] = None,
    water_temp_f: Optional[float] = None
) -> str:
    """
    Generate first sentence describing current environmental conditions.

    Categorizes based on sub-score ranges:
    - High: >= 0.7
    - Mid: 0.4 - 0.69
    - Low: < 0.4

    Modified for cold north wind conditions.
    """
    # Check for cold north wind penalty
    strong_penalty = has_strong_north_wind_penalty(wind_direction, wind_speed, air_temp_f, water_temp_f)

    # Categorize each factor
    tide_level = _categorize_score(tide_score)
    wind_level = _categorize_score(wind_score)
    temp_level = _categorize_score(temp_score)

    # Build tide description
    if tide_level == "high":
        tide_desc = "Strong moving tide"
    elif tide_level == "mid":
        tide_desc = "Steady tide flow"
    else:  # low
        tide_desc = "Weak or slack tide"

    # Build wind description - modified for north winds
    if strong_penalty:
        wind_desc = "cold north wind"
    elif is_north_wind(wind_direction):
        wind_desc = "north wind"
    elif wind_level == "high":
        wind_desc = "good surface chop"
    elif wind_level == "mid":
        wind_desc = "moderate wind"
    else:  # low
        wind_desc = "calm water"

    # Build temperature description - temper for cold temps
    if strong_penalty or is_cold_temp(air_temp_f, water_temp_f):
        # Don't say "ideal" when it's cold
        temp_desc = "cold temperatures"
    elif temp_level == "high":
        temp_desc = "ideal temperatures"
    elif temp_level == "mid":
        temp_desc = "workable temperatures"
    else:  # low
        temp_desc = "a tough temperature range"

    # Use "mixed conditions" instead of overly positive framing when north wind + cold
    if strong_penalty and tide_level == "high":
        return f"{tide_desc}, but {wind_desc} and {temp_desc} create mixed conditions."
    else:
        return f"{tide_desc}, {wind_desc}, and {temp_desc}."


def _generate_behavior_sentence(
    bite_score: float,
    wind_direction: Optional[str] = None,
    wind_speed: Optional[float] = None,
    air_temp_f: Optional[float] = None,
    water_temp_f: Optional[float] = None
) -> str:
    """
    Generate second sentence describing fish behavior based on bite tier.

    Modified to account for cold north wind penalties.

    Tiers:
    - Good: 70-100
    - Moderate: 40-69
    - Slow: 0-39
    """
    # Check for cold north wind penalty
    strong_penalty = has_strong_north_wind_penalty(wind_direction, wind_speed, air_temp_f, water_temp_f)
    moderate_north = is_north_wind(wind_direction) and not strong_penalty

    if bite_score >= 70:
        # NEVER say "pushing shallow" under cold north wind penalty
        if strong_penalty:
            return "Cold north wind is pushing fish off the shallow flat. Expect them to hold deeper along edges; shallow bite may be slow."
        elif moderate_north:
            return "Fish are feeding but holding slightly deeper than normal due to north wind."
        else:
            return "Fish are feeding and pushing shallow."

    elif bite_score >= 40:
        if strong_penalty:
            return "Fish are cautious and holding deeper due to cold north wind."
        elif moderate_north:
            return "Fish are behaving normally but favoring deeper edges."
        else:
            return "Fish are behaving normally and conditions are stable."

    else:
        if strong_penalty:
            return "Cold conditions and north wind make for a slow bite; target deeper zones and edges."
        else:
            return "Fish are cautious and slow to bite."


def _categorize_score(score: float) -> str:
    """Categorize a sub-score as high, mid, or low."""
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "mid"
    else:
        return "low"


def get_top_active_species(species_forecasts: list, limit: int = 2) -> list:
    """
    Get the top N most active species by bite score.

    Args:
        species_forecasts: List of species forecast dicts with 'species' and 'bite_score'
        limit: Maximum number of species to return

    Returns:
        List of species dicts sorted by bite score (highest first)
    """
    if not species_forecasts:
        return []

    # Sort by bite score descending
    sorted_species = sorted(
        species_forecasts,
        key=lambda x: x.get('bite_score', 0),
        reverse=True
    )

    return sorted_species[:limit]
