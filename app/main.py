"""
SiteSense AI — FastAPI Backend
Multi-agent retail location intelligence API.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import tempfile, os, json
import httpx

from app import config

from app.orchestrator import run_analysis
from app.database import (
    init_database, init_presets_table,
    store_analysis, get_all_analyses,
    get_recent_analyses, get_analysis_by_id,
    update_outcome, update_explanation_rating,
    mark_pdf_exported, log_user_event,
    get_total_count, get_kpi_data,
    get_all_presets, save_preset,
)


# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SiteSense AI",
    description="Multi-Agent Retail Location Intelligence API",
    version="3.0",
)


@app.on_event("startup")
def startup():
    """Initialize database schema and seed preset table once on app startup."""
    init_database()
    init_presets_table()


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class MultiLocationRequest(BaseModel):
    locations: List[str]
    store_type: str = "cafe"
    radius_km: int = 1
    demand_weight: float = 0.25
    competition_weight: float = 0.25
    accessibility_weight: float = 0.25
    diversity_weight: float = 0.25


class OutcomeRequest(BaseModel):
    status: str  # "Succeeded" | "Failed" | "Not Proceeded"


class ExplanationRatingRequest(BaseModel):
    rating: int  # 1 or -1


# ── POI Image models ──────────────────────────────────────────────────────────

class POIImage(BaseModel):
    url: str
    thumb_url: str
    category: str
    photographer: str
    photographer_url: str


class POIImageList(BaseModel):
    images: List[POIImage]


# ── Weight Preset models ──────────────────────────────────────────────────────

class WeightPreset(BaseModel):
    id: int
    name: str
    demand: float
    competition: float
    accessibility: float
    diversity: float


class WeightPresetList(BaseModel):
    presets: List[WeightPreset]


class CreatePresetRequest(BaseModel):
    name: str
    demand: float
    competition: float
    accessibility: float
    diversity: float

    @validator("name")
    def name_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Preset name cannot be empty")
        if len(v) > 50:
            raise ValueError("Preset name must be 50 characters or fewer")
        return v

    @validator("demand", "competition", "accessibility", "diversity")
    def weight_in_range(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError("Each weight must be between 0.0 and 1.0")
        return round(v, 4)


class LogEventRequest(BaseModel):
    event_type: str
    analysis_id: Optional[int] = None
    metadata: Optional[dict] = {}


class HealthResponse(BaseModel):
    status: str
    db_records: int
    timestamp: str


class KPIResponse(BaseModel):
    total_analyses: int
    analyses_last_30_days: int
    score_distribution: dict
    pdf_export_rate: float
    explanation_positive_rate: float
    outcome_flagged_count: int
    city_breakdown: dict
    multi_location_session_rate: float


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    """Lightweight health check — returns status and total DB record count."""
    return {
        "status": "ok",
        "db_records": get_total_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core analysis
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/analyze")
def analyze(
    location: str,
    store_type: str = "cafe",
    radius_km: int = 1,
    demand_weight: float = 0.25,
    competition_weight: float = 0.25,
    accessibility_weight: float = 0.25,
    diversity_weight: float = 0.25,
    save_to_history: bool = True,
):
    """
    Analyze a single retail location through the full 8-agent LangGraph pipeline.
    Weights must sum to 1.0 (validated here).
    """
    try:
        if radius_km < 1 or radius_km > 5:
            raise HTTPException(status_code=400, detail="Radius must be between 1-5 km")

        total_weight = demand_weight + competition_weight + accessibility_weight + diversity_weight
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail="Weights must sum to 1.0")

        result = run_analysis(
            location=location,
            store_type=store_type,
            radius_km=radius_km,
            demand_weight=demand_weight,
            competition_weight=competition_weight,
            accessibility_weight=accessibility_weight,
            diversity_weight=diversity_weight,
        )

        response = {
            "location": result["location"],
            "latitude": result["lat"],
            "longitude": result["lon"],
            "demand_score": result["demand_score"],
            "competition_score": result["competition_score"],
            "accessibility_score": result["accessibility_score"],
            "diversity_score": result["diversity_score"],
            "viability_score": result["viability_score"],
            "recommendation": result["recommendation"],
            "explanation": result["explanation"],
            "validation_warnings": result.get("warnings") or [],
            "competitors_list": result.get("competitors_list", []),
            "transport_nodes_list": result.get("transport_nodes_list", []),
            "weights": {
                "demand": demand_weight,
                "competition": competition_weight,
                "accessibility": accessibility_weight,
                "diversity": diversity_weight,
            },
        }

        analysis_id = None
        if save_to_history:
            try:
                analysis_id = store_analysis(
                    location=result["location"],
                    store_type=store_type,
                    radius_km=radius_km,
                    demand_score=result["demand_score"],
                    competition_score=result["competition_score"],
                    accessibility_score=result["accessibility_score"],
                    diversity_score=result["diversity_score"],
                    viability_score=result["viability_score"],
                    recommendation=result["recommendation"],
                    explanation=result["explanation"],
                    demand_weight=demand_weight,
                    competition_weight=competition_weight,
                    accessibility_weight=accessibility_weight,
                    diversity_weight=diversity_weight,
                    coordinates={"lat": result["lat"], "lon": result["lon"]},
                    validation_warnings=result.get("warnings"),
                    competitors_list=result.get("competitors_list", []),
                    transport_nodes_list=result.get("transport_nodes_list", []),
                    nearby_places_list=result.get("nearby_places_list", []),
                )
            except Exception as e:
                print(f"Warning: Could not save to history: {e}")

        response["analysis_id"] = analysis_id
        return response

    except HTTPException:
        raise
    except ValueError as e:
        # Only real geocoding failures produce a plain ValueError
        # (JSONDecodeError is now handled inside data_fetch and never raises)
        return {"error": f"Location not found: {e}"}
    except Exception as e:
        return {"error": f"Analysis failed: {e}"}


@app.post("/analyze-multiple")
def analyze_multiple(body: MultiLocationRequest):
    """
    Analyze up to 3 locations and return ranked results (by viability score, desc).
    """
    try:
        if not (1 <= len(body.locations) <= 3):
            raise HTTPException(status_code=400, detail="Must analyze 1-3 locations")

        results = []
        for location in body.locations:
            try:
                result = run_analysis(
                    location=location,
                    store_type=body.store_type,
                    radius_km=body.radius_km,
                    demand_weight=body.demand_weight,
                    competition_weight=body.competition_weight,
                    accessibility_weight=body.accessibility_weight,
                    diversity_weight=body.diversity_weight,
                )
                results.append({
                    "location": result["location"],
                    "latitude": result["lat"],
                    "longitude": result["lon"],
                    "demand_score": result["demand_score"],
                    "competition_score": result["competition_score"],
                    "accessibility_score": result["accessibility_score"],
                    "diversity_score": result["diversity_score"],
                    "viability_score": result["viability_score"],
                    "recommendation": result["recommendation"],
                    "explanation": result["explanation"],
                    "validation_warnings": result.get("warnings") or [],
                })
            except Exception as e:
                results.append({"location": location, "error": str(e)})

        good = sorted([r for r in results if "viability_score" in r],
                      key=lambda x: x["viability_score"], reverse=True)
        bad  = [r for r in results if "error" in r]

        return {"count": len(good), "results": good + bad}

    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Multi-location analysis failed: {e}"}


# ─────────────────────────────────────────────────────────────────────────────
# Outcome & rating tracking
# ─────────────────────────────────────────────────────────────────────────────

@app.patch("/analyses/{analysis_id}/outcome")
def patch_outcome(analysis_id: int, body: OutcomeRequest):
    """Update the real-world outcome of an analysis."""
    valid = {"Succeeded", "Failed", "Not Proceeded"}
    if body.status not in valid:
        raise HTTPException(status_code=422, detail=f"status must be one of {valid}")
    ok = update_outcome(analysis_id, body.status)
    if not ok:
        raise HTTPException(status_code=404, detail="Analysis not found")
    log_user_event("outcome_set", analysis_id, {"status": body.status})
    return {"ok": True, "analysis_id": analysis_id, "status": body.status}


@app.patch("/analyses/{analysis_id}/explanation-rating")
def patch_explanation_rating(analysis_id: int, body: ExplanationRatingRequest):
    """Store a thumbs-up (+1) or thumbs-down (-1) on the Gemini explanation."""
    if body.rating not in (1, -1):
        raise HTTPException(status_code=422, detail="rating must be 1 or -1")
    ok = update_explanation_rating(analysis_id, body.rating)
    if not ok:
        raise HTTPException(status_code=404, detail="Analysis not found")
    log_user_event("explanation_rated", analysis_id, {"rating": body.rating})
    return {"ok": True, "analysis_id": analysis_id, "rating": body.rating}


# ─────────────────────────────────────────────────────────────────────────────
# Event logging
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/log-event")
def log_event(body: LogEventRequest):
    """Generic event logger for frontend interactions."""
    log_user_event(body.event_type, body.analysis_id, body.metadata or {})
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# Analytics / KPIs
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/analytics/kpis", response_model=KPIResponse)
def analytics_kpis():
    """
    Compute platform KPIs from raw DB data.
    Never cached — always reads live data.
    """
    try:
        return get_kpi_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"KPI computation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PDF export  (Step 1 bug fix — no nested button, returns FileResponse)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/export-pdf/{analysis_id}")
def export_pdf(analysis_id: int):
    """
    Generate and return a PDF report for a stored analysis.
    Returns FileResponse with application/pdf media type.
    Frontend calls requests.get(url) and passes bytes to st.download_button.
    """
    record = get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    try:
        from app.report_generator import generate_pdf_report
        pdf_bytes = generate_pdf_report(
            location=record["location"],
            store_type=record["store_type"],
            radius_km=record["radius_km"],
            demand_score=record["demand_score"],
            competition_score=record["competition_score"],
            accessibility_score=record["accessibility_score"],
            diversity_score=record["diversity_score"],
            viability_score=record["viability_score"],
            recommendation=record["recommendation"],
            explanation=record.get("explanation", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    # Write to temp file — FastAPI FileResponse streams it, then OS cleans up
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(pdf_bytes)
    tmp.close()

    safe_name = record["location"].replace(" ", "_").replace(",", "")
    filename = f"SiteSense_{safe_name}.pdf"

    # Flag as exported
    try:
        mark_pdf_exported(analysis_id)
        log_user_event("pdf_exported", analysis_id, {"filename": filename})
    except Exception:
        pass

    return FileResponse(
        tmp.name,
        media_type="application/pdf",
        filename=filename,
        background=None,
    )


# ─────────────────────────────────────────────────────────────────────────────
# History helpers
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(limit: int = 20):
    """Return recent analysis history."""
    return {"analyses": get_recent_analyses(limit)}


# ─────────────────────────────────────────────────────────────────────────────
# Weight Presets
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/presets", response_model=WeightPresetList)
def get_presets():
    """Return all saved weight presets (built-in + user-saved)."""
    return WeightPresetList(presets=get_all_presets())


@app.post("/presets", response_model=WeightPreset, status_code=201)
def create_preset(body: CreatePresetRequest):
    """
    Save a named weight preset (upsert by name).
    Weights do not need to sum to 1.0 — the pipeline normalises them.
    Built-in preset names can be updated but not deleted.
    """
    saved = save_preset(
        body.name, body.demand, body.competition,
        body.accessibility, body.diversity,
    )
    return WeightPreset(**saved)


# ─────────────────────────────────────────────────────────────────────────────
# POI Images  (Unsplash — graceful degradation when key absent / rate-limited)
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/poi-images", response_model=POIImageList)
async def get_poi_images(
    location: str = Query(..., min_length=1, max_length=100),
    categories: str = Query(..., min_length=1, max_length=300),
):
    """
    Fetch up to 8 Unsplash photos for a location + POI category list.
    Returns an empty list (never raises) if the key is missing,
    the API is unreachable, or the rate-limit is hit.
    """
    key = config.UNSPLASH_ACCESS_KEY
    if not key:
        return POIImageList(images=[])

    category_list = [c.strip() for c in categories.split(",") if c.strip()]
    if not category_list:
        return POIImageList(images=[])

    images: List[POIImage] = []
    seen_ids: set = set()

    async with httpx.AsyncClient(timeout=8.0) as client:
        for category in category_list:
            if len(images) >= 8:
                break
            query = f"{category} {location}"
            try:
                resp = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={
                        "query": query,
                        "per_page": 3,
                        "orientation": "landscape",
                        "content_filter": "high",
                    },
                    headers={"Authorization": f"Client-ID {key}"},
                )
                if resp.status_code == 429:   # rate-limited — stop immediately
                    break
                if resp.status_code != 200:
                    continue
                payload = resp.json()
                for item in payload.get("results", []):
                    if len(images) >= 8:
                        break
                    photo_id = item.get("id", "")
                    if photo_id in seen_ids:
                        continue
                    seen_ids.add(photo_id)
                    urls = item.get("urls", {})
                    user = item.get("user", {})
                    url       = urls.get("small", "")
                    thumb_url = urls.get("thumb", "")
                    if not url:
                        continue
                    images.append(POIImage(
                        url=url,
                        thumb_url=thumb_url,
                        category=category,
                        photographer=user.get("name", ""),
                        photographer_url=user.get("links", {}).get("html", ""),
                    ))
            except Exception:
                continue   # never surface errors to caller

    return POIImageList(images=images)
