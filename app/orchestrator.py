"""
LangGraph Orchestrator: State-based workflow for multi-agent retail analysis.

This module defines a StateGraph that coordinates agents in a deterministic sequence.
Each node represents an agent or processing step, maintaining a shared state throughout execution.
"""

import time
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from app.data_fetch import fetch_pois
from app.agents import (
    demand_agent,
    competition_agent,
    accessibility_agent,
    diversity_agent
)
from app.explanation_agent import generate_explanation
from app.decision import make_decision
from app.score_validator import validate_scores
from app.agent_logger import log_agent_execution
from geopy.geocoders import Nominatim


# ========== STATE DEFINITION ==========

class RetailAnalysisState(TypedDict):
    """
    State object that flows through the LangGraph workflow.
    Each node reads and updates relevant fields.
    """
    # Input parameters
    location: str
    store_type: str
    radius_km: int
    
    # Custom weights for decision node
    demand_weight: float
    competition_weight: float
    accessibility_weight: float
    diversity_weight: float
    
    # Geocoding results
    lat: float
    lon: float
    
    # Data extraction
    total_pois: int
    competitors: int
    transport_nodes: int
    diversity_raw: int
    
    # POI coordinate lists for mapping
    competitors_list: list  # [{lat: float, lon: float}, ...]
    transport_nodes_list: list  # [{lat: float, lon: float}, ...]
    
    # Agent outputs
    demand_score: float
    competition_score: float
    accessibility_score: float
    diversity_score: float
    
    # Decision outputs
    viability_score: float
    recommendation: str
    explanation: str
    
    # Validation
    warnings: list


# ========== GRAPH NODES ==========

def data_extraction_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Data Extraction Node: Geocode location and fetch POI data.
    
    Inputs: location, store_type, radius_km
    Outputs: lat, lon, total_pois, competitors, transport_nodes, diversity_raw,
             competitors_list, transport_nodes_list
    """
    # Geocode location with timeout
    geolocator = Nominatim(user_agent="retail-bi-app", timeout=20)
    loc = geolocator.geocode(state["location"])
    
    if not loc:
        raise ValueError(f"Location not found: {state['location']}")
    
    # Fetch POI data
    pois = fetch_pois(loc.latitude, loc.longitude, state["radius_km"] * 1000)
    
    # Extract metrics and coordinate lists
    total_pois = len(pois)
    competitors_list = []
    transport_nodes_list = []
    
    for p in pois:
        # Check if this POI is a competitor
        if state["store_type"] in str(p.get("tags", {})).lower():
            if "lat" in p and "lon" in p:
                competitors_list.append({"lat": p["lat"], "lon": p["lon"]})
        
        # Check if this POI is a transport node
        # Multi-tag detection: bus stops, stations (railway/tram/subway), platforms, aerodromes
        tags_str = str(p.get("tags", {})).lower()
        transport_tags = [
            "bus_stop", "bus_station",
            "railway", "station",
            "tram_stop", "subway",
            "public_transport", "aerodrome"
        ]
        if any(tag in tags_str for tag in transport_tags):
            if "lat" in p and "lon" in p:
                transport_nodes_list.append({"lat": p["lat"], "lon": p["lon"]})
    
    competitors = len(competitors_list)
    transport_nodes = len(transport_nodes_list)
    diversity_raw = len(set(str(p.get("tags", {})) for p in pois))
    
    return {
        **state,
        "lat": loc.latitude,
        "lon": loc.longitude,
        "total_pois": total_pois,
        "competitors": competitors,
        "transport_nodes": transport_nodes,
        "diversity_raw": diversity_raw,
        "competitors_list": competitors_list,
        "transport_nodes_list": transport_nodes_list
    }


def demand_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Demand Agent Node: Evaluate market demand based on POI density.
    
    Inputs: total_pois
    Outputs: demand_score
    """
    start_time = time.time()
    demand_score = demand_agent(state["total_pois"])
    execution_time = (time.time() - start_time) * 1000
    
    log_agent_execution(
        agent_name="demand_agent",
        inputs={"total_pois": state["total_pois"]},
        outputs=demand_score,
        execution_time_ms=execution_time
    )
    
    return {**state, "demand_score": demand_score}


