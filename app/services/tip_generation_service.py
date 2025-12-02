"""
Tip Generation Service - Auto-generates fishing tips per species+zone.

Generates human-readable tips based on:
- Cached bite scores
- Best rig from rig_effects
- Best bait from recent catches
- Zone metadata (structure, depth)
- Learned condition preferences
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import logging

from app.models.schemas import (
    SpeciesZoneTip, BiteScore, Catch, Zone,
    RigEffect, ZoneConditionEffect
)
from app.services.rig_learning_service import get_best_rig_for_zone
from app.rules.species_tiers import get_species_tier

logger = logging.getLogger(__name__)


# Default rigs by species (fallback if no learned data)
DEFAULT_RIGS = {
    'speckled_trout': 'popping_cork',
    'redfish': 'jig',
    'flounder': 'jig',
    'sheepshead': 'bottom_rig',
    'black_drum': 'bottom_rig',
    'croaker': 'bottom_rig',
    'white_trout': 'jig',
}

# Default bait by species
DEFAULT_BAITS = {
    'speckled_trout': 'live shrimp',
    'redfish': 'live shrimp',
    'flounder': 'mud minnow',
    'sheepshead': 'fiddler crab',
    'black_drum': 'shrimp',
    'croaker': 'shrimp',
    'white_trout': 'shrimp',
}

# Zone structure descriptions
ZONE_DESCRIPTIONS = {
    'Zone 1': 'rubble and north pilings',
    'Zone 2': 'open water',
    'Zone 3': 'north pilings',
    'Zone 4': 'green light line',
    'Zone 5': 'deep north piling line with center pilings',
}


def get_best_bait_for_zone(
    db: Session,
    species: str,
    zone_id: str,
    days_back: int = 30
) -> str:
    """
    Get most commonly used bait for this species+zone in recent catches.

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier
        days_back: How many days to look back

    Returns:
        Best bait string (or default for species)
    """
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    # Find most common bait
    result = db.query(
        Catch.bait_used,
        func.count(Catch.id).label('count')
    ).filter(
        and_(
            Catch.species == species,
            Catch.zone_id == zone_id,
            Catch.timestamp >= cutoff,
            Catch.bait_used.isnot(None)
        )
    ).group_by(Catch.bait_used).order_by(desc('count')).first()

    if result and result[0]:
        return result[0]

    # Fallback to default
    return DEFAULT_BAITS.get(species, 'live shrimp')


def get_best_tide_for_zone(
    db: Session,
    species: str,
    zone_id: str
) -> str:
    """
    Get best tide recommendation from zone_condition_effects.

    Returns:
        Tide recommendation string like "on incoming tide" or "on any moving tide"
    """
    # Get all tide bands for this species+zone
    tide_weights = db.query(
        ZoneConditionEffect.tide_band,
        func.avg(ZoneConditionEffect.weight).label('avg_weight'),
        func.sum(ZoneConditionEffect.success_count).label('total_count')
    ).filter(
        and_(
            ZoneConditionEffect.species == species,
            ZoneConditionEffect.zone_id == zone_id
        )
    ).group_by(ZoneConditionEffect.tide_band).all()

    if not tide_weights:
        return "on moving tide"

    # Convert to dict
    tide_dict = {row[0]: (row[1], row[2]) for row in tide_weights}

    incoming_weight = tide_dict.get('incoming', (0, 0))[0]
    outgoing_weight = tide_dict.get('outgoing', (0, 0))[0]
    slack_weight = tide_dict.get('slack', (0, 0))[0]

    # Determine recommendation
    if incoming_weight > outgoing_weight + 0.5 and incoming_weight > slack_weight:
        return "on incoming tide"
    elif outgoing_weight > incoming_weight + 0.5 and outgoing_weight > slack_weight:
        return "on outgoing tide"
    elif incoming_weight > slack_weight and outgoing_weight > slack_weight:
        return "on any moving tide"
    else:
        return "on moving tide"


def generate_tip(
    db: Session,
    species: str,
    zone_id: str
) -> Optional[str]:
    """
    Generate a fishing tip for species+zone.

    Format:
    "[Zone X] is your best bet. Fish a [rig] with [bait] [structure/depth context] [tide]."

    Examples:
    - "Zone 3 is your best bet. Fish a popping cork with live shrimp along the north pilings on incoming tide."
    - "Try the rubble in Zone 1 on the bottom with a jig and shrimp on any moving tide."

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier

    Returns:
        Tip string, or None if score too low
    """
    # Check bite score viability
    bite_score = db.query(BiteScore).filter(
        and_(
            BiteScore.species == species,
            BiteScore.zone_id == zone_id
        )
    ).first()

    if not bite_score or bite_score.score < 50:
        # Don't generate tips for poor scores
        return None

    # Get best rig
    rig = get_best_rig_for_zone(db, species, zone_id, min_uses=2)
    if not rig:
        rig = DEFAULT_RIGS.get(species, 'jig')

    # Get best bait
    bait = get_best_bait_for_zone(db, species, zone_id)

    # Get zone structure description
    structure = ZONE_DESCRIPTIONS.get(zone_id, zone_id)

    # Get tide recommendation
    tide = get_best_tide_for_zone(db, species, zone_id)

    # Build tip
    # Determine if it's the best zone or just a good zone
    if bite_score.score >= 70:
        intro = f"{zone_id} is your best bet."
    else:
        intro = f"Try {zone_id}."

    # Format rig name nicely
    rig_display = rig.replace('_', ' ')

    # Build the full tip
    if zone_id == 'Zone 1':
        # Special case for rubble zone
        tip = f"{intro} Fish a {rig_display} with {bait} around the {structure} {tide}."
    elif zone_id == 'Zone 5':
        # Special case for deep zone
        tip = f"{intro} Work a {rig_display} with {bait} along the {structure} {tide}."
    else:
        tip = f"{intro} Fish a {rig_display} with {bait} {tide}."

    return tip


def update_species_zone_tip(
    db: Session,
    species: str,
    zone_id: str
) -> Optional[SpeciesZoneTip]:
    """
    Generate and save/update tip for species+zone.

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier

    Returns:
        Updated SpeciesZoneTip instance, or None if no tip generated
    """
    try:
        tip_text = generate_tip(db, species, zone_id)

        if not tip_text:
            # No tip - delete if exists
            existing = db.query(SpeciesZoneTip).filter(
                and_(
                    SpeciesZoneTip.species == species,
                    SpeciesZoneTip.zone_id == zone_id
                )
            ).first()
            if existing:
                db.delete(existing)
                db.commit()
                logger.info(f"Deleted tip for {species} {zone_id} (score too low)")
            return None

        # Upsert tip
        now = datetime.utcnow()
        tip = db.query(SpeciesZoneTip).filter(
            and_(
                SpeciesZoneTip.species == species,
                SpeciesZoneTip.zone_id == zone_id
            )
        ).first()

        if tip:
            tip.tip_text = tip_text
            tip.last_updated = now
        else:
            tip = SpeciesZoneTip(
                species=species,
                zone_id=zone_id,
                tip_text=tip_text,
                last_updated=now
            )
            db.add(tip)

        db.commit()

        logger.info(f"Updated tip for {species} {zone_id}: {tip_text}")

        return tip

    except Exception as e:
        logger.error(f"Error updating tip for {species} {zone_id}: {e}")
        db.rollback()
        raise


def get_tip_for_zone(
    db: Session,
    species: str,
    zone_id: str
) -> Optional[str]:
    """
    Get cached tip for species+zone.

    Returns:
        Tip text string, or None
    """
    tip = db.query(SpeciesZoneTip).filter(
        and_(
            SpeciesZoneTip.species == species,
            SpeciesZoneTip.zone_id == zone_id
        )
    ).first()

    return tip.tip_text if tip else None


def regenerate_all_tips(db: Session, species: str = None):
    """
    Regenerate tips for all species+zone combinations (or just one species).

    Args:
        db: Database session
        species: Optional species to limit to
    """
    zones = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5']

    if species:
        species_list = [species]
    else:
        # Get all Tier 1 species
        from app.rules.species_tiers import TIER_1_FULL_ANALYTICS
        species_list = TIER_1_FULL_ANALYTICS

    count = 0
    for sp in species_list:
        for zone in zones:
            result = update_species_zone_tip(db, sp, zone)
            if result:
                count += 1

    logger.info(f"Regenerated {count} tips")
    return count
