from app.scoring import classify


def make_decision(
    demand: float,
    competition: float,
    accessibility: float,
    diversity: float,
    demand_weight: float = 0.25,
    competition_weight: float = 0.25,
    accessibility_weight: float = 0.25,
    diversity_weight: float = 0.25
) -> dict:
    """
    Make a viability decision based on weighted scores.
    
    Allows custom weighting of factors for client-specific strategies:
    - Demand-focused: high demand weight for growth markets
    - Competition-conscious: low competition weight for saturated areas
    - Accessibility-focused: high accessibility weight for transit-dependent areas
    - Diversity-focused: high diversity weight for multi-use neighborhoods
    
    Args:
        demand: Demand score (0-100)
        competition: Competition score (0-100)
        accessibility: Accessibility score (0-100)
        diversity: Diversity score (0-100)
        demand_weight: Weight for demand (default 0.25)
        competition_weight: Weight for competition (default 0.25)
        accessibility_weight: Weight for accessibility (default 0.25)
        diversity_weight: Weight for diversity (default 0.25)
        
    Returns:
        dict with viability_score and recommendation
    """
    # Validate weights sum to 1.0 (allow small floating point error)
    total_weight = demand_weight + competition_weight + accessibility_weight + diversity_weight
    
    if abs(total_weight - 1.0) > 0.001:
        # Normalize weights if they don't sum to 1
        demand_weight /= total_weight
        competition_weight /= total_weight
        accessibility_weight /= total_weight
        diversity_weight /= total_weight
    
    # Weighted viability score
    # Note: Competition is inversely weighted (lower is better)
    viability_score = (
        (demand_weight * demand) +
        (competition_weight * (100 - competition)) +  # Inverse scoring
        (accessibility_weight * accessibility) +
        (diversity_weight * diversity)
    ) / (demand_weight + competition_weight + accessibility_weight + diversity_weight)
    
    recommendation = classify(viability_score)
    
    return {
        "viability_score": viability_score,
        "recommendation": recommendation,
        "weights": {
            "demand": demand_weight,
            "competition": competition_weight,
            "accessibility": accessibility_weight,
            "diversity": diversity_weight
        }
    }
