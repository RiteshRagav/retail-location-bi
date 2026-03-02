"""
Explanation Agent: Generates human-readable explanations using Google Gemini.

This agent leverages a Large Language Model to synthesize quantitative scores
into an executive-style narrative explaining location viability.
"""

import os
import requests
import json


def generate_explanation(
    location: str,
    demand_score: float,
    competition_score: float,
    accessibility_score: float,
    diversity_score: float,
    viability_score: float,
    recommendation: str
) -> str:
    """
    Generate an AI-powered explanation of retail location viability using Gemini.
    
    Args:
        location: Name of the location being analyzed
        demand_score: Market demand score (0-100)
        competition_score: Competitive pressure score (0-100)
        accessibility_score: Public transport accessibility score (0-100)
        diversity_score: Area diversity score (0-100)
        viability_score: Final viability score (-100 to 100)
        recommendation: Recommendation classification (e.g., "Strongly Recommended")
        
    Returns:
        Executive-style explanation text (max 120 words) or fallback message
    """
    
    # Retrieve API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        # Graceful fallback if API key is not configured
        return f"Automated explanation currently unavailable. Scores indicate {recommendation}."
    
    # Identify strongest and weakest factors
    scores = {
        "demand": demand_score,
        "competition": competition_score,
        "accessibility": accessibility_score,
        "diversity": diversity_score
    }
    
    strongest_factor = max(scores, key=scores.get)
    weakest_factor = min(scores, key=scores.get)
    
    # Construct prompt for Gemini
    prompt = f"""Analyze this retail location viability assessment and provide a 120-word executive summary:

Location: {location}
- Market Demand (POI density): {demand_score:.1f}/100
- Competition Level: {competition_score:.1f}/100
- Accessibility (transit): {accessibility_score:.1f}/100
- Area Diversity: {diversity_score:.1f}/100
- Overall Viability Score: {viability_score:.1f}
- Recommendation: {recommendation}

Strongest factor: {strongest_factor.replace('_', ' ').title()} ({scores[strongest_factor]:.1f})
Weakest factor: {weakest_factor.replace('_', ' ').title()} ({scores[weakest_factor]:.1f})

Provide a concise executive summary explaining:
1. The strongest positive indicator
2. The primary risk or constraint
3. Why the recommendation is justified

Keep it under 120 words. Use professional, direct tone. No introductions or sign-offs."""

    try:
        # Call Gemini API via REST
        gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 256,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        # Include API key as query parameter
        response = requests.post(
            gemini_endpoint,
            headers=headers,
            json=payload,
            params={"key": api_key},
            timeout=10
        )
        
        # Handle API response
        if response.status_code == 200:
            data = response.json()
            
            # Extract generated text from Gemini response
            if "candidates" in data and len(data["candidates"]) > 0:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    explanation = candidate["content"]["parts"][0].get("text", "").strip()
                    return explanation if explanation else _fallback_explanation(recommendation)
        
        # If API returns error, log and fallback
        return _fallback_explanation(recommendation)
    
    except requests.exceptions.Timeout:
        # Handle timeout gracefully
        return _fallback_explanation(recommendation)
    except requests.exceptions.RequestException:
        # Handle network errors gracefully
        return _fallback_explanation(recommendation)
    except (KeyError, IndexError, json.JSONDecodeError):
        # Handle malformed API responses gracefully
        return _fallback_explanation(recommendation)


def _fallback_explanation(recommendation: str) -> str:
    """
    Provide a fallback explanation when Gemini API is unavailable.
    
    Args:
        recommendation: The viability recommendation
        
    Returns:
        Fallback explanation text
    """
    return f"Automated explanation currently unavailable. Scores indicate {recommendation}."
