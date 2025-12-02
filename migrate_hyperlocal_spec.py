#!/usr/bin/env python3
"""
Database migration script for Hyperlocal Spec Implementation.

This script:
1. Creates new tables (environment_snapshots)
2. Adds new columns to existing tables (catches, bait_logs)
3. Migrates existing data where possible
4. Sets defaults for required fields

IMPORTANT: Back up your database before running!
cp app/bayscan.db app/bayscan.db.backup.$(date +%Y%m%d_%H%M%S)
"""
import sys
from pathlib import Path

# Add app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, engine
from app.models.schemas import Catch, BaitLog, EnvironmentSnapshot
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_column_exists(engine, table_name, column_name):
    """Check if a column exists in a table."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_database():
    """Run the full migration."""
    logger.info("Starting hyperlocal spec migration...")

    try:
        # Step 1: Create new tables (environment_snapshots)
        logger.info("Creating new tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ environment_snapshots table created")

        # Step 2: Add new columns to catches table
        logger.info("Adding new columns to catches table...")

        with engine.connect() as conn:
            # Check what columns already exist
            existing_columns = []
            if check_column_exists(engine, 'catches', 'zone_id'):
                existing_columns.append('zone_id')
            if check_column_exists(engine, 'catches', 'bait_used'):
                existing_columns.append('bait_used')

            # Add new columns to catches if they don't exist
            if 'zone_id' not in existing_columns:
                logger.info("Adding zone_id to catches...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN zone_id VARCHAR(20) DEFAULT 'Zone 3'
                """))
                conn.commit()

            if 'distance_from_dock' not in check_column_exists(engine, 'catches', 'distance_from_dock'):
                logger.info("Adding distance_from_dock to catches...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN distance_from_dock VARCHAR(20)
                """))
                conn.commit()

            if not check_column_exists(engine, 'catches', 'depth_estimate'):
                logger.info("Adding depth_estimate to catches...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN depth_estimate VARCHAR(20)
                """))
                conn.commit()

            if not check_column_exists(engine, 'catches', 'structure_type'):
                logger.info("Adding structure_type to catches...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN structure_type VARCHAR(50)
                """))
                conn.commit()

            if not check_column_exists(engine, 'catches', 'predator_seen_recently'):
                logger.info("Adding predator_seen_recently to catches...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN predator_seen_recently BOOLEAN DEFAULT 0
                """))
                conn.commit()

            # Rename columns (SQLite doesn't support RENAME COLUMN directly in older versions)
            # We'll need to check if old columns exist and add new ones
            if check_column_exists(engine, 'catches', 'bait_type') and not check_column_exists(engine, 'catches', 'bait_used'):
                logger.info("Adding bait_used column (migrating from bait_type)...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN bait_used VARCHAR(100)
                """))
                conn.commit()
                # Copy data from old column
                conn.execute(text("""
                    UPDATE catches SET bait_used = bait_type WHERE bait_type IS NOT NULL
                """))
                conn.commit()

            if check_column_exists(engine, 'catches', 'method') and not check_column_exists(engine, 'catches', 'presentation'):
                logger.info("Adding presentation column (migrating from method)...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN presentation VARCHAR(100)
                """))
                conn.commit()
                # Copy data from old column
                conn.execute(text("""
                    UPDATE catches SET presentation = method WHERE method IS NOT NULL
                """))
                conn.commit()

            # Add expanded environment fields if they don't exist
            new_env_fields = [
                ('humidity', 'FLOAT'),
                ('current_speed', 'FLOAT'),
                ('current_direction', 'VARCHAR(10)'),
                ('weather', 'VARCHAR(50)'),
                ('time_of_day', 'VARCHAR(20)'),
                ('moon_phase', 'FLOAT'),
                ('dock_lights_on', 'BOOLEAN DEFAULT 0'),
            ]

            for field_name, field_type in new_env_fields:
                if not check_column_exists(engine, 'catches', field_name):
                    logger.info(f"Adding {field_name} to catches...")
                    conn.execute(text(f"""
                        ALTER TABLE catches ADD COLUMN {field_name} {field_type}
                    """))
                    conn.commit()

            # Rename temperature columns for clarity
            if check_column_exists(engine, 'catches', 'temperature') and not check_column_exists(engine, 'catches', 'air_temp'):
                logger.info("Adding air_temp column (migrating from temperature)...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN air_temp FLOAT
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE catches SET air_temp = temperature WHERE temperature IS NOT NULL
                """))
                conn.commit()

            if check_column_exists(engine, 'catches', 'water_temperature') and not check_column_exists(engine, 'catches', 'water_temp'):
                logger.info("Adding water_temp column (migrating from water_temperature)...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN water_temp FLOAT
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE catches SET water_temp = water_temperature WHERE water_temperature IS NOT NULL
                """))
                conn.commit()

            if check_column_exists(engine, 'catches', 'pressure_trend') and not check_column_exists(engine, 'catches', 'barometric_pressure'):
                logger.info("Adding barometric_pressure to catches...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN barometric_pressure FLOAT
                """))
                conn.commit()

            if check_column_exists(engine, 'catches', 'tide_state') and not check_column_exists(engine, 'catches', 'tide_stage'):
                logger.info("Adding tide_stage column (migrating from tide_state)...")
                conn.execute(text("""
                    ALTER TABLE catches ADD COLUMN tide_stage VARCHAR(20)
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE catches SET tide_stage = tide_state WHERE tide_state IS NOT NULL
                """))
                conn.commit()

        logger.info("✓ catches table migration complete")

        # Step 3: Update bait_logs table
        logger.info("Updating bait_logs table...")

        with engine.connect() as conn:
            # Rename time to timestamp if needed
            if check_column_exists(engine, 'bait_logs', 'time') and not check_column_exists(engine, 'bait_logs', 'timestamp'):
                logger.info("Adding timestamp column (migrating from time)...")
                conn.execute(text("""
                    ALTER TABLE bait_logs ADD COLUMN timestamp DATETIME
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE bait_logs SET timestamp = time WHERE time IS NOT NULL
                """))
                conn.commit()

            # Rename zone to zone_id if needed
            if check_column_exists(engine, 'bait_logs', 'zone') and not check_column_exists(engine, 'bait_logs', 'zone_id'):
                logger.info("Adding zone_id column (migrating from zone)...")
                conn.execute(text("""
                    ALTER TABLE bait_logs ADD COLUMN zone_id VARCHAR(20)
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE bait_logs SET zone_id = zone WHERE zone IS NOT NULL
                """))
                conn.commit()

            # Rename quantity to quantity_estimate if needed
            if check_column_exists(engine, 'bait_logs', 'quantity') and not check_column_exists(engine, 'bait_logs', 'quantity_estimate'):
                logger.info("Adding quantity_estimate column...")
                conn.execute(text("""
                    ALTER TABLE bait_logs ADD COLUMN quantity_estimate VARCHAR(20)
                """))
                conn.commit()
                # Convert numbers to estimates
                conn.execute(text("""
                    UPDATE bait_logs SET quantity_estimate =
                        CASE
                            WHEN quantity = 0 THEN 'none'
                            WHEN quantity < 10 THEN 'few'
                            ELSE 'plenty'
                        END
                    WHERE quantity IS NOT NULL
                """))
                conn.commit()

            # Add structure_type if missing
            if not check_column_exists(engine, 'bait_logs', 'structure_type'):
                logger.info("Adding structure_type to bait_logs...")
                conn.execute(text("""
                    ALTER TABLE bait_logs ADD COLUMN structure_type VARCHAR(50)
                """))
                conn.commit()

            # Rename how_caught to method if needed
            if check_column_exists(engine, 'bait_logs', 'how_caught') and not check_column_exists(engine, 'bait_logs', 'method'):
                logger.info("Adding method column (migrating from how_caught)...")
                conn.execute(text("""
                    ALTER TABLE bait_logs ADD COLUMN method VARCHAR(50)
                """))
                conn.commit()
                conn.execute(text("""
                    UPDATE bait_logs SET method = how_caught WHERE how_caught IS NOT NULL
                """))
                conn.commit()

            # Add all environment snapshot fields to bait_logs
            bait_env_fields = [
                ('water_temp', 'FLOAT'),
                ('air_temp', 'FLOAT'),
                ('humidity', 'FLOAT'),
                ('barometric_pressure', 'FLOAT'),
                ('tide_height', 'FLOAT'),
                ('tide_stage', 'VARCHAR(20)'),
                ('current_speed', 'FLOAT'),
                ('current_direction', 'VARCHAR(10)'),
                ('wind_speed', 'FLOAT'),
                ('wind_direction', 'VARCHAR(10)'),
                ('weather', 'VARCHAR(50)'),
                ('time_of_day', 'VARCHAR(20)'),
                ('moon_phase', 'FLOAT'),
                ('dock_lights_on', 'BOOLEAN DEFAULT 0'),
            ]

            for field_name, field_type in bait_env_fields:
                if not check_column_exists(engine, 'bait_logs', field_name):
                    logger.info(f"Adding {field_name} to bait_logs...")
                    conn.execute(text(f"""
                        ALTER TABLE bait_logs ADD COLUMN {field_name} {field_type}
                    """))
                    conn.commit()

        logger.info("✓ bait_logs table migration complete")

        # Step 4: Set default zone for old catches if needed
        logger.info("Setting default zones for old catches...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE catches
                SET zone_id = 'Zone 3'
                WHERE zone_id IS NULL OR zone_id = ''
            """))
            conn.commit()
            logger.info(f"✓ Set default zone for {result.rowcount} catches")

        logger.info("Migration completed successfully!")
        logger.info("=" * 50)
        logger.info("NEXT STEPS:")
        logger.info("1. Restart the bayscan service: sudo systemctl restart bayscan.service")
        logger.info("2. Check logs: sudo journalctl -u bayscan.service -f")
        logger.info("3. Test logging a catch with new fields")
        logger.info("4. Verify environment snapshots are being captured")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error("Please restore from backup and check the error")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("HYPERLOCAL SPEC DATABASE MIGRATION")
    print("=" * 50)
    print()
    print("⚠️  WARNING: This will modify your database!")
    print()
    print("Before proceeding, ensure you have a backup:")
    print("  cp app/bayscan.db app/bayscan.db.backup")
    print()
    response = input("Continue with migration? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        success = migrate_database()
        sys.exit(0 if success else 1)
    else:
        print("Migration cancelled")
        sys.exit(0)
