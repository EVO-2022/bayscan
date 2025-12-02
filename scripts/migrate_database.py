#!/usr/bin/env python3
"""
Database migration script to add new columns to existing tables.

This adds:
- rig_type column to catches table
"""
import sys
import os
import sqlite3

# Database path
DB_PATH = "/home/evo/fishing-forecast/fishing_forecast.db"


def migrate_database():
    """Add missing columns to existing tables."""
    print("Migrating database...")
    print(f"Database: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if catches table exists and get its columns
    cursor.execute("PRAGMA table_info(catches)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    print("Current catches table columns:")
    for col, typ in columns.items():
        print(f"  - {col}: {typ}")

    # Define columns to add
    new_columns = [
        ('zone_id', 'VARCHAR(20)'),
        ('distance_from_dock', 'VARCHAR(20)'),
        ('depth_estimate', 'VARCHAR(20)'),
        ('structure_type', 'VARCHAR(50)'),
        ('bait_used', 'VARCHAR(100)'),
        ('presentation', 'VARCHAR(100)'),
        ('rig_type', 'VARCHAR(50)'),
        ('predator_seen_recently', 'BOOLEAN'),
        ('water_temp', 'FLOAT'),
        ('air_temp', 'FLOAT'),
        ('humidity', 'FLOAT'),
        ('barometric_pressure', 'FLOAT'),
        ('tide_stage', 'VARCHAR(20)'),
        ('current_speed', 'FLOAT'),
        ('current_direction', 'VARCHAR(10)'),
        ('wind_direction', 'VARCHAR(10)'),
        ('weather', 'VARCHAR(50)'),
        ('time_of_day', 'VARCHAR(20)'),
        ('moon_phase', 'FLOAT'),
        ('dock_lights_on', 'BOOLEAN'),
    ]

    print("\nAdding missing columns...")
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"  Adding {col_name} ({col_type})...")
            try:
                cursor.execute(f"ALTER TABLE catches ADD COLUMN {col_name} {col_type}")
                conn.commit()
                print(f"    ✓ Added {col_name}")
            except Exception as e:
                print(f"    ✗ Error adding {col_name}: {e}")
        else:
            print(f"  ✓ {col_name} already exists")

    conn.close()
    print("\n✓ Migration complete!\n")


if __name__ == "__main__":
    migrate_database()
