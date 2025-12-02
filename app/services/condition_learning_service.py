"""
Condition Learning Service - Tracks effectiveness of conditions and rigs under conditions.

Updates two tables on each catch:
1. zone_condition_effects - Which conditions work for species+zone
2. rig_condition_effects - Which rigs work under specific conditions

Both use logarithmic weight scaling (cap at 4).
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import math

from app.models.schemas import (
    ZoneConditionEffect, RigConditionEffect,
    Catch, EnvironmentSnapshot
)
from app.rules.species_behavior_profiles import get_species_profile

logger = logging.getLogger(__name__)


def classify_tide(tide_stage: str) -> str:
    """Classify tide into band: incoming/outgoing/slack."""
    if not tide_stage:
        return "unknown"
    tide_lower = tide_stage.lower()
    if "incoming" in tide_lower or "rising" in tide_lower:
        return "incoming"
    elif "outgoing" in tide_lower or "falling" in tide_lower:
        return "outgoing"
    elif "slack" in tide_lower or "high" in tide_lower or "low" in tide_lower:
        return "slack"
    return "unknown"


def classify_clarity(clarity: str) -> str:
    """Classify clarity into band: clean/stained/muddy."""
    if not clarity:
        return "clean"  # default
    clarity_lower = clarity.lower()
    if "muddy" in clarity_lower or "dirty" in clarity_lower:
        return "muddy"
    elif "stained" in clarity_lower or "off" in clarity_lower:
        return "stained"
    else:
        return "clean"


def classify_wind(wind_direction: Optional[str], species: str) -> str:
    """
    Classify wind as favorable/neutral/unfavorable for a species.

    Uses species preferences from behavior profiles.
    """
    if not wind_direction or wind_direction is None:
        return "neutral"

    profile = get_species_profile(species)
    if not profile:
        return "neutral"

    wind_prefs = profile.get('wind_preferences', {})
    if not wind_prefs:
        return "neutral"

    favorable = wind_prefs.get('favorable', [])
    unfavorable = wind_prefs.get('unfavorable', [])

    try:
        wind_upper = wind_direction.upper()
    except (AttributeError, TypeError):
        return "neutral"

    # Check favorable
    for fav in favorable:
        if fav.upper() in wind_upper:
            return "favorable"

    # Check unfavorable
    for unfav in unfavorable:
        if unfav.upper() in wind_upper:
            return "unfavorable"

    return "neutral"


def classify_current(current_speed: Optional[float]) -> str:
    """Classify current into band: low/medium/high."""
    if current_speed is None or current_speed <= 0:
        return "low"
    elif current_speed < 0.3:
        return "low"
    elif current_speed < 0.6:
        return "medium"
    else:
        return "high"


def update_zone_condition_effect(
    db: Session,
    species: str,
    zone_id: str,
    conditions: Dict[str, Any],
    weight_multiplier: float = 1.0
) -> Optional[ZoneConditionEffect]:
    """
    Update zone_condition_effect for a successful catch.

    Bands conditions into:
    - tide_band: incoming/outgoing/slack
    - clarity_band: clean/stained/muddy
    - wind_band: favorable/neutral/unfavorable (species-specific)
    - current_band: low/medium/high

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier
        conditions: Dict with tide_stage, clarity, wind_direction, current_speed
        weight_multiplier: Multiplier for success_count increment (default 1.0, use 0.15 for crab traps)

    Returns:
        Updated ZoneConditionEffect instance
    """
    try:
        # Band the conditions
        tide_band = classify_tide(conditions.get('tide_stage'))
        clarity_band = classify_clarity(conditions.get('clarity'))
        wind_band = classify_wind(conditions.get('wind_direction'), species)
        current_band = classify_current(conditions.get('current_speed'))

        # Skip if unknown conditions
        if tide_band == "unknown":
            logger.debug(f"Skipping zone_condition_effect - unknown tide")
            return None

        # Find or create
        zce = db.query(ZoneConditionEffect).filter(
            and_(
                ZoneConditionEffect.species == species,
                ZoneConditionEffect.zone_id == zone_id,
                ZoneConditionEffect.tide_band == tide_band,
                ZoneConditionEffect.clarity_band == clarity_band,
                ZoneConditionEffect.wind_band == wind_band,
                ZoneConditionEffect.current_band == current_band
            )
        ).first()

        if zce:
            # Update existing - apply weight_multiplier for crab traps
            zce.success_count += weight_multiplier
        else:
            # Create new - use weight_multiplier as initial count
            zce = ZoneConditionEffect(
                species=species,
                zone_id=zone_id,
                tide_band=tide_band,
                clarity_band=clarity_band,
                wind_band=wind_band,
                current_band=current_band,
                success_count=weight_multiplier
            )
            db.add(zce)

        # Compute weight using logarithmic scale (caps at 4)
        zce.weight = min(4.0, math.log(zce.success_count + 1))

        db.commit()

        logger.info(
            f"Updated zone_condition_effect: {species} {zone_id} "
            f"{tide_band}/{clarity_band}/{wind_band}/{current_band} "
            f"count={zce.success_count} weight={zce.weight:.2f}"
        )

        return zce

    except Exception as e:
        logger.error(f"Error updating zone_condition_effect: {e}")
        db.rollback()
        raise


def update_rig_condition_effect(
    db: Session,
    species: str,
    rig_type: str,
    conditions: Dict[str, Any],
    weight_multiplier: float = 1.0
) -> Optional[RigConditionEffect]:
    """
    Update rig_condition_effect for a successful catch.

    Tracks which rigs work under specific conditions (regardless of zone).

    Args:
        db: Database session
        species: Species key
        rig_type: Rig type used
        conditions: Dict with tide_stage, clarity
        weight_multiplier: Multiplier for success_count increment (default 1.0, use 0.15 for crab traps)

    Returns:
        Updated RigConditionEffect instance
    """
    if not rig_type or rig_type == 'unknown':
        logger.debug(f"Skipping rig_condition_effect - no rig_type")
        return None

    try:
        # Band the conditions
        tide_band = classify_tide(conditions.get('tide_stage'))
        clarity_band = classify_clarity(conditions.get('clarity'))

        if tide_band == "unknown":
            logger.debug(f"Skipping rig_condition_effect - unknown tide")
            return None

        # Find or create
        rce = db.query(RigConditionEffect).filter(
            and_(
                RigConditionEffect.species == species,
                RigConditionEffect.rig_type == rig_type,
                RigConditionEffect.tide_band == tide_band,
                RigConditionEffect.clarity_band == clarity_band
            )
        ).first()

        if rce:
            # Update existing - apply weight_multiplier for crab traps
            rce.success_count += weight_multiplier
        else:
            # Create new - use weight_multiplier as initial count
            rce = RigConditionEffect(
                species=species,
                rig_type=rig_type,
                tide_band=tide_band,
                clarity_band=clarity_band,
                success_count=weight_multiplier
            )
            db.add(rce)

        # Compute weight using logarithmic scale (caps at 4)
        rce.weight = min(4.0, math.log(rce.success_count + 1))

        db.commit()

        logger.info(
            f"Updated rig_condition_effect: {species} {rig_type} "
            f"{tide_band}/{clarity_band} "
            f"count={rce.success_count} weight={rce.weight:.2f}"
        )

        return rce

    except Exception as e:
        logger.error(f"Error updating rig_condition_effect: {e}")
        db.rollback()
        raise


def get_zone_condition_weight(
    db: Session,
    species: str,
    zone_id: str,
    conditions: Dict[str, Any]
) -> float:
    """
    Get learned weight for current zone conditions.

    Used during score calculation.

    Returns:
        Weight (0-4), or 0 if no data
    """
    tide_band = classify_tide(conditions.get('tide_stage'))
    clarity_band = classify_clarity(conditions.get('clarity'))
    wind_band = classify_wind(conditions.get('wind_direction'), species)
    current_band = classify_current(conditions.get('current_speed'))

    if tide_band == "unknown":
        return 0.0

    zce = db.query(ZoneConditionEffect).filter(
        and_(
            ZoneConditionEffect.species == species,
            ZoneConditionEffect.zone_id == zone_id,
            ZoneConditionEffect.tide_band == tide_band,
            ZoneConditionEffect.clarity_band == clarity_band,
            ZoneConditionEffect.wind_band == wind_band,
            ZoneConditionEffect.current_band == current_band
        )
    ).first()

    return zce.weight if zce else 0.0


def get_rig_condition_weight(
    db: Session,
    species: str,
    rig_type: str,
    conditions: Dict[str, Any]
) -> float:
    """
    Get learned weight for rig under current conditions.

    Used during score calculation.

    Returns:
        Weight (0-4), or 0 if no data
    """
    if not rig_type:
        return 0.0

    tide_band = classify_tide(conditions.get('tide_stage'))
    clarity_band = classify_clarity(conditions.get('clarity'))

    if tide_band == "unknown":
        return 0.0

    rce = db.query(RigConditionEffect).filter(
        and_(
            RigConditionEffect.species == species,
            RigConditionEffect.rig_type == rig_type,
            RigConditionEffect.tide_band == tide_band,
            RigConditionEffect.clarity_band == clarity_band
        )
    ).first()

    return rce.weight if rce else 0.0
