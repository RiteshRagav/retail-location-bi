"""
Score Validator: Validates score ranges and detects logical anomalies.

This module ensures score consistency and identifies suspicious patterns
that may indicate data quality issues or unusual market conditions.
"""

from typing import Dict, List, Any


def validate_scores(
    demand_score: float,
    competition_score: float,
    accessibility_score: float,
    diversity_score: float,
    viability_score: float
) -> Dict[str, Any]:
    """
    Validate and sanitize all scores, detecting logical inconsistencies.
    
    This function:
    1. Ensures all scores are within valid range [0, 100]
    2. Detects logical anomalies that suggest data quality issues
    3. Returns corrected scores and warnings for transparency
    
    Args:
        demand_score: Market demand score (target: 0-100)
        competition_score: Competition level score (target: 0-100)
        accessibility_score: Accessibility score (target: 0-100)
        diversity_score: Area diversity score (target: 0-100)
        viability_score: Final viability score (target: -100 to 100)
        
    Returns:
        Dictionary containing:
        {
            "validated_scores": {
                "demand_score": float,
                "competition_score": float,
                "accessibility_score": float,
                "diversity_score": float,
                "viability_score": float
            },
            "warnings": [str, ...],
            "clamped": bool (true if any score was adjusted)
        }
    """
    
    warnings: List[str] = []
    clamped = False
    
    # Clamp individual component scores to [0, 100]
    validated_demand = _clamp_score(demand_score, 0, 100)
    validated_competition = _clamp_score(competition_score, 0, 100)
    validated_accessibility = _clamp_score(accessibility_score, 0, 100)
    validated_diversity = _clamp_score(diversity_score, 0, 100)
    
    # Track if any clamping occurred
    if (validated_demand != demand_score or
        validated_competition != competition_score or
        validated_accessibility != accessibility_score or
        validated_diversity != diversity_score):
        clamped = True
    
    # Clamp viability score to [-100, 100]
    validated_viability = _clamp_score(viability_score, -100, 100)
    if validated_viability != viability_score:
        clamped = True
    
    # ========== ANOMALY DETECTION ==========
    
    # Anomaly 1: High demand but zero accessibility
    if validated_demand > 80 and validated_accessibility == 0:
        warnings.append(
            "High demand (>80) detected but zero accessibility. "
            "Market opportunity may be unreachable to customers."
        )
    
    # Anomaly 2: All scores are perfect (100)
    if (validated_demand == 100 and
        validated_competition == 100 and
        validated_accessibility == 100 and
        validated_diversity == 100):
        warnings.append(
            "All scores are 100 (perfect). This is statistically unrealistic. "
            "Data quality should be verified."
        )
    
    # Anomaly 3: Very high competition but high viability (logical mismatch)
    if validated_competition > 90 and validated_viability > 70:
        warnings.append(
            "Very high competition (>90) but high viability score (>70). "
            "This is contradictory. Market saturation typically reduces viability."
        )
    
    # Anomaly 4: Zero accessibility in high-demand areas (unrealistic)
    if validated_demand > 75 and validated_accessibility < 5:
        warnings.append(
            "High demand area with minimal accessibility (<5). "
            "Customers may struggle to reach this location by transit."
        )
    
    # Anomaly 5: Very low diversity despite high demand
    if validated_demand > 80 and validated_diversity < 20:
        warnings.append(
            "High demand (>80) but low area diversity (<20). "
            "Area may be mono-functional; diversification could improve viability."
        )
    
    # Anomaly 6: Perfect competition score (zero competitors)
    if validated_competition == 0:
        warnings.append(
            "Competition score is 0 (no competitors detected). "
            "This may indicate data collection issues or a truly unserved market."
        )
    
    # Anomaly 7: Negative viability despite good individual scores
    if (validated_demand > 60 and
        validated_accessibility > 60 and
        validated_diversity > 50 and
        validated_viability < 0):
        warnings.append(
            "Good individual scores but negative viability. "
            "High competition is likely the limiting factor."
        )
    
    # Add clamping warning if values were adjusted
    if clamped:
        warnings.insert(
            0,
            "Score clamping applied: One or more scores were adjusted to valid range."
        )
    
    return {
        "validated_scores": {
            "demand_score": round(validated_demand, 2),
            "competition_score": round(validated_competition, 2),
            "accessibility_score": round(validated_accessibility, 2),
            "diversity_score": round(validated_diversity, 2),
            "viability_score": round(validated_viability, 2)
        },
        "warnings": warnings,
        "clamped": clamped
    }


def _clamp_score(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a score to the specified range.
    
    Args:
        value: Score to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped score value
    """
    return max(min_val, min(max_val, value))
