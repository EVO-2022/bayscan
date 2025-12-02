#!/usr/bin/env python3
"""
Initialization script for the BayScan cache system.

This script:
1. Creates all new database tables
2. Populates static tables (zones, species)
3. Generates initial cache for all species+zone combinations
4. Backfills rig_effects and condition_effects from existing catch logs

Run this ONCE after deploying the cache system code.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.database import SessionLocal, engine, Base
from app.models.schemas import (
    Zone, Species, BiteScore, BaitScore,
    RigEffect, ZoneConditionEffect, RigConditionEffect,
    SpeciesZoneTip, Catch
)
from app.services.score_cache_service import recalculate_bite_score, recalculate_bait_score
from app.services.rig_learning_service import update_rig_effect
from app.services.condition_learning_service import (
    update_zone_condition_effect,
    update_rig_condition_effect
)
from app.services.tip_generation_service import update_species_zone_tip
from app.rules.species_tiers import TIER_1_SPECIES, TIER_2_SPECIES


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")


def populate_zones(db):
    """Populate zones table with static zone metadata."""
    print("\nPopulating zones table...")

    zones_data = [
        {
            'id': 'Zone 1',
            'name': 'Northwest Zone',
            'depth_band': 'shallow',
            'has_pilings': True,
            'has_center_pilings': False,
            'has_rubble': True,
            'has_light': False,
            'description': '2-4 ft depth, north pilings and rubble structure'
        },
        {
            'id': 'Zone 2',
            'name': 'Southwest Zone',
            'depth_band': 'shallow',
            'has_pilings': False,
            'has_center_pilings': False,
            'has_rubble': False,
            'has_light': False,
            'description': '2-4 ft depth, open water'
        },
        {
            'id': 'Zone 3',
            'name': 'Northeast Zone',
            'depth_band': 'medium',
            'has_pilings': True,
            'has_center_pilings': False,
            'has_rubble': False,
            'has_light': False,
            'description': '3-6 ft depth, north pilings, most fished'
        },
        {
            'id': 'Zone 4',
            'name': 'Southeast Zone',
            'depth_band': 'medium',
            'has_pilings': False,
            'has_center_pilings': False,
            'has_rubble': False,
            'has_light': True,
            'description': '3-6 ft depth, green light, most fished'
        },
        {
            'id': 'Zone 5',
            'name': 'East Zone',
            'depth_band': 'deep',
            'has_pilings': True,
            'has_center_pilings': True,
            'has_rubble': False,
            'has_light': False,
            'description': '5-7 ft depth, dual north and center pilings, strongest structure'
        }
    ]

    for zone_data in zones_data:
        existing = db.query(Zone).filter(Zone.id == zone_data['id']).first()
        if not existing:
            zone = Zone(**zone_data)
            db.add(zone)
            print(f"  Added {zone_data['id']}")
        else:
            print(f"  {zone_data['id']} already exists")

    db.commit()
    print("✓ Zones populated")


def populate_species(db):
    """Populate species table with species metadata."""
    print("\nPopulating species table...")

    species_data = [
        # Tier 1 - Full Analytics
        {'id': 'speckled_trout', 'name': 'Speckled Trout', 'tier': 1, 'category': 'tier1_full'},
        {'id': 'redfish', 'name': 'Redfish', 'tier': 1, 'category': 'tier1_full'},
        {'id': 'flounder', 'name': 'Flounder', 'tier': 1, 'category': 'tier1_full'},
        {'id': 'sheepshead', 'name': 'Sheepshead', 'tier': 1, 'category': 'tier1_full'},
        {'id': 'black_drum', 'name': 'Black Drum', 'tier': 1, 'category': 'tier1_full'},

        # Tier 2 - Simplified
        {'id': 'croaker', 'name': 'Croaker', 'tier': 2, 'category': 'tier2_simplified'},
        {'id': 'white_trout', 'name': 'White Trout', 'tier': 2, 'category': 'tier2_simplified'},
        {'id': 'menhaden', 'name': 'Menhaden', 'tier': 2, 'category': 'tier2_simplified'},
        {'id': 'mullet', 'name': 'Mullet', 'tier': 2, 'category': 'tier2_simplified'},
        {'id': 'jack_crevalle', 'name': 'Jack Crevalle', 'tier': 2, 'category': 'tier2_simplified'},

        # Bait species
        {'id': 'live_shrimp', 'name': 'Live Shrimp', 'tier': 0, 'category': 'bait'},
        {'id': 'fiddler_crab', 'name': 'Fiddler Crab', 'tier': 0, 'category': 'bait'},
    ]

    for sp_data in species_data:
        existing = db.query(Species).filter(Species.id == sp_data['id']).first()
        if not existing:
            species = Species(**sp_data)
            db.add(species)
            print(f"  Added {sp_data['name']}")
        else:
            print(f"  {sp_data['name']} already exists")

    db.commit()
    print("✓ Species populated")


def backfill_learning_from_catches(db):
    """
    Backfill rig_effects and condition_effects from existing catch logs.

    This processes all historical catches to populate the learning tables.
    Only processes catches that have zone_id (new schema).
    """
    print("\nBackfilling learning data from catch logs...")

    try:
        # Try to get catches with zone_id (new schema)
        catches = db.query(Catch).filter(
            Catch.zone_id.isnot(None)
        ).order_by(Catch.timestamp).all()
    except Exception as e:
        # If zone_id column doesn't exist yet, skip backfilling
        print(f"  Skipping backfill - database schema needs migration first")
        print(f"  Error: {e}")
        return

    if not catches:
        print("  No catches with zone_id found - skipping backfill")
        print("  (Catches will be logged with new schema going forward)")
        return

    print(f"  Processing {len(catches)} catch records with zone_id...")

    for i, catch in enumerate(catches):
        try:
            # Use rig_type if available, otherwise fall back to presentation
            rig_type = catch.rig_type or getattr(catch, 'presentation', None)

            # Update rig effect
            if rig_type:
                update_rig_effect(db, catch.species, catch.zone_id, rig_type)

            # Update condition effects
            conditions = {
                'tide_stage': getattr(catch, 'tide_stage', None),
                'clarity': 'clean',  # Default if not available
                'wind_direction': getattr(catch, 'wind_direction', None),
                'current_speed': getattr(catch, 'current_speed', None)
            }

            update_zone_condition_effect(db, catch.species, catch.zone_id, conditions)

            if rig_type:
                update_rig_condition_effect(db, catch.species, rig_type, conditions)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(catches)} catches...")

        except Exception as e:
            print(f"  Error processing catch {catch.id}: {e}")
            continue

    db.commit()
    print(f"✓ Backfilled learning data from {len(catches)} catches")


def generate_initial_cache(db):
    """
    Generate initial cache for all species+zone combinations.

    Calculates bite scores and bait scores for all relevant combinations.
    """
    print("\nGenerating initial cache...")

    zones = ['Zone 1', 'Zone 2', 'Zone 3', 'Zone 4', 'Zone 5']

    # Tier 1 species
    print("  Calculating Tier 1 species scores...")
    for species in TIER_1_SPECIES:
        for zone in zones:
            try:
                recalculate_bite_score(db, species, zone, force_recalc=True)
                update_species_zone_tip(db, species, zone)
                print(f"    ✓ {species} - {zone}")
            except Exception as e:
                print(f"    ✗ Error: {species} - {zone}: {e}")

    # Tier 2 species
    print("  Calculating Tier 2 species scores...")
    for species in TIER_2_SPECIES:
        for zone in zones:
            try:
                recalculate_bite_score(db, species, zone, force_recalc=True)
                print(f"    ✓ {species} - {zone}")
            except Exception as e:
                print(f"    ✗ Error: {species} - {zone}: {e}")

    # Bait species
    print("  Calculating bait scores...")
    bait_species = ['live_shrimp', 'menhaden', 'mullet', 'fiddler_crab']
    for bait in bait_species:
        for zone in zones:
            try:
                recalculate_bait_score(db, bait, zone)
                print(f"    ✓ {bait} - {zone}")
            except Exception as e:
                print(f"    ✗ Error: {bait} - {zone}: {e}")

    db.commit()
    print("✓ Initial cache generated")


def print_stats(db):
    """Print statistics about the initialized system."""
    print("\n" + "="*60)
    print("INITIALIZATION COMPLETE")
    print("="*60)

    bite_score_count = db.query(BiteScore).count()
    bait_score_count = db.query(BaitScore).count()
    rig_effect_count = db.query(RigEffect).count()
    zone_condition_count = db.query(ZoneConditionEffect).count()
    rig_condition_count = db.query(RigConditionEffect).count()
    tip_count = db.query(SpeciesZoneTip).count()

    print(f"\nDatabase Statistics:")
    print(f"  Bite Scores:           {bite_score_count}")
    print(f"  Bait Scores:           {bait_score_count}")
    print(f"  Rig Effects:           {rig_effect_count}")
    print(f"  Zone Cond Effects:     {zone_condition_count}")
    print(f"  Rig Cond Effects:      {rig_condition_count}")
    print(f"  Tips:                  {tip_count}")

    print(f"\nSystem is ready!")
    print(f"  - Scores are cached and will update automatically on new catches")
    print(f"  - Periodic recalculation runs every 30 minutes")
    print(f"  - Learning system is tracking rig and condition effectiveness")
    print("="*60 + "\n")


def main():
    """Run the full initialization."""
    print("\n" + "="*60)
    print("BAYSCAN CACHE SYSTEM INITIALIZATION")
    print("="*60)

    db = SessionLocal()

    try:
        # Step 1: Create tables
        create_tables()

        # Step 2: Populate static data
        populate_zones(db)
        populate_species(db)

        # Step 3: Backfill learning from existing catches
        backfill_learning_from_catches(db)

        # Step 4: Generate initial cache
        generate_initial_cache(db)

        # Step 5: Print stats
        print_stats(db)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1

    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
