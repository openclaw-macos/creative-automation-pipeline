#!/usr/bin/env python3
"""
Migration script for pipeline logging database.
Moves database from external location to outputs/logs/ and enhances schema.
"""
import os
import sys
import sqlite3
import shutil
from pathlib import Path

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure
except ImportError:
    # Fallback logging
    def log_info(msg): print(f"INFO: {msg}")
    def log_warning(msg): print(f"WARNING: {msg}")
    def log_error(msg): print(f"ERROR: {msg}")
    def log_success(msg): print(f"SUCCESS: {msg}")
    def log_failure(msg): print(f"FAILURE: {msg}")

def migrate_database():
    """Migrate database from external location to outputs/logs/."""
    
    # Paths
    external_db = "/Users/youee-mac/A42_Folder/creative-automation-pipeline/outputs/pipeline_logs.db"
    project_root = Path(__file__).parent.parent
    new_db_dir = project_root / "outputs" / "logs"
    new_db_path = new_db_dir / "pipeline_logs.db"
    
    log_info("=== Pipeline Logging Database Migration ===")
    log_info(f"Source: {external_db}")
    log_info(f"Destination: {new_db_path}")
    
    # Check if source exists
    if not os.path.exists(external_db):
        log_error(f"Source database not found: {external_db}")
        log_info("Creating new database at destination...")
        new_db_dir.mkdir(parents=True, exist_ok=True)
        init_new_database(str(new_db_path))
        return True
    
    # Create destination directory
    new_db_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy database
    try:
        shutil.copy2(external_db, str(new_db_path))
        log_success(f"Database copied: {os.path.getsize(new_db_path)} bytes")
    except Exception as e:
        log_error(f"Failed to copy database: {e}")
        return False
    
    # Enhance schema
    try:
        enhance_schema(str(new_db_path))
        log_success("Schema enhanced successfully")
    except Exception as e:
        log_error(f"Failed to enhance schema: {e}")
        return False
    
    # Verify migration
    try:
        verify_migration(str(new_db_path))
        log_success("Migration verified successfully")
    except Exception as e:
        log_error(f"Migration verification failed: {e}")
        return False
    
    log_success("=== Migration Completed Successfully ===")
    log_info(f"New database location: {new_db_path}")
    log_info("Update reporting.py to use new location")
    return True

def init_new_database(db_path: str):
    """Initialize a new database with enhanced schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create enhanced generation_logs table
    cursor.execute('''
        CREATE TABLE generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            stage TEXT NOT NULL DEFAULT 'image_generation',
            product TEXT,
            brief_name TEXT,
            status TEXT,
            aspect_ratio TEXT,
            width INTEGER,
            height INTEGER,
            compliance_status TEXT,
            generation_time_ms INTEGER,
            duration_ms INTEGER,
            image_path TEXT,
            output_path TEXT,
            file_size_bytes INTEGER,
            checks_passed INTEGER,
            total_checks INTEGER,
            brand_colors_passed BOOLEAN,
            logo_presence_passed BOOLEAN,
            legal_check_passed BOOLEAN,
            campaign_message TEXT,
            workflow_name TEXT,
            seed INTEGER,
            video_duration_sec REAL,
            youtube_video_id TEXT,
            heygen_video_id TEXT,
            youtube_privacy_status TEXT,
            additional_info TEXT
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX idx_timestamp ON generation_logs(timestamp)')
    cursor.execute('CREATE INDEX idx_product ON generation_logs(product)')
    cursor.execute('CREATE INDEX idx_compliance ON generation_logs(compliance_status)')
    cursor.execute('CREATE INDEX idx_stage ON generation_logs(stage)')
    cursor.execute('CREATE INDEX idx_status ON generation_logs(status)')
    
    conn.commit()
    conn.close()
    log_info(f"Created new database with enhanced schema: {db_path}")

def enhance_schema(db_path: str):
    """Add new columns to existing database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get current columns
    cursor.execute("PRAGMA table_info(generation_logs)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Columns to add
    new_columns = [
        ('stage', 'TEXT', "'image_generation'"),
        ('brief_name', 'TEXT', 'NULL'),
        ('status', 'TEXT', 'NULL'),
        ('duration_ms', 'INTEGER', 'NULL'),
        ('output_path', 'TEXT', 'NULL'),
        ('file_size_bytes', 'INTEGER', 'NULL'),
        ('video_duration_sec', 'REAL', 'NULL'),
        ('youtube_video_id', 'TEXT', 'NULL'),
        ('heygen_video_id', 'TEXT', 'NULL'),
        ('youtube_privacy_status', 'TEXT', 'NULL')
    ]
    
    # Add missing columns
    for col_name, col_type, default_value in new_columns:
        if col_name not in existing_columns:
            cursor.execute(f'ALTER TABLE generation_logs ADD COLUMN {col_name} {col_type} DEFAULT {default_value}')
            log_info(f"Added column: {col_name}")
    
    # Update existing rows
    cursor.execute("UPDATE generation_logs SET stage = 'image_generation' WHERE stage IS NULL")
    cursor.execute("UPDATE generation_logs SET status = 'success' WHERE status IS NULL")
    
    # Create new indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stage ON generation_logs(stage)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON generation_logs(status)')
    
    conn.commit()
    
    # Verify enhancement
    cursor.execute("SELECT COUNT(*) FROM generation_logs")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT stage) FROM generation_logs")
    stages = cursor.fetchone()[0]
    
    conn.close()
    
    log_info(f"Enhanced schema: {total} total records, {stages} stage(s)")
    return True

def verify_migration(db_path: str):
    """Verify migration was successful."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='generation_logs'")
    if not cursor.fetchone():
        raise Exception("Table 'generation_logs' not found")
    
    # Check new columns exist
    cursor.execute("PRAGMA table_info(generation_logs)")
    columns = [col[1] for col in cursor.fetchall()]
    required_columns = ['stage', 'status', 'duration_ms']
    
    for col in required_columns:
        if col not in columns:
            raise Exception(f"Required column '{col}' not found")
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM generation_logs")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    log_info(f"Verification passed: {count} records, {len(columns)} columns")
    return True

def main():
    """Run migration."""
    try:
        success = migrate_database()
        if success:
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Update reporting.py with new database path")
            print("2. Test logging with updated PipelineReporter")
            print("3. Run campaign scripts to verify logging")
        else:
            print("\n❌ Migration failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()