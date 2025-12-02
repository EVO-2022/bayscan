"""Cold north wind detection and penalty logic for shallow water fishing.

This module detects cold north wind conditions and applies penalties to shallow water
fishing behavior, pushing fish deeper and adjusting zone recommendations.
"""

from typing import Optional, Dict, Tuple


# North-derived wind directions
NORTH_WIND_DIRECTIONS = ['N', 'NNE', 'NE', 'NNW', 'NW']

# Cold temperature threshold
COLD_TEMP_THRESHOLD_F = 60.0

# Shallow depth threshold
SHALLOW_DEPTH_THRESHOLD_FT = 6.0


def is_north_wind(wind_direction: Optional[str]) -> bool:
    """Check if wind is from a north-derived direction.

    Args:
        wind_direction: Cardinal wind direction (e.g., 'N', 'NE', 'SW')

    Returns:
        True if wind is from north-derived direction
    """
    if not wind_direction:
        return False
    return wind_direction.upper() in NORTH_WIND_DIRECTIONS


def is_cold_temp(air_temp_f: Optional[float], water_temp_f: Optional[float]) -> bool:
    """Check if temperatures are cold.

    Args:
        air_temp_f: Air temperature in Fahrenheit
        water_temp_f: Water temperature in Fahrenheit

    Returns:
        True if either temp is <= 60°F
    """
    if air_temp_f and air_temp_f <= COLD_TEMP_THRESHOLD_F:
        return True
    if water_temp_f and water_temp_f <= COLD_TEMP_THRESHOLD_F:
        return True
    return False


def is_shallow_location(average_depth_ft: float = 4.5) -> bool:
    """Check if location is considered shallow.

    Belle Fontaine Dock average depth is ~4.5 ft, which is < 6 ft threshold.

    Args:
        average_depth_ft: Average depth at location

    Returns:
        True if depth < 6 ft
    """
    return average_depth_ft < SHALLOW_DEPTH_THRESHOLD_FT


def has_strong_north_wind_penalty(
    wind_direction: Optional[str],
    wind_speed: Optional[float],
    air_temp_f: Optional[float],
    water_temp_f: Optional[float]
) -> bool:
    """Check if strong north wind penalty conditions are met.

    Penalty applies when:
    - Wind is from north
    - Wind speed >= 10 mph
    - Temperature is cold (air or water <= 60°F)

    Args:
        wind_direction: Cardinal wind direction
        wind_speed: Wind speed in mph
        air_temp_f: Air temperature in Fahrenheit
        water_temp_f: Water temperature in Fahrenheit

    Returns:
        True if strong penalty should apply
    """
    if not is_north_wind(wind_direction):
        return False

    if not wind_speed or wind_speed < 10.0:
        return False

    return is_cold_temp(air_temp_f, water_temp_f)


def has_moderate_north_wind_penalty(
    wind_direction: Optional[str],
    air_temp_f: Optional[float],
    water_temp_f: Optional[float]
) -> bool:
    """Check if moderate north wind penalty conditions are met.

    Penalty applies when:
    - Wind is from north
    - In shallow water
    - Even without strong winds (< 10 mph)

    Args:
        wind_direction: Cardinal wind direction
        air_temp_f: Air temperature in Fahrenheit
        water_temp_f: Water temperature in Fahrenheit

    Returns:
        True if moderate penalty should apply
    """
    if not is_north_wind(wind_direction):
        return False

    # In shallow location (Belle Fontaine is shallow)
    if not is_shallow_location():
        return False

    return True  # Any north wind in shallow water gets some penalty


def get_depth_shift(
    species: str,
    wind_direction: Optional[str],
    wind_speed: Optional[float],
    air_temp_f: Optional[float],
    water_temp_f: Optional[float]
) -> int:
    """Get depth shift in feet for cold north wind conditions.

    Args:
        species: Species key (e.g., 'speckled_trout')
        wind_direction: Cardinal wind direction
        wind_speed: Wind speed in mph
        air_temp_f: Air temperature in Fahrenheit
        water_temp_f: Water temperature in Fahrenheit

    Returns:
        Depth shift in feet (0-3)
    """
    # Strong penalty: shift 2-3 ft deeper
    if has_strong_north_wind_penalty(wind_direction, wind_speed, air_temp_f, water_temp_f):
        # Shallow species (trout, reds, mullet) shift more
        if species in ['speckled_trout', 'redfish', 'mullet']:
            return 3
        # Mid-depth species shift moderately
        elif species in ['white_trout', 'croaker', 'blue_crab']:
            return 2
        # Deep species shift less (already deep)
        else:
            return 1

    # Moderate penalty: shift 1 ft deeper
    elif has_moderate_north_wind_penalty(wind_direction, air_temp_f, water_temp_f):
        if species in ['speckled_trout', 'redfish', 'mullet']:
            return 1
        return 0

    return 0


def apply_depth_shift(original_range: Tuple[int, int], shift_ft: int) -> Tuple[int, int]:
    """Apply depth shift to original depth range.

    Args:
        original_range: Original depth range tuple (min_ft, max_ft)
        shift_ft: Depth shift in feet

    Returns:
        New depth range tuple
    """
    min_ft, max_ft = original_range

    # Shift both min and max deeper
    new_min = min_ft + shift_ft
    new_max = max_ft + shift_ft

    # Cap at 7 ft (max dock area depth)
    new_min = min(new_min, 7)
    new_max = min(new_max, 7)

    return (new_min, new_max)


def get_cold_north_wind_depth_note(
    species: str,
    original_note: str,
    strong_penalty: bool
) -> str:
    """Get modified depth note for cold north wind conditions.

    Args:
        species: Species key
        original_note: Original depth behavior note
        strong_penalty: True if strong penalty applies

    Returns:
        Modified depth note
    """
    if strong_penalty:
        # Strong penalty: emphasize deeper holding
        if species in ['speckled_trout', 'redfish']:
            return "Holding deeper along edges; shallow bite may be slow"
        elif species in ['black_drum', 'flounder']:
            return "Off the dock edge on the deeper side, not in skinniest water"
        elif species in ['white_trout', 'croaker']:
            return "Pushed deeper by cold north wind"
        else:
            return "Holding deeper than normal"
    else:
        # Moderate penalty: slight modification
        return f"{original_note.rstrip('.')} (pushed slightly deeper by north wind)"
