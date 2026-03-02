from fastapi import FastAPI, HTTPException
from typing import List
from app.orchestrator import run_analysis
from app.database import store_analysis

app = FastAPI(
    title="SiteSense AI",
    description="Multi-Agent Retail Location Intelligence API",
    version="2.0"
)


@app.get("/analyze")
def analyze(
    location: str,
    store_type: str = "cafe",
    radius_km: int = 1,
    demand_weight: float = 0.25,
    competition_weight: float = 0.25,
    accessibility_weight: float = 0.25,
    diversity_weight: float = 0.25,
    save_to_history: bool = True
):
    """
    Analyze a single retail location with custom weights.
    
    LangGraph-orchestrated multi-agent pipeline:
    1. Data Extraction → Geocode and fetch POI data
    2. Demand Agent → Evaluate market demand
    3. Competition Agent → Assess competitive pressure
    4. Accessibility Agent → Transport & activity density
    5. Diversity Agent → Economic diversity assessment
    6. Validation Node → Anomaly detection
    7. Decision Node → Weighted viability score
    8. Explanation Agent → AI-powered summary
    
    Args:
        location: City, district, or full address
        store_type: cafe, pharmacy, clothing, supermarket, restaurant
        radius_km: Search radius in kilometers (1-5)
        demand_weight: Weight for demand metric (0-1)
        competition_weight: Weight for competition metric (0-1)
        accessibility_weight: Weight for accessibility metric (0-1)
        diversity_weight: Weight for diversity metric (0-1)
        save_to_history: Store result in analysis history database
        
    Returns:
        Complete analysis with scores, explanation, and visualizations
    """
    try:
        # Validate radius
        if radius_km < 1 or radius_km > 5:
            raise HTTPException(status_code=400, detail="Radius must be between 1-5 km")
        
        # Validate weights sum to 1
        total_weight = demand_weight + competition_weight + accessibility_weight + diversity_weight
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(status_code=400, detail="Weights must sum to 1.0")
        
        # Execute orchestrated analysis
        result = run_analysis(
            location=location,
            store_type=store_type,
            radius_km=radius_km,
            demand_weight=demand_weight,
            competition_weight=competition_weight,
            accessibility_weight=accessibility_weight,
            diversity_weight=diversity_weight
        )
        
        # Format response
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
            "validation_warnings": result["warnings"] if result["warnings"] else [],
            "competitors_list": result["competitors_list"],
            "transport_nodes_list": result["transport_nodes_list"],
            "weights": {
                "demand": demand_weight,
                "competition": competition_weight,
                "accessibility": accessibility_weight,
                "diversity": diversity_weight
            }
        }
        
        # Store in history if requested
        if save_to_history:
            try:
                store_analysis(
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
                    validation_warnings=result["warnings"]
                )
            except Exception as e:
                # Log error but don't fail the response
                print(f"Warning: Could not save to history: {str(e)}")
        
        return response
    
    except HTTPException:
        raise
    except ValueError as e:
        return {"error": f"Location not found: {str(e)}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


@app.post("/analyze-multiple")
def analyze_multiple(
    locations: List[str],
    store_type: str = "cafe",
    radius_km: int = 1,
    demand_weight: float = 0.25,
    competition_weight: float = 0.25,
    accessibility_weight: float = 0.25,
    diversity_weight: float = 0.25
):
    """
    Analyze multiple locations (up to 3) and return ranked results.
    
    Useful for comparative site selection and market evaluation.
    Results are sorted by viability score (highest first).
    
    Args:
        locations: List of 1-3 location names/addresses
        store_type: Type of retail store
        radius_km: Search radius in kilometers
        demand_weight: Custom weight for demand
        competition_weight: Custom weight for competition
        accessibility_weight: Custom weight for accessibility
        diversity_weight: Custom weight for diversity
        
    Returns:
        List of analyses sorted by viability score (descending)
    """
    try:
        # Validate location count
        if len(locations) < 1 or len(locations) > 3:
            raise HTTPException(status_code=400, detail="Must analyze 1-3 locations")
        
        results = []
        
        for location in locations:
            try:
                result = run_analysis(
                    location=location,
                    store_type=store_type,
                    radius_km=radius_km,
                    demand_weight=demand_weight,
                    competition_weight=competition_weight,
                    accessibility_weight=accessibility_weight,
                    diversity_weight=diversity_weight
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
                    "validation_warnings": result["warnings"] if result["warnings"] else []
                })
            except Exception as e:
                results.append({
                    "location": location,
                    "error": str(e)
                })
        
        # Sort by viability score (descending)
        results_with_scores = [r for r in results if "viability_score" in r]
        results_with_errors = [r for r in results if "error" in r]
        
        sorted_results = sorted(
            results_with_scores,
            key=lambda x: x["viability_score"],
            reverse=True
        )
        
        return {
            "count": len(sorted_results),
            "results": sorted_results + results_with_errors
        }
    
    except HTTPException:
        raise
    except Exception as e:
        return {"error": f"Multi-location analysis failed: {str(e)}"}
        return {"error": str(e)}
    except Exception as e:
        # Handle unexpected errors
        return {"error": f"Analysis failed: {str(e)}"}
