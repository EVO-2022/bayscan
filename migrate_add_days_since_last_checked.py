#!/usr/bin/env python3
"""
Migration: Add days_since_last_checked column to catches and bait_logs tables.

This field is used for trap entries (crab traps, bait traps) to track the soak window.
"""

import sqlite3
import sys

DB_PATH = "/home/evo/fishing-forecast/fishing_forecast.db"

def migrate():
    """Add days_since_last_checked column to catches and bait_logs tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if column already exists in catches table
        cursor.execute("PRAGMA table_info(catches)")
        catches_columns = [col[1] for col in cursor.fetchall()]

        if 'days_since_last_checked' not in catches_columns:
            print("Adding days_since_last_checked to catches table...")
            cursor.execute("ALTER TABLE catches ADD COLUMN days_since_last_checked INTEGER")
            print("✓ Added days_since_last_checked to catches")
        else:
            print("✓ days_since_last_checked already exists in catches")

        # Check if column already exists in bait_logs table
        cursor.execute("PRAGMA table_info(bait_logs)")
        bait_logs_columns = [col[1] for col in cursor.fetchall()]

        if 'days_since_last_checked' not in bait_logs_columns:
            print("Adding days_since_last_checked to bait_logs table...")
            cursor.execute("ALTER TABLE bait_logs ADD COLUMN days_since_last_checked INTEGER")
            print("✓ Added days_since_last_checked to bait_logs")
        else:
            print("✓ days_since_last_checked already exists in bait_logs")

        conn.commit()
        conn.close()

        print("\n✅ Migration completed successfully")
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
