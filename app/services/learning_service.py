"""
Learning Layer Service

Implements adaptive learning based on user catch logs.
Adjusts species bite scores based on actual fishing results.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Optional
import logging

from app.models.schemas import LearningBucket, Catch

logger = logging.getLogger(__name__)

# Learning parameters
DELTA_MIN = -0.3
DELTA_MAX = 0.3
MICRO_ADJUSTMENT = 0.02
DAILY_DECAY_FACTOR = 0.98
MIN_SAMPLES_FOR_CONFIDENCE = 5


def get_time_of_day_block(dt: datetime) -> str:
    """
    Get time of day block for a datetime.

    Args:
        dt: Datetime to classify

    Returns:
        'morning', 'midday', or 'evening'
    """
    hour = dt.hour
    if 6 <= hour < 11:
        return 'morning'
    elif 11 <= hour < 15:
        return 'midday'
    elif 15 <= hour < 20:
        return 'evening'
    else:
        return 'night'  # Outside main blocks


def get_bucket_key(species: str, zone: str, tide_stage: str, time_block: str) -> Dict[str, str]:
    """
    Create a bucket identifier.

    Args:
        species: Species key (e.g., 'redfish')
        zone: Zone (e.g., 'Zone 3')
        tide_stage: Tide stage ('low', 'rising', 'high', 'falling')
        time_block: Time block ('morning', 'midday', 'evening')

    Returns:
        Dictionary with bucket keys
    """
    return {
        'species': species,
        'zone': zone,
        'tide_stage': tide_stage,
        'time_of_day_block': time_block
    }


def get_or_create_bucket(db: Session, species: str, zone: str, tide_stage: str, time_block: str) -> LearningBucket:
    """
    Get existing learning bucket or create new one.

    Args:
        db: Database session
        species: Species key
        zone: Zone identifier
        tide_stage: Tide stage
        time_block: Time of day block

    Returns:
        LearningBucket instance
    """
    bucket = db.query(LearningBucket).filter(
        and_(
            LearningBucket.species == species,
            LearningBucket.zone == zone,
            LearningBucket.tide_stage == tide_stage,
            LearningBucket.time_of_day_block == time_block
        )
    ).first()

    if not bucket:
        bucket = LearningBucket(
            species=species,
            zone=zone,
            tide_stage=tide_stage,
            time_of_day_block=time_block,
            delta=0.0,
            confidence=0.5,
            sample_count=0
        )
        db.add(bucket)
        db.commit()
        db.refresh(bucket)

    return bucket


def adjust_bucket_after_session(
    db: Session,
    species: str,
    zone: str,
    tide_stage: str,
    time_block: str,
    predicted_rating: str,
    caught_count: int
) -> None:
    """
    Micro-adjust a bucket's delta based on fishing session result.

    Rules:
    - If model predicted GOOD or higher and caught 0 fish → delta -= 0.02
    - If model predicted FAIR or lower and caught ≥1 fish → delta += 0.02

    Args:
        db: Database session
        species: Species key
        zone: Zone identifier
        tide_stage: Tide stage
        time_block: Time of day block
        predicted_rating: Model's prediction ('UNLIKELY', 'SLOW', 'DECENT', 'HOT')
        caught_count: Number of fish caught in session
    """
    bucket = get_or_create_bucket(db, species, zone, tide_stage, time_block)

    # Determine if adjustment needed
    should_decrease = predicted_rating in ['HOT', 'DECENT'] and caught_count == 0
    should_increase = predicted_rating in ['SLOW', 'UNLIKELY'] and caught_count >= 1

    if should_decrease:
        bucket.delta = max(DELTA_MIN, bucket.delta - MICRO_ADJUSTMENT)
        logger.info(f"Decreased delta for {species} in {zone} (predicted {predicted_rating}, caught 0): delta={bucket.delta:.3f}")

    elif should_increase:
        bucket.delta = min(DELTA_MAX, bucket.delta + MICRO_ADJUSTMENT)
        logger.info(f"Increased delta for {species} in {zone} (predicted {predicted_rating}, caught {caught_count}): delta={bucket.delta:.3f}")

    # Update metadata
    bucket.sample_count += 1
    bucket.last_adjustment = datetime.utcnow()

    # Update confidence based on sample count
    if bucket.sample_count < MIN_SAMPLES_FOR_CONFIDENCE:
        bucket.confidence = 0.3 + (bucket.sample_count / MIN_SAMPLES_FOR_CONFIDENCE) * 0.4
    else:
        bucket.confidence = min(0.9, 0.7 + (bucket.sample_count / 20) * 0.2)

    db.commit()


def apply_daily_decay(db: Session) -> None:
    """
    Apply daily decay to all learning buckets.

    Called at midnight local time.
    Formula: delta = delta * 0.98
    """
    try:
        buckets = db.query(LearningBucket).all()

        for bucket in buckets:
            bucket.delta = bucket.delta * DAILY_DECAY_FACTOR

            # If delta gets very close to 0, reset to 0
            if abs(bucket.delta) < 0.01:
                bucket.delta = 0.0

        db.commit()
        logger.info(f"Applied daily decay to {len(buckets)} learning buckets")

    except Exception as e:
        logger.error(f"Error applying daily decay: {e}")
        db.rollback()


def get_learning_delta(
    db: Session,
    species: str,
    zone: str,
    tide_stage: str,
    time_block: str
) -> Dict:
    """
    Get learning delta and metadata for a specific bucket.

    Args:
        db: Database session
        species: Species key
        zone: Zone identifier
        tide_stage: Tide stage
        time_block: Time of day block

    Returns:
        Dictionary with delta, confidence, sample_count, and explanation
    """
    bucket = db.query(LearningBucket).filter(
        and_(
            LearningBucket.species == species,
            LearningBucket.zone == zone,
            LearningBucket.tide_stage == tide_stage,
            LearningBucket.time_of_day_block == time_block
        )
    ).first()

    if not bucket:
        return {
            'delta': 0.0,
            'confidence': 0.5,
            'sample_count': 0,
            'explanation': 'No historical data for this condition combination yet.'
        }

    # Generate explanation
    direction = "improved" if bucket.delta > 0 else "reduced" if bucket.delta < 0 else "neutral"
    explanation = f"Based on {bucket.sample_count} fishing sessions, this condition has {direction} bite rates by {abs(bucket.delta):.2f}."

    return {
        'delta': bucket.delta,
        'confidence': bucket.confidence,
        'sample_count': bucket.sample_count,
        'explanation': explanation,
        'last_updated': bucket.last_adjustment.isoformat() if bucket.last_adjustment else None
    }


def process_catch_for_learning(db: Session, catch: Catch, predicted_tier: str) -> None:
    """
    Process a newly logged catch for learning adjustments.

    Args:
        db: Database session
        catch: Catch record
        predicted_tier: What the model predicted (HOT/DECENT/SLOW/UNLIKELY)
    """
    try:
        # Extract bucket parameters from catch
        time_block = get_time_of_day_block(catch.timestamp)

        # Need tide stage - get from catch snapshot or current
        tide_stage = catch.tide_state or 'unknown'
        if tide_stage == 'slack':
            tide_stage = 'low'  # Map slack to low

        # Only process if we have valid zone info
        if not catch.dock_side:
            logger.warning(f"Catch {catch.id} has no zone info, skipping learning")
            return

        # Adjust bucket
        adjust_bucket_after_session(
            db=db,
            species=catch.species,
            zone=catch.dock_side,
            tide_stage=tide_stage,
            time_block=time_block,
            predicted_rating=predicted_tier,
            caught_count=catch.quantity or 1
        )

    except Exception as e:
        logger.error(f"Error processing catch for learning: {e}")


def get_zone_data_sufficiency(db: Session, zone: str) -> Dict:
    """
    Check if a zone has sufficient data for reliable predictions.

    Args:
        db: Database session
        zone: Zone identifier

    Returns:
        Dictionary with data sufficiency info
    """
    # Count total catches in this zone
    catch_count = db.query(Catch).filter(Catch.dock_side == zone).count()

    # Count learning buckets for this zone
    bucket_count = db.query(LearningBucket).filter(LearningBucket.zone == zone).count()

    is_sufficient = catch_count >= 5
    status = 'SUFFICIENT' if is_sufficient else 'UNKNOWN'

    return {
        'zone': zone,
        'status': status,
        'catch_count': catch_count,
        'bucket_count': bucket_count,
        'message': f"Zone has {catch_count} logged catches" if is_sufficient else "Insufficient data - using nearby zone averages"
    }


def get_unfished_zone_delta(db: Session, zone: str, species: str, tide_stage: str, time_block: str) -> float:
    """
    For unfished zones, calculate delta based on nearby zones.

    Args:
        db: Database session
        zone: Zone identifier (e.g., 'Zone 5')
        species: Species key
        tide_stage: Tide stage
        time_block: Time of day block

    Returns:
        Average delta from nearby zones
    """
    # Define nearby zones for each zone
    nearby_zones = {
        'Zone 1': ['Zone 2'],
        'Zone 2': ['Zone 1', 'Zone 3'],
        'Zone 3': ['Zone 2', 'Zone 4'],
        'Zone 4': ['Zone 3', 'Zone 5'],
        'Zone 5': ['Zone 2', 'Zone 3', 'Zone 4']  # Average of mid zones
    }

    zones_to_check = nearby_zones.get(zone, ['Zone 2', 'Zone 3', 'Zone 4'])

    # Query buckets from nearby zones
    buckets = db.query(LearningBucket).filter(
        and_(
            LearningBucket.species == species,
            LearningBucket.zone.in_(zones_to_check),
            LearningBucket.tide_stage == tide_stage,
            LearningBucket.time_of_day_block == time_block
        )
    ).all()

    if not buckets:
        return 0.0

    # Return average delta
    avg_delta = sum(b.delta for b in buckets) / len(buckets)
    return avg_delta
