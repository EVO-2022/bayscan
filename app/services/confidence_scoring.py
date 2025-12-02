"""Confidence scoring for BayScan predictions.

Confidence is based on the amount of historical catch data available
for a specific species in a specific zone.
"""

from sqlalchemy.orm import Session
from app.models.schemas import Catch
from typing import Dict


def calculate_species_zone_confidence(db: Session, species: str, zone_id: str) -> Dict:
    """
    Calculate confidence level for species/zone predictions.

    Confidence levels:
    - LOW: <10 catches
    - MEDIUM: 10-50 catches
    - HIGH: >50 catches

    Args:
        db: Database session
        species: Species key
        zone_id: Zone identifier

    Returns:
        Dictionary with level, sample_count, description
    """
    try:
        # Count catches for this species in this zone
        count = db.query(Catch).filter(
            Catch.species == species,
            Catch.zone_id == zone_id
        ).count()

        if count < 10:
            level = 'LOW'
            description = 'Limited data - predictions based on seasonal baseline and general behavior'
            weight = 0.3  # Lower weight for recent activity in scoring
        elif count < 50:
            level = 'MEDIUM'
            description = 'Moderate data - predictions incorporate recent activity patterns'
            weight = 0.6
        else:
            level = 'HIGH'
            description = 'High confidence - predictions based on solid historical data'
            weight = 1.0

        return {
            'level': level,
            'sample_count': count,
            'description': description,
            'recent_activity_weight': weight,  # Used to scale recent activity modifier
        }

    except Exception as e:
        # Fallback to LOW confidence on error
        return {
            'level': 'LOW',
            'sample_count': 0,
            'description': 'Insufficient data',
            'recent_activity_weight': 0.3,
        }


def get_overall_confidence(db: Session, species: str) -> str:
    """
    Get overall confidence level across all zones for a species.

    Args:
        db: Database session
        species: Species key

    Returns:
        'LOW', 'MEDIUM', or 'HIGH'
    """
    try:
        total_count = db.query(Catch).filter(
            Catch.species == species
        ).count()

        if total_count < 20:
            return 'LOW'
        elif total_count < 100:
            return 'MEDIUM'
        else:
            return 'HIGH'

    except:
        return 'LOW'


def should_reduce_recent_activity_influence(confidence: Dict) -> bool:
    """
    Check if recent activity influence should be reduced due to low confidence.

    Args:
        confidence: Confidence dict from calculate_species_zone_confidence()

    Returns:
        True if recent activity should have reduced influence
    """
    return confidence['level'] == 'LOW'
