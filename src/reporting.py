#!/usr/bin/env python3
"""
Reporting & Logging Module for Creative Automation Pipeline.
Logs generation details to SQLite database and/or JSON file.
"""
import json
import os
import sqlite3
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add src directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Unified logging
try:
    from utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level
except ImportError:
    # Fallback for when run as module
    from .utils.logger import log_info, log_warning, log_error, log_success, log_failure, log_debug, log_step, set_log_level, get_log_level

class PipelineReporter:
    def __init__(self, db_path: str = "../outputs/pipeline_logs.db", json_log_path: str = "../outputs/run_report.json"):
        """
        Initialize reporter with SQLite database and JSON log file.
        """
        self.db_path = db_path
        self.json_log_path = json_log_path
        
        # Ensure output directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(json_log_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.init_database()
        
        # Load existing JSON log or create empty list
        self.json_log = self.load_json_log()
    
    def init_database(self):
        """Create SQLite table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS generation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                product TEXT,
                aspect_ratio TEXT,
                width INTEGER,
                height INTEGER,
                compliance_status TEXT,
                generation_time_ms INTEGER,
                image_path TEXT,
                checks_passed INTEGER,
                total_checks INTEGER,
                brand_colors_passed BOOLEAN,
                logo_presence_passed BOOLEAN,
                legal_check_passed BOOLEAN,
                campaign_message TEXT,
                workflow_name TEXT,
                seed INTEGER,
                additional_info TEXT
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON generation_logs(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_product ON generation_logs(product)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_compliance ON generation_logs(compliance_status)
        ''')
        
        conn.commit()
        conn.close()
    
    def load_json_log(self) -> List[Dict[str, Any]]:
        """Load existing JSON log file or return empty list."""
        if Path(self.json_log_path).exists():
            try:
                with open(self.json_log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save_json_log(self):
        """Save JSON log to file."""
        with open(self.json_log_path, 'w', encoding='utf-8') as f:
            json.dump(self.json_log, f, indent=2, default=str)
    
    def log_generation(
        self,
        product: str,
        aspect_ratio: str,
        width: int,
        height: int,
        compliance_status: str,
        generation_time_ms: int,
        image_path: str,
        checks_passed: int,
        total_checks: int,
        brand_colors_passed: bool,
        logo_presence_passed: bool,
        legal_check_passed: bool,
        campaign_message: str = "",
        workflow_name: str = "default",
        seed: int = 0,
        additional_info: Dict[str, Any] = None
    ) -> int:
        """
        Log a generation event to both SQLite and JSON.
        Returns the log ID.
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare additional info as JSON string
        additional_info_str = json.dumps(additional_info) if additional_info else None
        
        # SQLite insert
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO generation_logs (
                timestamp, product, aspect_ratio, width, height,
                compliance_status, generation_time_ms, image_path,
                checks_passed, total_checks, brand_colors_passed,
                logo_presence_passed, legal_check_passed, campaign_message,
                workflow_name, seed, additional_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp, product, aspect_ratio, width, height,
            compliance_status, generation_time_ms, image_path,
            checks_passed, total_checks, brand_colors_passed,
            logo_presence_passed, legal_check_passed, campaign_message,
            workflow_name, seed, additional_info_str
        ))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # JSON log entry
        log_entry = {
            "id": log_id,
            "timestamp": timestamp,
            "product": product,
            "aspect_ratio": aspect_ratio,
            "dimensions": {"width": width, "height": height},
            "compliance_status": compliance_status,
            "generation_time_ms": generation_time_ms,
            "image_path": image_path,
            "checks": {
                "passed": checks_passed,
                "total": total_checks,
                "brand_colors": brand_colors_passed,
                "logo_presence": logo_presence_passed,
                "legal_check": legal_check_passed
            },
            "campaign_message": campaign_message,
            "workflow_name": workflow_name,
            "seed": seed,
            "additional_info": additional_info
        }
        
        self.json_log.append(log_entry)
        self.save_json_log()
        
        return log_id
    
    def query_logs(
        self,
        product: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        compliance_status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query logs from SQLite database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM generation_logs WHERE 1=1"
        params = []
        
        if product:
            query += " AND product LIKE ?"
            params.append(f"%{product}%")
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if compliance_status:
            query += " AND compliance_status = ?"
            params.append(compliance_status)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert rows to dicts
        result = [dict(row) for row in rows]
        
        conn.close()
        return result
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics from logs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total generations
        cursor.execute("SELECT COUNT(*) FROM generation_logs")
        stats["total_generations"] = cursor.fetchone()[0]
        
        # Average generation time
        cursor.execute("SELECT AVG(generation_time_ms) FROM generation_logs")
        stats["avg_generation_time_ms"] = cursor.fetchone()[0]
        
        # Compliance pass rate
        cursor.execute("SELECT compliance_status, COUNT(*) FROM generation_logs GROUP BY compliance_status")
        compliance_counts = dict(cursor.fetchall())
        stats["compliance_counts"] = compliance_counts
        
        # Pass rate percentage
        total = stats["total_generations"]
        passed = compliance_counts.get("PASS", 0)
        stats["compliance_pass_rate"] = (passed / total * 100) if total > 0 else 0
        
        # Products count
        cursor.execute("SELECT product, COUNT(*) FROM generation_logs GROUP BY product ORDER BY COUNT(*) DESC")
        stats["products"] = dict(cursor.fetchall())
        
        conn.close()
        return stats
    
    def export_to_csv(self, output_path: str):
        """Export logs to CSV file."""
        import csv
        
        logs = self.query_logs(limit=10000)
        if not logs:
            log_info("No logs to export.")
            return
        
        fieldnames = logs[0].keys()
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(logs)
        
        log_info(f"Exported {len(logs)} logs to {output_path}")


def main():
    """Test the reporting module."""
    import argparse
    import logging
    
    parser = argparse.ArgumentParser(description="Test reporting module")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug output")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
                       default="INFO", help="Set log level (default: INFO)")
    args = parser.parse_args()
    
    # Set log level based on verbose flag or log-level argument
    if args.verbose:
        set_log_level(logging.DEBUG)
        log_debug("Verbose debug output enabled")
    else:
        level = get_log_level(args.log_level)
        set_log_level(level)
        if level <= logging.DEBUG:
            log_debug(f"Log level set to {args.log_level}")
    
    reporter = PipelineReporter(db_path=":memory:", json_log_path="/tmp/test_report.json")
    
    # Log some test entries
    for i in range(3):
        log_id = reporter.log_generation(
            product=f"Product_{i}",
            aspect_ratio="16:9",
            width=1920,
            height=1080,
            compliance_status="PASS",
            generation_time_ms=1500 + i * 100,
            image_path=f"/tmp/image_{i}.png",
            checks_passed=3,
            total_checks=3,
            brand_colors_passed=True,
            logo_presence_passed=True,
            legal_check_passed=True,
            campaign_message="Test campaign",
            workflow_name="default",
            seed=42 + i
        )
        log_info(f"Logged generation with ID: {log_id}")
    
    # Query logs
    logs = reporter.query_logs(limit=5)
    log_info(f"\nRetrieved {len(logs)} logs:")
    for log in logs:
        log_info(f"  {log['timestamp']} - {log['product']} - {log['compliance_status']}")
    
    # Get summary stats
    stats = reporter.get_summary_stats()
    log_info(f"\nSummary stats: {stats}")


if __name__ == "__main__":
    main()