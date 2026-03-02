"""
Multi-agent module for retail location analysis.

Each agent specializes in evaluating a specific dimension of location viability.
Agents are independent, composable, and contain no API or framework logic.
"""

from app.scoring import normalize


def demand_agent(total_pois: int) -> float:
    """
    Demand Agent: Evaluates market demand based on POI density.
    
    Higher POI count indicates more business activity and foot traffic.
    
    Args:
        total_pois: Total number of points of interest in the radius
        
    Returns:
        Normalized score (0-100) representing market demand
    """
    return normalize(total_pois, 200)


def competition_agent(competitors: int) -> float:
    """
    Competition Agent: Evaluates competitive pressure.
    
    Fewer competitors means lower market saturation and better viability.
    This metric is inversely weighted in the final score.
    
    Args:
        competitors: Number of competing stores in the radius
        
    Returns:
        Normalized score (0-100) representing competition level
    """
    return normalize(competitors, 50)


def accessibility_agent(transport_nodes: int, total_pois: int = 0, boost: bool = False) -> float:
    """
    Accessibility Agent: Evaluates location accessibility via transport infrastructure.
    
    Enhanced Logic:
    - Weighted formula: 0.6 × transport_score + 0.4 × activity_density_score
    - Transport score: normalized from transport nodes (max 30 in 1km urban radius)
    - Activity density: POI count as proxy for foot traffic (max 200 POIs)
    - Road proximity: +5 boost if >50 POIs (indicates better street connectivity)
    
    Rationale:
    - Customers reach stores via public transport (buses, trams, trains, metro)
    - High POI density indicates multi-use urban areas with better street networks
    - Urban areas with >50 POIs have demonstrated accessibility via road connectivity
    
    Args:
        transport_nodes: Count of detected transport infrastructure points
        total_pois: Total POI count (proxy for commercial activity density)
        boost: Manual override for high-density boost
        
    Returns:
        Normalized score (0-100) representing overall accessibility
    """
    # Transport accessibility component (normalized to 0-100)
    transport_score = normalize(transport_nodes, 30)
    
    # Activity density component: POI density as foot traffic proxy (normalized to 0-100)
    activity_density_score = normalize(total_pois, 200)
    
    # Weighted combination: 60% transport, 40% activity density
    score = (0.6 * transport_score) + (0.4 * activity_density_score)
    
    # Road proximity heuristic: high POI density indicates better street connectivity
    if boost or (total_pois > 50):
        score = min(100, score + 5)
    
    return score


def diversity_agent(diversity_raw: int) -> float:
    """
    Diversity Agent: Evaluates area diversity and mixed-use characteristics.
    
    Higher diversity indicates a multi-functional area with various amenities,
    suggesting economic vitality and customer base heterogeneity.
    
    Args:
        diversity_raw: Count of unique POI categories in the area
        
    Returns:
        Normalized score (0-100) representing area diversity
    """
    return normalize(diversity_raw, 100)
