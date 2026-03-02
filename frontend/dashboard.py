"""
Professional SiteSense AI Dashboard - Client-Ready Streamlit Application

Features:
- Single & multi-location analysis (up to 3 locations)
- Custom weight adjustment with dynamic scoring
- Side-by-side location comparison
- Professional color-coded metrics
- Interactive map with layer toggles
- PDF report generation
- Analysis history & reload
- Comprehensive tooltips & explanations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import app module
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import requests
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import math
from datetime import datetime
import base64
from io import BytesIO

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="SiteSense AI - Retail Location Intelligence",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== API CONFIGURATION ==========
API_URL = "http://127.0.0.1:8000"

# ========== CUSTOM STYLING ==========
st.markdown("""<style>
.metric-card { padding: 15px; border-radius: 8px; margin: 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.strong { background-color: #d4edda; border-left: 4px solid #27ae60; }
.moderate { background-color: #fff3cd; border-left: 4px solid #f39c12; }
.risky { background-color: #f8d7da; border-left: 4px solid #e74c3c; }
</style>""", unsafe_allow_html=True)

# ========== HEADER ==========
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🗺️ SiteSense AI")
    st.markdown("**Professional Retail Location Intelligence - v2.0**")

# ========== NAVIGATION TABS ==========
tab1, tab2, tab3, tab4 = st.tabs(["📍 Analyze", "🔄 Compare", "⚙️ Guide", "📊 History"])

# ========== SESSION STATE ==========
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "comparison_results" not in st.session_state:
    st.session_state.comparison_results = None

def get_score_color(score):
    return "strong" if score > 60 else ("moderate" if score > 40 else "risky")

def get_emoji(score):
    return "✅" if score > 60 else ("⚠️" if score > 40 else "❌")

# ========== TAB 1: SINGLE LOCATION ==========
with tab1:
    st.markdown("### 📍 Analyze a Single Location")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        location = st.text_input("Location", "Paris")
    with col2:
        store_type = st.selectbox("Store Type", ["cafe", "pharmacy", "clothing", "supermarket", "restaurant"])
    with col3:
        radius_km = st.slider("Radius (km)", 1, 5, 1)
    
    st.markdown("**Custom Weight Strategy** (all default 0.25 = balanced)")
    w_col1, w_col2, w_col3, w_col4 = st.columns(4)
    with w_col1:
        demand_w = st.slider("Demand", 0.0, 1.0, 0.25, 0.05)
    with w_col2:
        comp_w = st.slider("Competition", 0.0, 1.0, 0.25, 0.05)
    with w_col3:
        access_w = st.slider("Accessibility", 0.0, 1.0, 0.25, 0.05)
    with w_col4:
        div_w = st.slider("Diversity", 0.0, 1.0, 0.25, 0.05)
    
    # Normalize weights
    total = demand_w + comp_w + access_w + div_w
    if total > 0:
        demand_w, comp_w, access_w, div_w = demand_w/total, comp_w/total, access_w/total, div_w/total
    
    if st.button("🔍 Analyze", key="single", type="primary", use_container_width=True):
        with st.spinner("⏳ Analyzing..."):
            try:
                response = requests.get(
                    f"{API_URL}/analyze",
                    params={
                        "location": location,
                        "store_type": store_type,
                        "radius_km": radius_km,
                        "demand_weight": demand_w,
                        "competition_weight": comp_w,
                        "accessibility_weight": access_w,
                        "diversity_weight": div_w,
                        "save_to_history": True
                    },
                    timeout=130
                )
                data = response.json()
                if "error" not in data:
                    st.session_state.analysis_result = data
                    st.rerun()
                else:
                    st.error(f"Error: {data['error']}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    
    # ========== DISPLAY RESULTS ==========
    if st.session_state.analysis_result:
        data = st.session_state.analysis_result
        st.markdown("---")
        
        # Viability Banner
        vib = data["viability_score"]
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""<div class="metric-card {get_score_color(vib)}">
            <h2>{get_emoji(vib)} Viability: {vib:.1f}/100</h2>
            <p><strong>{data['recommendation']}</strong></p></div>""", unsafe_allow_html=True)
        
        # 4 Metrics
        st.markdown("#### 📊 Score Breakdown")
        m1, m2, m3, m4 = st.columns(4)
        metrics = [
            ("🎯 Demand", data["demand_score"]),
            ("⚔️ Competition", data["competition_score"]),
            ("🚌 Accessibility", data["accessibility_score"]),
            ("🏙️ Diversity", data["diversity_score"])
        ]
        for col, (label, score) in zip([m1, m2, m3, m4], metrics):
            with col:
                st.markdown(f"""<div class="metric-card {get_score_color(score)}">
                <p style="margin:0;color:#666;font-size:12px;">{label}</p>
                <h3 style="margin:5px 0;font-size:28px;">{score:.1f}</h3></div>""", unsafe_allow_html=True)
        
        # Radar Chart
        st.markdown("#### 📈 Score Profile")
        categories = ["Demand", "Competition", "Accessibility", "Diversity"]
        values = [data["demand_score"], data["competition_score"], data["accessibility_score"], data["diversity_score"]]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories, fill='toself',
            fillcolor='rgba(31, 119, 210, 0.3)', line=dict(color='#1f77d2', width=2)
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False, height=400
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Map
        st.markdown("#### 📍 Location Map")
        if "latitude" in data and "longitude" in data:
            lat, lon = data["latitude"], data["longitude"]
            m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
            
            folium.Marker([lat, lon], popup="🎯 Target", icon=folium.Icon(color="red", icon="map-pin")).add_to(m)
            folium.Circle([lat, lon], radius=radius_km*1000, color="blue", fill=True, fillOpacity=0.1).add_to(m)
            
            for c in data.get("competitors_list", []):
                if "lat" in c and "lon" in c:
                    folium.Marker([c["lat"], c["lon"]], popup="Competitor", icon=folium.Icon(color="blue", icon="shopping-cart")).add_to(m)
            
            for t in data.get("transport_nodes_list", []):
                if "lat" in t and "lon" in t:
                    folium.Marker([t["lat"], t["lon"]], popup="Transport", icon=folium.Icon(color="green", icon="bus")).add_to(m)
            
            st_folium(m, width=None, height=400)
        
        # Explanation
        st.markdown("#### 💬 Analysis Summary")
        st.info(data["explanation"])
        
        # Warnings
        if data.get("validation_warnings"):
            st.markdown("#### ⚠️ System Insights")
            for w in data["validation_warnings"]:
                st.warning(w)
        
        # PDF Export
        if st.button("📄 Download PDF Report", use_container_width=True):
            try:
                from app.report_generator import generate_pdf_report
                pdf = generate_pdf_report(
                    location=data["location"], store_type=store_type, radius_km=radius_km,
                    demand_score=data["demand_score"], competition_score=data["competition_score"],
                    accessibility_score=data["accessibility_score"], diversity_score=data["diversity_score"],
                    viability_score=data["viability_score"], recommendation=data["recommendation"],
                    explanation=data["explanation"]
                )
                st.download_button("💾 Download", pdf,
                    f"Report_{data['location'].replace(' ','_')}.pdf", "application/pdf")
            except Exception as e:
                st.error(f"PDF error: {str(e)}")

# ========== TAB 2: MULTI-LOCATION COMPARISON ==========
with tab2:
    st.markdown("### 🔄 Compare Up to 3 Locations")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        loc1 = st.text_input("Location 1", "Paris")
    with col2:
        loc2 = st.text_input("Location 2", "")
    with col3:
        loc3 = st.text_input("Location 3", "")
    
    locations = [l for l in [loc1, loc2, loc3] if l]
    store_comp = st.selectbox("Store Type", ["cafe", "pharmacy", "clothing", "supermarket", "restaurant"], key="comp")
    radius_comp = st.slider("Radius (km)", 1, 5, 1, key="comp_radius")
    
    if st.button("🔄 Compare", type="primary", use_container_width=True):
        if locations:
            with st.spinner(f"Comparing {len(locations)} locations..."):
                try:
                    response = requests.post(
                        f"{API_URL}/analyze-multiple",
                        json={"locations": locations, "store_type": store_comp, "radius_km": radius_comp},
                        timeout=300
                    )
                    result = response.json()
                    if "error" not in result:
                        st.session_state.comparison_results = result
                        st.rerun()
                    else:
                        st.error(f"Error: {result['error']}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    if st.session_state.comparison_results:
        comp = st.session_state.comparison_results
        if comp.get("results"):
            results = [r for r in comp["results"] if "viability_score" in r]
            if results:
                st.markdown("#### 🏆 Ranked Results")
                for idx, r in enumerate(results, 1):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**#{idx}. {r['location']}**")
                    with col2:
                        st.write(f"{get_emoji(r['viability_score'])} {r['viability_score']:.1f}")
                    with col3:
                        st.caption(r['recommendation'])

# ========== TAB 3: GUIDE ==========
with tab3:
    st.markdown("### ⚙️ Metric Explanations")
    
    e1, e2 = st.columns(2)
    with e1:
        with st.expander("🎯 Demand"):
            st.write("Market demand from POI density. Higher = more activity & customers. Max: 200 POIs.")
        with st.expander("🚌 Accessibility"):
            st.write("Transport + foot traffic. 60% transport nodes, 40% POI density. Essential for accessibility.")
    with e2:
        with st.expander("⚔️ Competition"):
            st.write("Competitors in radius. Lower is better (less saturation). Max: 50 competitors.")
        with st.expander("🏙️ Diversity"):
            st.write("Area economic diversity & mixed-use characteristics. More = vitality.")
    
    st.markdown("#### Viability Formula")
    st.code("Viability = avg(demand, 100-competition, accessibility, diversity)")
    st.markdown("Adjust weights for custom strategies: growth (high demand), risk-averse (low competition), etc.")

# ========== TAB 4: HISTORY ==========
with tab4:
    st.markdown("### 📊 Analysis History")
    try:
        from app.database import get_recent_analyses
        recent = get_recent_analyses(10)
        if recent:
            for a in recent:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"📍 {a['location']} | {a['store_type']}")
                    st.caption(a['timestamp'])
                with col2:
                    st.write(f"{get_emoji(a['viability_score'])} {a['viability_score']:.1f}")
                with col3:
                    if st.button("View", key=f"h_{a['id']}"):
                        st.session_state.analysis_result = {
                            "location": a['location'], "latitude": a['coordinates']['lat'] if a['coordinates'] else 0,
                            "longitude": a['coordinates']['lon'] if a['coordinates'] else 0,
                            "demand_score": a['demand_score'], "competition_score": a['competition_score'],
                            "accessibility_score": a['accessibility_score'], "diversity_score": a['diversity_score'],
                            "viability_score": a['viability_score'], "recommendation": a['recommendation'],
                            "explanation": a['explanation'], "validation_warnings": a['validation_warnings'] or [],
                            "competitors_list": [], "transport_nodes_list": []
                        }
                        st.rerun()
        else:
            st.info("No history yet")
    except Exception as e:
        st.info(f"History unavailable: {str(e)}")

# ========== FOOTER ==========
st.markdown("---")
st.markdown("<div style='text-align:center;color:#999;font-size:11px;'>SiteSense AI v2.0 | Multi-Agent Retail Location Intelligence | © 2025</div>", unsafe_allow_html=True)