def competition_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Competition Agent Node: Assess competitive pressure.
    
    Inputs: competitors
    Outputs: competition_score
    """
    start_time = time.time()
    competition_score = competition_agent(state["competitors"])
    execution_time = (time.time() - start_time) * 1000
    
    log_agent_execution(
        agent_name="competition_agent",
        inputs={"competitors": state["competitors"]},
        outputs=competition_score,
        execution_time_ms=execution_time
    )
    
    return {**state, "competition_score": competition_score}


def accessibility_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Accessibility Agent Node: Measure public transport accessibility.
    
    Inputs: transport_nodes, total_pois
    Outputs: accessibility_score
    """
    start_time = time.time()
    # Pass both transport_nodes and total_pois for road proximity heuristic
    accessibility_score = accessibility_agent(
        state["transport_nodes"],
        total_pois=state["total_pois"]
    )
    execution_time = (time.time() - start_time) * 1000
    
    log_agent_execution(
        agent_name="accessibility_agent",
        inputs={"transport_nodes": state["transport_nodes"]},
        outputs=accessibility_score,
        execution_time_ms=execution_time
    )
    
    return {**state, "accessibility_score": accessibility_score}


def diversity_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Diversity Agent Node: Evaluate area economic diversity.
    
    Inputs: diversity_raw
    Outputs: diversity_score
    """
    start_time = time.time()
    diversity_score = diversity_agent(state["diversity_raw"])
    execution_time = (time.time() - start_time) * 1000
    
    log_agent_execution(
        agent_name="diversity_agent",
        inputs={"diversity_raw": state["diversity_raw"]},
        outputs=diversity_score,
        execution_time_ms=execution_time
    )
    
    return {**state, "diversity_score": diversity_score}


def validation_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Validation Node: Validate scores and detect anomalies.
    
    Inputs: All component scores
    Outputs: warnings (warnings list)
    
    Note: Validated scores are returned but don't override originals
    for logging clarity. Decision node uses these validated values.
    """
    validation_result = validate_scores(
        demand_score=state["demand_score"],
        competition_score=state["competition_score"],
        accessibility_score=state["accessibility_score"],
        diversity_score=state["diversity_score"],
        viability_score=0  # Placeholder
    )
    
    # Extract validated scores
    validated = validation_result["validated_scores"]
    warnings = validation_result["warnings"]
    
    return {
        **state,
        "demand_score": validated["demand_score"],
        "competition_score": validated["competition_score"],
        "accessibility_score": validated["accessibility_score"],
        "diversity_score": validated["diversity_score"],
        "warnings": warnings
    }


