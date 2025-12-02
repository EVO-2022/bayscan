#!/usr/bin/env python3
"""
Migration script to update bait_logs table to match new schema.

Changes:
- Rename 'time' column to 'timestamp'
- Rename 'zone' column to 'zone_id'
- Rename 'how_caught' column to 'method'
- Rename 'quantity' column to 'quantity_estimate'
- Add 'structure_type' column
- Add all environment snapshot columns
"""

import sqlite3
from datetime import datetime

def migrate_bait_logs():
    """Migrate bait_logs table to new schema."""
    conn = sqlite3.connect('fishing_forecast.db')
    cursor = conn.cursor()

    print("Starting bait_logs migration...")

    try:
        # Get existing data
        cursor.execute("SELECT id, bait_species, zone, time, quantity, how_caught, notes, created_at FROM bait_logs")
        existing_data = cursor.fetchall()
        print(f"Found {len(existing_data)} existing bait log records")

        # Drop old table
        cursor.execute("DROP TABLE IF EXISTS bait_logs_old")
        cursor.execute("ALTER TABLE bait_logs RENAME TO bait_logs_old")
        print("Renamed old table to bait_logs_old")

        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE bait_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                bait_species VARCHAR(50) NOT NULL,
                method VARCHAR(50) NOT NULL,
                quantity_estimate VARCHAR(20),
                zone_id VARCHAR(20) NOT NULL,
                structure_type VARCHAR(50),
                notes TEXT,

                -- Environment snapshot columns
                water_temp FLOAT,
                air_temp FLOAT,
                humidity FLOAT,
                barometric_pressure FLOAT,
                tide_height FLOAT,
                tide_stage VARCHAR(20),
                current_speed FLOAT,
                current_direction VARCHAR(10),
                wind_speed FLOAT,
                wind_direction VARCHAR(10),
                weather VARCHAR(50),
                time_of_day VARCHAR(20),
                moon_phase FLOAT,
                dock_lights_on BOOLEAN DEFAULT 0,

                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Created new bait_logs table")

        # Create indexes
        cursor.execute("CREATE INDEX idx_bait_logs_timestamp ON bait_logs(timestamp)")
        cursor.execute("CREATE INDEX idx_bait_logs_bait_species ON bait_logs(bait_species)")
        cursor.execute("CREATE INDEX idx_bait_logs_zone_id ON bait_logs(zone_id)")
        print("Created indexes")

        # Migrate data
        for row in existing_data:
            old_id, bait_species, zone, time, quantity, how_caught, notes, created_at = row

            # Convert quantity to quantity_estimate text
            if quantity is None or quantity == 0:
                quantity_estimate = 'none'
            elif quantity <= 5:
                quantity_estimate = 'few'
            else:
                quantity_estimate = 'plenty'

            cursor.execute("""
                INSERT INTO bait_logs (
                    id, timestamp, bait_species, method, quantity_estimate,
                    zone_id, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                old_id,
                time,  # time -> timestamp
                bait_species,
                how_caught or 'cast_net',  # how_caught -> method, default to cast_net
                quantity_estimate,  # quantity -> quantity_estimate
                zone,  # zone -> zone_id
                notes,
                created_at
            ))

        print(f"Migrated {len(existing_data)} records")

        # Drop old table
        cursor.execute("DROP TABLE bait_logs_old")
        print("Dropped old table")

        conn.commit()
        print("Migration completed successfully!")

        # Verify
        cursor.execute("PRAGMA table_info(bait_logs)")
        columns = cursor.fetchall()
        print("\nNew schema columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_bait_logs()
