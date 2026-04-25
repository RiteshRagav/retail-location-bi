"""
Database module for storing and retrieving analysis history.

Uses SQLite for lightweight persistence. No external services required.
Stores all analysis results for client reference and historical tracking.

Rules:
- init_database() is called ONCE on FastAPI startup. Never call it inside query functions.
- All schema changes use ALTER TABLE ... ADD COLUMN (non-destructive).
- Never DROP any table.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path


DATABASE_PATH = Path(__file__).parent.parent / "analysis_history.db"

_DB_INITIALIZED = False


def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database schema. Called once on app startup."""
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return
    _DB_INITIALIZED = True

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # ── Core analyses table ──────────────────────────────────────────────
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

    # ── Non-destructive migrations ────────────────────────────────────────
    _safe_add_column(cursor, "analyses", "outcome_status",      "TEXT DEFAULT NULL")
    _safe_add_column(cursor, "analyses", "outcome_flagged_at",  "TEXT DEFAULT NULL")
    _safe_add_column(cursor, "analyses", "pdf_exported",        "INTEGER DEFAULT 0")
    _safe_add_column(cursor, "analyses", "explanation_rating",  "INTEGER DEFAULT NULL")
    _safe_add_column(cursor, "analyses", "poi_data_json",       "TEXT DEFAULT NULL")

    # ── New tracking tables ───────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER,
            agent_name TEXT,
            latency_ms REAL,
            anomaly_flagged INTEGER DEFAULT 0,
            error_message TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            analysis_id INTEGER,
            metadata_json TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


def _safe_add_column(cursor, table: str, column: str, definition: str):
    """Add a column to a table if it doesn't already exist."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError:
        pass  # Column already exists — skip silently


# ─────────────────────────────────────────────────────────────────────────────
# Write functions
# ─────────────────────────────────────────────────────────────────────────────

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
    validation_warnings: list = None,
    competitors_list: list = None,
    transport_nodes_list: list = None,
    nearby_places_list: list = None,
) -> int:
    """
    Store an analysis result in the database.
    Returns: analysis_id — the ID of the stored record.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    coordinates_json = json.dumps(coordinates) if coordinates else None
    warnings_json = json.dumps(validation_warnings) if validation_warnings else None
    poi_data_json = json.dumps({
        "competitors": competitors_list or [],
        "transport": transport_nodes_list or [],
        "amenities": nearby_places_list or [],
    })

    cursor.execute("""
        INSERT INTO analyses (
            location, store_type, radius_km,
            demand_score, competition_score, accessibility_score, diversity_score,
            viability_score, recommendation, explanation,
            demand_weight, competition_weight, accessibility_weight, diversity_weight,
            coordinates, validation_warnings, poi_data_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        location, store_type, radius_km,
        demand_score, competition_score, accessibility_score, diversity_score,
        viability_score, recommendation, explanation,
        demand_weight, competition_weight, accessibility_weight, diversity_weight,
        coordinates_json, warnings_json, poi_data_json,
    ))

    conn.commit()
    analysis_id = cursor.lastrowid
    conn.close()
    return analysis_id


def update_outcome(analysis_id: int, status: str) -> bool:
    """Update the outcome status of an analysis."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE analyses SET outcome_status = ?, outcome_flagged_at = ? WHERE id = ?",
        (status, datetime.utcnow().isoformat(), analysis_id),
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def update_explanation_rating(analysis_id: int, rating: int) -> bool:
    """Store a thumbs-up (1) or thumbs-down (-1) rating for the Gemini explanation."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE analyses SET explanation_rating = ? WHERE id = ?",
        (rating, analysis_id),
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def mark_pdf_exported(analysis_id: int) -> bool:
    """Flag an analysis as having had its PDF exported."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE analyses SET pdf_exported = 1 WHERE id = ?",
        (analysis_id,),
    )
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def log_user_event(event_type: str, analysis_id: int = None, metadata: dict = None):
    """Insert a row into user_events."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_events (event_type, analysis_id, metadata_json) VALUES (?, ?, ?)",
        (event_type, analysis_id, json.dumps(metadata or {})),
    )
    conn.commit()
    conn.close()


def get_total_count() -> int:
    """Return total number of analysis records."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM analyses")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ─────────────────────────────────────────────────────────────────────────────
# Read functions
# ─────────────────────────────────────────────────────────────────────────────

def _parse_record(columns, row) -> dict:
    """Convert a raw DB row into a typed dict, parsing JSON fields."""
    record = dict(zip(columns, row))
    for field in ("coordinates", "validation_warnings", "poi_data_json"):
        if record.get(field):
            try:
                record[field] = json.loads(record[field])
            except (json.JSONDecodeError, TypeError):
                record[field] = None
    return record


