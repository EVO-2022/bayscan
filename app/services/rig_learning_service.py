"""
Rig Learning Service - Tracks which rigs work best per species+zone.

Updates rig_effects table on each catch to learn:
- Which rigs are most effective for each species in each zone
- Weight increases logarithmically with success count (caps at 3)
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import math

from app.models.schemas import RigEffect, Catch

logger = logging.getLogger(__name__)


def update_rig_effect(
    db: Session,
    species: str,
    zone_id: str,
    rig_type: str
) -> Optional[RigEffect]:
    """
    Update rig_effect for a successful catch.

    On each catch:
    1. Find or create rig_effects row
    2. Increment success_count
    3. Recompute weight = min(3, log(success_count + 1))

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier
        rig_type: Rig type used (e.g., 'jig', 'popping_cork')

    Returns:
        Updated RigEffect instance
    """
    if not rig_type or rig_type == 'unknown':
        logger.debug(f"Skipping rig_effect update - no rig_type provided")
        return None

    try:
        # Find or create
        rig_effect = db.query(RigEffect).filter(
            and_(
                RigEffect.species == species,
                RigEffect.zone_id == zone_id,
                RigEffect.rig_type == rig_type
            )
        ).first()

        now = datetime.utcnow()

        if rig_effect:
            # Update existing
            rig_effect.success_count += 1
            rig_effect.last_used = now
        else:
            # Create new
            rig_effect = RigEffect(
                species=species,
                zone_id=zone_id,
                rig_type=rig_type,
                success_count=1,
                last_used=now
            )
            db.add(rig_effect)

        # Compute weight using logarithmic scale (caps at 3)
        # log(1+1) = 0.69, log(2+1) = 1.10, log(5+1) = 1.79, log(10+1) = 2.40, log(20+1) = 3.04
        rig_effect.weight = min(3.0, math.log(rig_effect.success_count + 1))

        db.commit()

        logger.info(
            f"Updated rig_effect: {species} {zone_id} {rig_type} "
            f"count={rig_effect.success_count} weight={rig_effect.weight:.2f}"
        )

        return rig_effect

    except Exception as e:
        logger.error(f"Error updating rig_effect: {e}")
        db.rollback()
        raise


def get_best_rig_for_zone(
    db: Session,
    species: str,
    zone_id: str,
    min_uses: int = 3
) -> Optional[str]:
    """
    Get the most effective rig for a species in a zone.

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier
        min_uses: Minimum success count to consider (default 3)

    Returns:
        Best rig_type string, or None if insufficient data
    """
    best_rig = db.query(RigEffect).filter(
        and_(
            RigEffect.species == species,
            RigEffect.zone_id == zone_id,
            RigEffect.success_count >= min_uses
        )
    ).order_by(RigEffect.weight.desc()).first()

    return best_rig.rig_type if best_rig else None


def get_rig_weight(
    db: Session,
    species: str,
    zone_id: str,
    rig_type: str
) -> float:
    """
    Get learned weight for a specific rig.

    Used during score calculation to boost scores for proven rigs.

    Returns:
        Weight (0-3), or 0 if no data
    """
    rig_effect = db.query(RigEffect).filter(
        and_(
            RigEffect.species == species,
            RigEffect.zone_id == zone_id,
            RigEffect.rig_type == rig_type
        )
    ).first()

    return rig_effect.weight if rig_effect else 0.0


def get_all_rig_effects_for_zone(
    db: Session,
    species: str,
    zone_id: str
) -> list:
    """
    Get all rig effects for a species+zone, ordered by effectiveness.

    Returns:
        List of dicts with rig_type, success_count, weight
    """
    rig_effects = db.query(RigEffect).filter(
        and_(
            RigEffect.species == species,
            RigEffect.zone_id == zone_id
        )
    ).order_by(RigEffect.weight.desc()).all()

    return [
        {
            'rig_type': re.rig_type,
            'success_count': re.success_count,
            'weight': re.weight,
            'last_used': re.last_used
        }
        for re in rig_effects
    ]
