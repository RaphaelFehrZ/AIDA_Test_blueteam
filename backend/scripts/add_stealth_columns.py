"""
Migration script: Add stealth & evasion columns to the assessments table.

Since the project uses create_all() (not Alembic), this script uses
ALTER TABLE ... ADD COLUMN IF NOT EXISTS for safe, idempotent migration.

Usage:
    python backend/scripts/add_stealth_columns.py
"""
import os
import sys

# Add backend to path for database import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import engine
from sqlalchemy import text


COLUMNS = [
    ("stealth_profile", "VARCHAR(50) DEFAULT 'normal'"),
    ("proxy_config", "TEXT"),
    ("custom_user_agent", "TEXT"),
    ("scan_delay", "VARCHAR(50)"),
    ("max_rate", "INTEGER"),
    ("decoy_ips", "TEXT"),
    ("source_port", "INTEGER"),
    ("nmap_timing", "VARCHAR(10)"),
    ("fragmentation", "BOOLEAN DEFAULT FALSE"),
    ("randomize_hosts", "BOOLEAN DEFAULT FALSE"),
    ("extra_nmap_evasion", "TEXT"),
    ("nikto_evasion", "VARCHAR(50)"),
    ("nikto_tuning", "VARCHAR(50)"),
]


def migrate():
    with engine.connect() as conn:
        for col_name, col_type in COLUMNS:
            stmt = text(
                f"ALTER TABLE assessments ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            )
            conn.execute(stmt)
            print(f"  + {col_name} ({col_type})")
        conn.commit()
    print("\nMigration complete: stealth columns added to assessments table.")


if __name__ == "__main__":
    print("Adding stealth & evasion columns to assessments table...\n")
    migrate()