def get_all_analyses() -> list:
    """Retrieve all stored analyses, most recent first."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses ORDER BY timestamp DESC")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [_parse_record(columns, row) for row in rows]


def get_recent_analyses(limit: int = 20) -> list:
    """Retrieve the most recent N analyses."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses ORDER BY timestamp DESC LIMIT ?", (limit,))
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [_parse_record(columns, row) for row in rows]


def get_analysis_by_id(analysis_id: int) -> dict:
    """Retrieve a specific analysis by ID."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _parse_record(columns, row)


def get_kpi_data() -> dict:
    """
    Compute KPI metrics directly from the DB.
    Never cached — always reads live data.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM analyses")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE timestamp >= datetime('now', '-30 days')")
    last_30 = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE viability_score >= 70")
    strong = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE viability_score >= 40 AND viability_score < 70")
    moderate = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE viability_score < 40")
    risky = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE pdf_exported = 1")
    pdf_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE explanation_rating = 1")
    thumbs_up = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE explanation_rating IS NOT NULL")
    rated = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM analyses WHERE outcome_status IS NOT NULL")
    outcome_flagged = cursor.fetchone()[0]

    cursor.execute("SELECT location FROM analyses")
    locations = [row[0] for row in cursor.fetchall()]

    conn.close()

    # City breakdown — extract first token before comma
    city_counts: dict = {}
    for loc in locations:
        city = loc.split(",")[0].strip()
        city_counts[city] = city_counts.get(city, 0) + 1

    return {
        "total_analyses": total,
        "analyses_last_30_days": last_30,
        "score_distribution": {"strong": strong, "moderate": moderate, "risky": risky},
        "pdf_export_rate": round((pdf_count / total * 100) if total else 0.0, 1),
        "explanation_positive_rate": round((thumbs_up / rated * 100) if rated else 0.0, 1),
        "outcome_flagged_count": outcome_flagged,
        "city_breakdown": city_counts,
        "multi_location_session_rate": 0.0,  # requires session tracking — placeholder
    }


def delete_analysis(analysis_id: int) -> bool:
    """Delete an analysis record. Returns True if successful."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


# ─────────────────────────────────────────────────────────────────────────────
# Weight Presets
# ─────────────────────────────────────────────────────────────────────────────

def init_presets_table():
    """Create weight_presets table and seed built-ins. Called once on startup."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weight_presets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL UNIQUE,
            demand        REAL NOT NULL,
            competition   REAL NOT NULL,
            accessibility REAL NOT NULL,
            diversity     REAL NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)
    existing = conn.execute("SELECT COUNT(*) FROM weight_presets").fetchone()[0]
    if existing == 0:
        built_ins = [
            ("Equal Weights",  0.25, 0.25, 0.25, 0.25),
            ("Growth",         0.40, 0.15, 0.25, 0.20),
            ("Risk-Averse",    0.20, 0.40, 0.20, 0.20),
            ("Transit-First",  0.20, 0.20, 0.45, 0.15),
            ("Diversity-Led",  0.20, 0.15, 0.20, 0.45),
        ]
        conn.executemany(
            "INSERT INTO weight_presets (name, demand, competition, accessibility, diversity) "
            "VALUES (?,?,?,?,?)",
            built_ins,
        )
    conn.commit()
    conn.close()


def get_all_presets() -> list:
    """Return all weight presets ordered by id."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, demand, competition, accessibility, diversity "
        "FROM weight_presets ORDER BY id"
    ).fetchall()
    conn.close()
    return [
        {
            "id": r["id"], "name": r["name"],
            "demand": r["demand"], "competition": r["competition"],
            "accessibility": r["accessibility"], "diversity": r["diversity"],
        }
        for r in rows
    ]


def save_preset(name: str, demand: float, competition: float,
                accessibility: float, diversity: float) -> dict:
    """Upsert a preset by name. Returns the saved record."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO weight_presets (name, demand, competition, accessibility, diversity)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            demand        = excluded.demand,
            competition   = excluded.competition,
            accessibility = excluded.accessibility,
            diversity     = excluded.diversity
    """, (name, demand, competition, accessibility, diversity))
    conn.commit()
    row = conn.execute(
        "SELECT id, name, demand, competition, accessibility, diversity "
        "FROM weight_presets WHERE name = ?",
        (name,),
    ).fetchone()
    conn.close()
    return {
        "id": row["id"], "name": row["name"],
        "demand": row["demand"], "competition": row["competition"],
        "accessibility": row["accessibility"], "diversity": row["diversity"],
    }
