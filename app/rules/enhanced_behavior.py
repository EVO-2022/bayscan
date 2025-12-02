"""
Enhanced Species Behavior Rules from 11-22-2025 Trip

These rules override or enhance base model predictions based on observed patterns.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def apply_redfish_rules(
    base_score: float,
    zone: str,
    tide_state: str,
    is_overcast: bool,
    time_of_day: str
) -> Dict:
    """
    Apply Redfish-specific behavior rules from 11-22-2025 trip.

    Rules:
    - Low tide + overcast + midday (Zones 2-3): minimum GOOD, confidence +0.15
    - Low tide → rising_start (Zones 2-3): bump one rating level, max EXCELLENT
    - Zones 1 and 4: use Zone 3 base rating but lower confidence (-0.05)

    Returns:
        Dict with adjusted score, confidence boost, min_tier, max_tier
    """
    adjustments = {
        'score_adjustment': 0.0,
        'confidence_boost': 0.0,
        'min_tier': None,
        'max_tier': None,
        'explanation': ''
    }

    # Rule 1: Low tide + overcast + midday in Zones 2-3
    if (tide_state == 'low' and is_overcast and time_of_day == 'midday' and
        zone in ['Zone 2', 'Zone 3']):
        adjustments['min_tier'] = 'DECENT'  # Minimum GOOD (using DECENT as close match)
        adjustments['confidence_boost'] = 0.15
        adjustments['explanation'] = 'Low tide overcast midday pattern - redfish often active'
        logger.info(f"Redfish rule triggered: low+overcast+midday in {zone}")

    # Rule 2: Low to rising transition in Zones 2-3
    if (tide_state == 'rising' and zone in ['Zone 2', 'Zone 3']):
        # Check if this is early rising (rising_start)
        # For now, treat all rising as potential
        adjustments['score_adjustment'] = 15.0  # Bump one tier (~20 points)
        adjustments['max_tier'] = 'HOT'  # Max EXCELLENT
        adjustments['explanation'] = 'Rising tide in prime zones - redfish move shallow'
        logger.info(f"Redfish rule triggered: rising tide in {zone}")

    # Rule 3: Zones 1 and 4 use Zone 3 baseline but reduced confidence
    if zone in ['Zone 1', 'Zone 4']:
        adjustments['confidence_boost'] = -0.05
        adjustments['explanation'] = 'Adjacent zone - using similar patterns with lower confidence'

    return adjustments


def apply_speckled_trout_rules(
    base_score: float,
    zone: str,
    tide_state: str
) -> Dict:
    """
    Apply Speckled Trout-specific behavior rules from 11-22-2025 trip.

    Rules:
    - Low tide in Zone 3: max FAIR
    - Rising_start in Zone 3: minimum GOOD, bump one level, max EXCELLENT, confidence +0.25

    Returns:
        Dict with adjusted score, confidence boost, min_tier, max_tier
    """
    adjustments = {
        'score_adjustment': 0.0,
        'confidence_boost': 0.0,
        'min_tier': None,
        'max_tier': None,
        'explanation': ''
    }

    # Rule 1: Low tide suppresses specks in Zone 3
    if tide_state == 'low' and zone == 'Zone 3':
        adjustments['max_tier'] = 'SLOW'  # Max FAIR (using SLOW as close match)
        adjustments['explanation'] = 'Low tide - specks avoid shallow Zone 3'
        logger.info(f"Speckled Trout rule triggered: low tide in {zone}")

    # Rule 2: Rising tide in Zone 3
    if tide_state == 'rising' and zone == 'Zone 3':
        adjustments['min_tier'] = 'DECENT'  # Minimum GOOD
        adjustments['score_adjustment'] = 15.0  # Bump one level
        adjustments['max_tier'] = 'HOT'  # Max EXCELLENT
        adjustments['confidence_boost'] = 0.25
        adjustments['explanation'] = 'Rising tide Zone 3 - prime speck conditions'
        logger.info(f"Speckled Trout rule triggered: rising tide in {zone}")

    return adjustments


def apply_white_trout_rules(
    base_score: float,
    zone: str,
    tide_state: str,
    hour: int
) -> Dict:
    """
    Apply White Trout-specific behavior rules from 11-22-2025 trip.

    Rules:
    - Low tide: max FAIR
    - Rising_start + sunset window (17:00-18:30) in Zone 3: minimum GOOD, bump one level, max EXCELLENT, confidence +0.3

    Returns:
        Dict with adjusted score, confidence boost, min_tier, max_tier
    """
    adjustments = {
        'score_adjustment': 0.0,
        'confidence_boost': 0.0,
        'min_tier': None,
        'max_tier': None,
        'explanation': ''
    }

    # Rule 1: Low tide suppresses white trout
    if tide_state == 'low':
        adjustments['max_tier'] = 'SLOW'  # Max FAIR
        adjustments['explanation'] = 'Low tide - white trout less active'
        logger.info(f"White Trout rule triggered: low tide")

    # Rule 2: Rising + sunset in Zone 3
    is_sunset_window = 17 <= hour <= 18.5
    if (tide_state == 'rising' and is_sunset_window and zone == 'Zone 3'):
        adjustments['min_tier'] = 'DECENT'  # Minimum GOOD
        adjustments['score_adjustment'] = 15.0  # Bump one level
        adjustments['max_tier'] = 'HOT'  # Max EXCELLENT
        adjustments['confidence_boost'] = 0.3
        adjustments['explanation'] = 'Rising tide + sunset in Zone 3 - peak white trout time'
        logger.info(f"White Trout rule triggered: rising+sunset in {zone}")

    return adjustments


def apply_croaker_rules(
    base_score: float,
    zone: str,
    tide_state: str
) -> Dict:
    """
    Apply Croaker-specific behavior rules from 11-22-2025 trip.

    Rules:
    - Low tide: max FAIR in Zones 3-4
    - Rising_start in Zones 3-4: minimum GOOD, bump one level, max EXCELLENT, confidence +0.25

    Returns:
        Dict with adjusted score, confidence boost, min_tier, max_tier
    """
    adjustments = {
        'score_adjustment': 0.0,
        'confidence_boost': 0.0,
        'min_tier': None,
        'max_tier': None,
        'explanation': ''
    }

    # Rule 1: Low tide in Zones 3-4
    if tide_state == 'low' and zone in ['Zone 3', 'Zone 4']:
        adjustments['max_tier'] = 'SLOW'  # Max FAIR
        adjustments['explanation'] = 'Low tide - croakers less active in mid zones'
        logger.info(f"Croaker rule triggered: low tide in {zone}")

    # Rule 2: Rising in Zones 3-4
    if tide_state == 'rising' and zone in ['Zone 3', 'Zone 4']:
        adjustments['min_tier'] = 'DECENT'  # Minimum GOOD
        adjustments['score_adjustment'] = 15.0  # Bump one level
        adjustments['max_tier'] = 'HOT'  # Max EXCELLENT
        adjustments['confidence_boost'] = 0.25
        adjustments['explanation'] = 'Rising tide in Zones 3-4 - croakers feeding actively'
        logger.info(f"Croaker rule triggered: rising tide in {zone}")

    return adjustments


def apply_enhanced_behavior_rules(
    species: str,
    base_score: float,
    zone: str,
    tide_state: str,
    cloud_cover: str,
    time_of_day: str,
    hour: int
) -> Dict:
    """
    Apply all enhanced behavior rules for a species.

    Args:
        species: Species key
        base_score: Base model bite score (0-100)
        zone: Zone identifier
        tide_state: Tide state (low, rising, high, falling)
        cloud_cover: Cloud cover (clear, partly_cloudy, overcast)
        time_of_day: Time of day (morning, midday, evening, night)
        hour: Current hour (0-23)

    Returns:
        Dictionary with all adjustments to apply
    """
    is_overcast = cloud_cover == 'overcast'

    if species == 'redfish':
        return apply_redfish_rules(base_score, zone, tide_state, is_overcast, time_of_day)
    elif species == 'speckled_trout':
        return apply_speckled_trout_rules(base_score, zone, tide_state)
    elif species == 'white_trout':
        return apply_white_trout_rules(base_score, zone, tide_state, hour)
    elif species == 'croaker':
        return apply_croaker_rules(base_score, zone, tide_state)
    else:
        # No enhanced rules for this species
        return {
            'score_adjustment': 0.0,
            'confidence_boost': 0.0,
            'min_tier': None,
            'max_tier': None,
            'explanation': ''
        }


def apply_tier_constraints(score: float, min_tier: Optional[str], max_tier: Optional[str]) -> float:
    """
    Apply tier constraints to a score.

    Tier ranges:
    - HOT: 80-100
    - DECENT: 50-79
    - SLOW: 20-49
    - UNLIKELY: 0-19

    Args:
        score: Current bite score
        min_tier: Minimum allowed tier
        max_tier: Maximum allowed tier

    Returns:
        Constrained score
    """
    # Map tiers to score ranges
    tier_min_scores = {
        'HOT': 80,
        'DECENT': 50,
        'SLOW': 20,
        'UNLIKELY': 0
    }

    tier_max_scores = {
        'HOT': 100,
        'DECENT': 79,
        'SLOW': 49,
        'UNLIKELY': 19
    }

    # Apply minimum constraint
    if min_tier and score < tier_min_scores[min_tier]:
        score = tier_min_scores[min_tier]

    # Apply maximum constraint
    if max_tier and score > tier_max_scores[max_tier]:
        score = tier_max_scores[max_tier]

    # Ensure score stays in valid range
    return max(0.0, min(100.0, score))
