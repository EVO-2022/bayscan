"""Species depth behavior patterns at Belle Fontaine Dock.

This module defines species-specific depth preferences and behavior patterns
based on bite score tiers (good, moderate, slow).

Dock depth profile (shallow shelf):
- 2 ft at rocky shoreline
- 4-5 ft at end of dock
- 7 ft at ~500 ft off shore
"""
from typing import Optional, Dict
from app.rules.cold_north_wind import (
    get_depth_shift,
    apply_depth_shift,
    get_cold_north_wind_depth_note,
    has_strong_north_wind_penalty
)

# Dock depth behavior by species and bite tier
DOCK_DEPTH_BEHAVIOR = {
    "speckled_trout": {
        "good":     {"depth": "shallow-mid", "range_ft": (2, 4), "note": "Push shallow along rocks and dock edges"},
        "moderate": {"depth": "mid",         "range_ft": (3, 5), "note": "Cruising around dock and nearby drop"},
        "slow":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Holding off the dock on deeper edge"},
    },
    "redfish": {
        "good":     {"depth": "shallow",     "range_ft": (1, 3), "note": "Roaming tight to rocks and flooded shoreline"},
        "moderate": {"depth": "shallow-mid", "range_ft": (2, 4), "note": "Working around dock and nearby structure"},
        "slow":     {"depth": "mid",         "range_ft": (3, 5), "note": "Sticking to slower current lanes"},
    },
    "flounder": {
        "good":     {"depth": "mid",         "range_ft": (3, 5), "note": "Laying on bottom along dock shadow line"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Sitting on slope from dock to deeper edge"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Holding on deeper, slower bottom"},
    },
    "sheepshead": {
        "good":     {"depth": "mid",         "range_ft": (3, 5), "note": "Tight to pilings and dock structure"},
        "moderate": {"depth": "mid",         "range_ft": (3, 5), "note": "Hugging structure, picking at barnacles"},
        "slow":     {"depth": "mid-deep",    "range_ft": (4, 6), "note": "Staying glued to deepest pilings"},
    },
    "black_drum": {
        "good":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Rooting bottom off the dock edge"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Slow cruising along deeper mud"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Laid up on soft bottom"},
    },
    "white_trout": {
        "good":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Schooling off the dock edge"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Loose schools just off structure"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Suspended or tight to bottom deeper"},
    },
    "croaker": {
        "good":     {"depth": "mid",         "range_ft": (3, 5), "note": "On bottom around dock and nearby slope"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Scattered along deeper edge"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Holding tight to deeper mud"},
    },
    "tripletail": {
        "good":     {"depth": "surface-mid", "range_ft": (2, 5), "note": "Suspended near surface around debris or dock"},
        "moderate": {"depth": "mid",         "range_ft": (3, 5), "note": "Holding to any floating cover or pilings"},
        "slow":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Staying tight to limited structure"},
    },
    "blue_crab": {
        "good":     {"depth": "shallow-mid", "range_ft": (2, 5), "note": "Active along bottom from rocks to dock edge"},
        "moderate": {"depth": "mid",         "range_ft": (3, 5), "note": "Walking bottom around dock"},
        "slow":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Less active, hugging bottom in deeper water"},
    },
    "mullet": {
        "good":     {"depth": "shallow",     "range_ft": (1, 3), "note": "Schooling visibly around rocks and shoreline"},
        "moderate": {"depth": "shallow-mid", "range_ft": (2, 4), "note": "Cruising the shelf near the dock"},
        "slow":     {"depth": "mid",         "range_ft": (3, 5), "note": "Deeper and more scattered"},
    },
    "jack_crevalle": {
        "good":     {"depth": "surface-mid", "range_ft": (2, 5), "note": "Roaming fast across the shelf when bait stacks"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Running edges and deeper bait lines"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Mostly absent near the dock"},
    },
    "mackerel": {
        "good":     {"depth": "surface-mid", "range_ft": (2, 5), "note": "Running bait lines across the shelf"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "On deeper edges when bait is out"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Mostly off the dock area"},
    },
    "shark": {
        "good":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Cruising deeper edge for scent and bait"},
        "moderate": {"depth": "deep",        "range_ft": (5, 7), "note": "Off the shelf, following channels"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Largely away from dock zone"},
    },
    "stingray": {
        "good":     {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Gliding and feeding on deeper soft bottom"},
        "moderate": {"depth": "mid-deep",    "range_ft": (4, 7), "note": "Consistent on flat mud/sand bottom"},
        "slow":     {"depth": "deep",        "range_ft": (5, 7), "note": "Laying mostly inactive on bottom"},
    },
}


def get_depth_behavior(
    species: str,
    bite_tier: str,
    wind_direction: Optional[str] = None,
    wind_speed: Optional[float] = None,
    air_temp_f: Optional[float] = None,
    water_temp_f: Optional[float] = None
) -> dict:
    """
    Get depth behavior for a species at a given bite tier.

    Applies cold north wind penalties to shift fish deeper when appropriate.

    Args:
        species: Species slug (e.g., "speckled_trout")
        bite_tier: "good", "moderate", or "slow"
        wind_direction: Cardinal wind direction (optional, for north wind penalty)
        wind_speed: Wind speed in mph (optional, for north wind penalty)
        air_temp_f: Air temperature in F (optional, for cold temp check)
        water_temp_f: Water temperature in F (optional, for cold temp check)

    Returns:
        Dict with 'depth', 'range_ft', and 'note' keys, or None if not found
    """
    if species not in DOCK_DEPTH_BEHAVIOR:
        return None

    behavior = DOCK_DEPTH_BEHAVIOR[species].get(bite_tier)
    if not behavior:
        return None

    # Check if cold north wind penalty applies
    if wind_direction:
        depth_shift = get_depth_shift(species, wind_direction, wind_speed, air_temp_f, water_temp_f)

        if depth_shift > 0:
            # Create a copy to avoid modifying the original
            modified_behavior = behavior.copy()

            # Apply depth shift
            original_range = modified_behavior['range_ft']
            new_range = apply_depth_shift(original_range, depth_shift)
            modified_behavior['range_ft'] = new_range

            # Update depth category if needed
            min_ft, max_ft = new_range
            avg_depth = (min_ft + max_ft) / 2

            if avg_depth <= 2.5:
                modified_behavior['depth'] = 'shallow'
            elif avg_depth <= 4.5:
                modified_behavior['depth'] = 'shallow-mid' if min_ft < 3 else 'mid'
            elif avg_depth <= 6:
                modified_behavior['depth'] = 'mid' if max_ft < 6 else 'mid-deep'
            else:
                modified_behavior['depth'] = 'deep'

            # Update note for cold north wind
            strong_penalty = has_strong_north_wind_penalty(
                wind_direction, wind_speed, air_temp_f, water_temp_f
            )
            modified_behavior['note'] = get_cold_north_wind_depth_note(
                species, behavior['note'], strong_penalty
            )

            return modified_behavior

    return behavior


def format_depth_range(range_ft: tuple) -> str:
    """Format depth range tuple as string.

    Args:
        range_ft: Tuple of (min_ft, max_ft)

    Returns:
        Formatted string like "2-4 ft"
    """
    if not range_ft or len(range_ft) != 2:
        return "N/A"

    min_ft, max_ft = range_ft
    if min_ft == max_ft:
        return f"{min_ft} ft"
    return f"{min_ft}-{max_ft} ft"
