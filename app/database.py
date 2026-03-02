"""
Database module for storing and retrieving analysis history.

Uses SQLite for lightweight persistence. No external services required.
Stores all analysis results for client reference and historical tracking.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).parent.parent / "analysis_history.db"


def init_database():
    """Initialize database schema if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            store_type TEXT NOT NULL,
            radius_km REAL NOT NULL,
            demand_score REAL,
            competition_score REAL,
            accessibility_score REAL,
            diversity_score REAL,
            viability_score REAL,
            recommendation TEXT,
            explanation TEXT,
            demand_weight REAL DEFAULT 0.25,
            competition_weight REAL DEFAULT 0.25,
            accessibility_weight REAL DEFAULT 0.25,
            diversity_weight REAL DEFAULT 0.25,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            coordinates TEXT,
            validation_warnings TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def store_analysis(
    location: str,
    store_type: str,
    radius_km: float,
    demand_score: float,
    competition_score: float,
    accessibility_score: float,
    diversity_score: float,
    viability_score: float,
    recommendation: str,
    explanation: str,
    demand_weight: float = 0.25,
    competition_weight: float = 0.25,
    accessibility_weight: float = 0.25,
    diversity_weight: float = 0.25,
    coordinates: dict = None,
    validation_warnings: list = None
) -> int:
    """
    Store an analysis result in the database.
    
    Returns:
        analysis_id: The ID of the stored record
    """
    init_database()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    coordinates_json = json.dumps(coordinates) if coordinates else None
    warnings_json = json.dumps(validation_warnings) if validation_warnings else None
    
    cursor.execute("""
        INSERT INTO analyses (
            location, store_type, radius_km,
            demand_score, competition_score, accessibility_score, diversity_score,
            viability_score, recommendation, explanation,
            demand_weight, competition_weight, accessibility_weight, diversity_weight,
            coordinates, validation_warnings
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        location, store_type, radius_km,
        demand_score, competition_score, accessibility_score, diversity_score,
        viability_score, recommendation, explanation,
        demand_weight, competition_weight, accessibility_weight, diversity_weight,
        coordinates_json, warnings_json
    ))
    
    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    
    return analysis_id


def get_all_analyses() -> list:
    """Retrieve all stored analyses, most recent first."""
    init_database()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM analyses
        ORDER BY timestamp DESC
    """)
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    analyses = []
    for row in rows:
        record = dict(zip(columns, row))
        # Parse JSON fields
        if record['coordinates']:
            record['coordinates'] = json.loads(record['coordinates'])
        if record['validation_warnings']:
            record['validation_warnings'] = json.loads(record['validation_warnings'])
        analyses.append(record)
    
    return analyses


def get_analysis_by_id(analysis_id: int) -> dict:
    """Retrieve a specific analysis by ID."""
    init_database()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM analyses WHERE id = ?
    """, (analysis_id,))
    
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    record = dict(zip(columns, row))
    # Parse JSON fields
    if record['coordinates']:
        record['coordinates'] = json.loads(record['coordinates'])
    if record['validation_warnings']:
        record['validation_warnings'] = json.loads(record['validation_warnings'])
    
    return record


def get_recent_analyses(limit: int = 10) -> list:
    """Retrieve the most recent N analyses."""
    init_database()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM analyses
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    
    analyses = []
    for row in rows:
        record = dict(zip(columns, row))
        if record['coordinates']:
            record['coordinates'] = json.loads(record['coordinates'])
        if record['validation_warnings']:
            record['validation_warnings'] = json.loads(record['validation_warnings'])
        analyses.append(record)
    
    return analyses


def delete_analysis(analysis_id: int) -> bool:
    """Delete an analysis record. Returns True if successful."""
    init_database()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success