def decision_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Decision Node: Compute final viability score and recommendation.
    
    Inputs: All validated component scores + custom weights
    Outputs: viability_score, recommendation
    """
    decision = make_decision(
        demand=state["demand_score"],
        competition=state["competition_score"],
        accessibility=state["accessibility_score"],
        diversity=state["diversity_score"],
        demand_weight=state["demand_weight"],
        competition_weight=state["competition_weight"],
        accessibility_weight=state["accessibility_weight"],
        diversity_weight=state["diversity_weight"]
    )
    
    return {
        **state,
        "viability_score": decision["viability_score"],
        "recommendation": decision["recommendation"]
    }


def explanation_node(state: RetailAnalysisState) -> RetailAnalysisState:
    """
    Explanation Agent Node: Generate AI-powered explanation using Gemini.
    
    Inputs: All scores and decision
    Outputs: explanation
    """
    start_time = time.time()
    explanation = generate_explanation(
        location=state["location"],
        demand_score=state["demand_score"],
        competition_score=state["competition_score"],
        accessibility_score=state["accessibility_score"],
        diversity_score=state["diversity_score"],
        viability_score=state["viability_score"],
        recommendation=state["recommendation"]
    )
    execution_time = (time.time() - start_time) * 1000
    
    log_agent_execution(
        agent_name="explanation_agent",
        inputs={
            "location": state["location"],
            "demand_score": state["demand_score"],
            "competition_score": state["competition_score"],
            "accessibility_score": state["accessibility_score"],
            "diversity_score": state["diversity_score"],
            "viability_score": state["viability_score"],
            "recommendation": state["recommendation"]
        },
        outputs=explanation,
        execution_time_ms=execution_time
    )
    
    return {**state, "explanation": explanation}


# ========== GRAPH BUILDER ==========

def build_workflow():
    """
    Build and compile the LangGraph StateGraph workflow.
    
    Returns:
        Compiled graph ready for execution
    """
    workflow = StateGraph(RetailAnalysisState)
    
    # Add nodes
    workflow.add_node("data_extraction", data_extraction_node)
    workflow.add_node("demand", demand_node)
    workflow.add_node("competition", competition_node)
    workflow.add_node("accessibility", accessibility_node)
    workflow.add_node("diversity", diversity_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("decision", decision_node)
    workflow.add_node("explanation", explanation_node)
    
    # Define edges (sequential deterministic flow)
    workflow.add_edge(START, "data_extraction")
    workflow.add_edge("data_extraction", "demand")
    workflow.add_edge("demand", "competition")
    workflow.add_edge("competition", "accessibility")
    workflow.add_edge("accessibility", "diversity")
    workflow.add_edge("diversity", "validation")
    workflow.add_edge("validation", "decision")
    workflow.add_edge("decision", "explanation")
    workflow.add_edge("explanation", END)
    
    return workflow.compile()


# ========== ORCHESTRATOR INTERFACE ==========

# Build graph at module load time
_graph = build_workflow()


def run_analysis(
    location: str,
    store_type: str = "cafe",
    radius_km: int = 1,
    demand_weight: float = 0.25,
    competition_weight: float = 0.25,
    accessibility_weight: float = 0.25,
    diversity_weight: float = 0.25
) -> RetailAnalysisState:
    """
    Execute the retail location analysis workflow with custom weighting.
    
    Multi-agent LangGraph pipeline with 8 nodes:
    1. data_extraction_node → Geocode + fetch POIs
    2. demand_node → Evaluate market demand
    3. competition_node → Assess competitors
    4. accessibility_node → Transport + density accessibility
    5. diversity_node → Area diversity assessment
    6. validation_node → Score anomaly detection
    7. decision_node → Weighted viability computation
    8. explanation_node → AI-powered explanation
    
    Args:
        location: Location name to analyze
        store_type: Type of store (default: "cafe")
        radius_km: Search radius in kilometers (default: 1)
        demand_weight: Weight for demand metric (default: 0.25)
        competition_weight: Weight for competition metric (default: 0.25)
        accessibility_weight: Weight for accessibility metric (default: 0.25)
        diversity_weight: Weight for diversity metric (default: 0.25)
        
    Returns:
        Final state dict with all analysis results
    """
    initial_state = {
        "location": location,
        "store_type": store_type,
        "radius_km": radius_km,
        "demand_weight": demand_weight,
        "competition_weight": competition_weight,
        "accessibility_weight": accessibility_weight,
        "diversity_weight": diversity_weight,
        "lat": 0.0,
        "lon": 0.0,
        "total_pois": 0,
        "competitors": 0,
        "transport_nodes": 0,
        "diversity_raw": 0,
        "competitors_list": [],
        "transport_nodes_list": [],
        "demand_score": 0.0,
        "competition_score": 0.0,
        "accessibility_score": 0.0,
        "diversity_score": 0.0,
        "viability_score": 0.0,
        "recommendation": "",
        "explanation": "",
        "warnings": []
    }
    
    return _graph.invoke(initial_state)
