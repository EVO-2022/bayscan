"""
Score Cache Service - Implements bite score caching with smoothing.

This service provides the core recalculateBiteScore() function that:
1. Computes raw scores using the behavior spec
2. Applies exponential smoothing based on data confidence
3. Caches results in bite_scores table
4. Generates reason summaries

All UI/API should read from bite_scores, never compute on the fly.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
import math

from app.models.schemas import (
    BiteScore, BaitScore, Catch, BaitLog, PredatorLog,
    RigEffect, ZoneConditionEffect, RigConditionEffect,
    EnvironmentSnapshot, Zone
)
from app.services.hyperlocal_scoring import calculate_zone_bite_score
from app.services.environment_snapshot import get_latest_snapshot, get_snapshot_as_dict
from app.services.scoring_service import get_current_conditions
from app.rules.uglyfishing_calendar import get_seasonal_baseline_score

logger = logging.getLogger(__name__)


def get_smoothing_weight(total_catches: int) -> float:
    """
    Calculate smoothing weight based on data quantity.

    More data = lower weight = more stable scores (less reactive)
    Less data = higher weight = more reactive scores

    Args:
        total_catches: Total number of catches for this species+zone

    Returns:
        Smoothing weight w (0.1 to 0.5)
    """
    if total_catches < 10:
        # Low data: more reactive (40-50% weight to new score)
        return 0.4 + (total_catches / 100.0)  # 0.4 to 0.5
    elif total_catches < 50:
        # Medium data: moderate smoothing (20-30% weight)
        return 0.2 + ((50 - total_catches) / 400.0)  # 0.2 to 0.3
    else:
        # High data: very stable (10-15% weight)
        return 0.1 + ((100 - min(total_catches, 100)) / 1000.0)  # 0.1 to 0.15


def get_score_rating(score: float) -> str:
    """Convert numeric score to rating label."""
    if score <= 20:
        return "Poor"
    elif score <= 40:
        return "Fair"
    elif score <= 60:
        return "Good"
    elif score <= 80:
        return "Great"
    else:
        return "Excellent"


def get_confidence_level(total_catches: int) -> str:
    """Determine confidence level from catch count."""
    if total_catches < 10:
        return "low"
    elif total_catches < 50:
        return "medium"
    else:
        return "high"


def build_reason_summary(
    conditions: Dict[str, Any],
    seasonal_baseline: float,
    condition_match: float,
    recent_activity: float,
    predator_penalty: float,
    species: str,
    zone_id: str
) -> str:
    """
    Build a concise explanation of the score.

    Focuses on the biggest contributors (positive or negative).
    """
    reasons = []

    # Recent activity
    if recent_activity >= 3:
        reasons.append(f"{int(recent_activity)} recent catches in {zone_id}")

    # Conditions
    tide = conditions.get('tide_stage', 'unknown')
    water_temp = conditions.get('water_temperature')
    clarity = conditions.get('clarity', 'unknown')

    if condition_match >= 5:
        temp_str = f"{int(water_temp)}°F" if water_temp else ""
        reasons.append(f"{tide} tide, {clarity} water {temp_str}".strip())
    elif condition_match <= -5:
        reasons.append(f"unfavorable conditions ({tide} tide)")

    # Predator penalty
    if predator_penalty <= -3:
        reasons.append("recent predator activity")

    # Seasonal baseline context
    if seasonal_baseline >= 70:
        reasons.append("peak season")
    elif seasonal_baseline <= 30:
        reasons.append("off-season")

    if not reasons:
        return f"Seasonal baseline for {species} in {zone_id}"

    return "; ".join(reasons).capitalize()


def recalculate_bite_score(
    db: Session,
    species: str,
    zone_id: str,
    force_recalc: bool = False
) -> Dict[str, Any]:
    """
    Recalculate and cache bite score for a species+zone with smoothing.

    This is the CORE function for score updates. All score changes flow through here.

    Process:
    1. Load context and conditions
    2. Compute raw_score using existing hyperlocal_scoring logic
    3. Load old cached score
    4. Apply smoothing: new_score = old_score * (1-w) + raw_score * w
    5. Update bite_scores table

    Args:
        db: Database session
        species: Species key (e.g., 'speckled_trout')
        zone_id: Zone identifier (e.g., 'Zone 3')
        force_recalc: If True, skip smoothing and use raw score directly

    Returns:
        Dictionary with updated score information
    """
    try:
        # STEP A: Load context
        now = datetime.utcnow()

        # Get latest environment snapshot
        snapshot = get_latest_snapshot(db)
        conditions = get_snapshot_as_dict(snapshot) if snapshot else {}

        # Fallback to basic conditions if no snapshot
        if not conditions:
            current_cond = get_current_conditions(db)
            conditions = {
                'water_temperature': current_cond.get('water_temp_f'),
                'tide_stage': current_cond.get('tide_state'),
                'wind_speed': current_cond.get('wind_speed'),
                'wind_direction': current_cond.get('wind_direction'),
                'time_of_day': current_cond.get('time_of_day'),
                'barometric_pressure': None,
                'clarity': 'clean'  # Default
            }

        # STEP B: Load recent activity for confidence
        total_catches = db.query(func.count(Catch.id)).filter(
            and_(
                Catch.species == species,
                Catch.zone_id == zone_id
            )
        ).scalar() or 0

        # STEP C & D: Compute raw_score using existing hyperlocal_scoring
        raw_result = calculate_zone_bite_score(
            db=db,
            species=species,
            zone_id=zone_id,
            conditions=conditions,
            date=now
        )

        raw_score = raw_result['bite_score']
        seasonal_baseline = raw_result.get('seasonal_baseline', 50)
        condition_match = raw_result.get('condition_match', 0)
        recent_activity = raw_result.get('recent_activity', 0)
        predator_penalty = raw_result.get('predator_penalty', 0)

        # STEP E: Apply smoothing
        old_bite_score = db.query(BiteScore).filter(
            and_(
                BiteScore.species == species,
                BiteScore.zone_id == zone_id
            )
        ).first()

        if old_bite_score and not force_recalc:
            # Exponential smoothing
            old_score = old_bite_score.score
            w = get_smoothing_weight(total_catches)
            new_score = old_score * (1 - w) + raw_score * w
            logger.info(f"Smoothing {species} {zone_id}: {old_score:.1f} -> {new_score:.1f} (w={w:.2f}, raw={raw_score:.1f})")
        else:
            # First calculation or forced recalc - use seasonal baseline as starting point
            new_score = raw_score
            logger.info(f"Initial score {species} {zone_id}: {new_score:.1f} (raw={raw_score:.1f})")

        # Clamp to 0-100
        new_score = max(0.0, min(100.0, new_score))

        # STEP F: Derive rating and confidence
        rating = get_score_rating(new_score)
        confidence = get_confidence_level(total_catches)

        # STEP G: Build reason summary
        reason_summary = build_reason_summary(
            conditions=conditions,
            seasonal_baseline=seasonal_baseline,
            condition_match=condition_match,
            recent_activity=recent_activity,
            predator_penalty=predator_penalty,
            species=species,
            zone_id=zone_id
        )

        # STEP H: Upsert into bite_scores
        if old_bite_score:
            old_bite_score.score = new_score
            old_bite_score.rating = rating
            old_bite_score.confidence = confidence
            old_bite_score.reason_summary = reason_summary
            old_bite_score.last_updated = now
        else:
            new_bite_score = BiteScore(
                species=species,
                zone_id=zone_id,
                score=new_score,
                rating=rating,
                confidence=confidence,
                reason_summary=reason_summary,
                last_updated=now
            )
            db.add(new_bite_score)

        db.commit()

        logger.info(f"Updated bite_score: {species} {zone_id} = {new_score:.1f} ({rating}, {confidence} confidence)")

        return {
            'species': species,
            'zone_id': zone_id,
            'score': round(new_score, 1),
            'rating': rating,
            'confidence': confidence,
            'reason_summary': reason_summary,
            'total_catches': total_catches,
            'raw_score': round(raw_score, 1)
        }

    except Exception as e:
        logger.error(f"Error recalculating bite score for {species} {zone_id}: {e}")
        db.rollback()
        raise


def recalculate_bait_score(
    db: Session,
    bait_species: str,
    zone_id: str
) -> Dict[str, Any]:
    """
    Recalculate and cache bait score for a bait_species+zone.

    Args:
        db: Database session
        bait_species: Bait species (e.g., 'live_shrimp')
        zone_id: Zone identifier

    Returns:
        Dictionary with updated bait score
    """
    try:
        from app.services.bait_scoring import calculate_bait_rating

        now = datetime.utcnow()

        # Get latest conditions
        snapshot = get_latest_snapshot(db)
        conditions = get_snapshot_as_dict(snapshot) if snapshot else {}

        # Calculate raw bait score
        bait_result = calculate_bait_rating(
            db=db,
            bait_species=bait_species,
            zone_id=zone_id,
            conditions=conditions
        )

        score = bait_result.get('rating', 50)
        rating = get_score_rating(score)
        reason = f"Seasonal: {bait_result.get('seasonal_baseline', 0):.0f}, Conditions: {bait_result.get('condition_match', 0):.0f}"

        # Upsert
        old_bait_score = db.query(BaitScore).filter(
            and_(
                BaitScore.bait_species == bait_species,
                BaitScore.zone_id == zone_id
            )
        ).first()

        if old_bait_score:
            old_bait_score.score = score
            old_bait_score.rating = rating
            old_bait_score.reason_summary = reason
            old_bait_score.last_updated = now
        else:
            new_bait_score = BaitScore(
                bait_species=bait_species,
                zone_id=zone_id,
                score=score,
                rating=rating,
                reason_summary=reason,
                last_updated=now
            )
            db.add(new_bait_score)

        db.commit()

        logger.info(f"Updated bait_score: {bait_species} {zone_id} = {score:.1f} ({rating})")

        return {
            'bait_species': bait_species,
            'zone_id': zone_id,
            'score': round(score, 1),
            'rating': rating,
            'reason_summary': reason
        }

    except Exception as e:
        logger.error(f"Error recalculating bait score for {bait_species} {zone_id}: {e}")
        db.rollback()
        raise


def get_cached_bite_score(
    db: Session,
    species: str,
    zone_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get cached bite score for species+zone.

    Returns None if not cached yet.
    """
    bite_score = db.query(BiteScore).filter(
        and_(
            BiteScore.species == species,
            BiteScore.zone_id == zone_id
        )
    ).first()

    if not bite_score:
        return None

    return {
        'species': species,
        'zone_id': zone_id,
        'score': bite_score.score,
        'rating': bite_score.rating,
        'confidence': bite_score.confidence,
        'reason_summary': bite_score.reason_summary,
        'last_updated': bite_score.last_updated
    }


def get_cached_bait_score(
    db: Session,
    bait_species: str,
    zone_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get cached bait score for bait_species+zone.

    Returns None if not cached yet.
    """
    bait_score = db.query(BaitScore).filter(
        and_(
            BaitScore.bait_species == bait_species,
            BaitScore.zone_id == zone_id
        )
    ).first()

    if not bait_score:
        return None

    return {
        'bait_species': bait_species,
        'zone_id': zone_id,
        'score': bait_score.score,
        'rating': bait_score.rating,
        'reason_summary': bait_score.reason_summary,
        'last_updated': bait_score.last_updated
    }
