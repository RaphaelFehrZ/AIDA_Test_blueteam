"""
Migration script: Add CTF columns to assessments and cards tables.

Since the project uses create_all() (not Alembic), this script uses
ALTER TABLE ... ADD COLUMN IF NOT EXISTS for safe, idempotent migration.

Usage:
    python backend/scripts/add_ctf_columns.py
"""
import os
import sys

# Add backend to path for database import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import engine
from sqlalchemy import text


ASSESSMENT_COLUMNS = [
    ("ctf_mode", "BOOLEAN DEFAULT FALSE"),
]

CARD_COLUMNS = [
    ("flag", "TEXT"),
    ("flag_status", "VARCHAR(50)"),
    ("points", "INTEGER"),
    ("challenge_category", "VARCHAR(50)"),
]


def migrate():
    with engine.connect() as conn:
        print("Updating assessments table...")
        for col_name, col_type in ASSESSMENT_COLUMNS:
            stmt = text(
                f"ALTER TABLE assessments ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            )
            conn.execute(stmt)
            print(f"  + {col_name} ({col_type})")

        print("\nUpdating cards table...")
        for col_name, col_type in CARD_COLUMNS:
            stmt = text(
                f"ALTER TABLE cards ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            )
            conn.execute(stmt)
            print(f"  + {col_name} ({col_type})")

        conn.commit()
    print("\nMigration complete: CTF columns added.")


if __name__ == "__main__":
    print("Adding CTF columns to assessments and cards tables...\n")
    migrate()
