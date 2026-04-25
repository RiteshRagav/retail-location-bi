"""
SiteSense AI v3.0 — Nike Dark Theme Dashboard
Steps 4-11 implemented cleanly.
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import streamlit.components.v1 as components
import requests
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import pandas as pd

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SiteSense AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_URL = "http://127.0.0.1:8000"

# ── Step 4: Nike Dark Theme CSS ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap');
*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
  background: #0A0A0A !important; color: #FFFFFF !important;
  font-family: 'Inter', sans-serif !important;
}
#MainMenu, footer, header, [data-testid="stToolbar"],
[data-testid="stDecoration"], .stDeployButton { display: none !important; }
.block-container { padding: 2rem 3rem !important; max-width: 1400px !important; margin: 0 auto; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 0.05em; }
[data-testid="stTabs"] button {
  color: #888 !important; font-family: 'Inter', sans-serif !important;
  font-size: 13px !important; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em;
  border: none !important; background: none !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: #E8002D !important; border-bottom: 2px solid #E8002D !important;
}
.stButton > button {
  background: #E8002D !important; color: #FFFFFF !important;
  border: none !important; border-radius: 2px !important;
  font-family: 'Bebas Neue', sans-serif !important;
  font-size: 18px !important; letter-spacing: 0.1em;
  padding: 12px 32px !important; width: 100%;
}
.stButton > button:hover { background: #C4001F !important; }
.stDownloadButton > button {
  background: #141414 !important; color: #E8002D !important;
  border: 1px solid #E8002D !important; border-radius: 2px !important;
  font-family: 'Bebas Neue', sans-serif !important;
  font-size: 16px !important; letter-spacing: 0.1em;
  padding: 10px 32px !important; width: 100%;
}
.stDownloadButton > button:hover { background: #1f0000 !important; }
.stSelectbox > div > div {
  background: #141414 !important; border: 1px solid #2A2A2A !important;
  color: #FFF !important; border-radius: 2px !important;
}
.stTextInput > div > div > input {
  background: #141414 !important; border: 1px solid #2A2A2A !important;
  color: #FFF !important; border-radius: 2px !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Bebas Neue', sans-serif !important; font-size: 2.5rem !important;
  color: #E8002D !important;
}
[data-testid="stMetricLabel"] { color: #666 !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 0.1em; }
[data-testid="stSidebar"] { background: #0A0A0A !important; border-right: 1px solid #1a1a1a; }
div[data-testid="stExpander"] { background: #111 !important; border: 1px solid #1a1a1a !important; }
.stAlert { background: #141414 !important; border-radius: 2px !important; }
hr { border-color: #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── Step 5: Location data ─────────────────────────────────────────────────────
CITY_AREAS = {
    "Chennai": ["Anna Nagar", "T. Nagar", "Velachery", "Adyar", "Porur", "Tambaram",
                "Sholinganallur", "OMR", "Nungambakkam", "Perambur", "Ambattur",
                "Chromepet", "Guindy", "Mylapore", "Royapettah", "Vadapalani"],
    "Coimbatore": ["RS Puram", "Gandhipuram", "Peelamedu", "Saibaba Colony",
                   "Singanallur", "Hopes College", "Tidel Park"],
    "Madurai": ["Anna Nagar", "Bypass Road", "Thirunagar", "SS Colony", "KK Nagar"],
    "Trichy": ["Thillai Nagar", "KK Nagar", "Srirangam", "Ariyamangalam", "Tennur"],
    "Salem": ["Fairlands", "Suramangalam", "Junction", "Shevapet"],
    "Tirunelveli": ["Palayamkottai", "Junction", "Krishnapuram"],
    "Bengaluru": ["Koramangala", "Indiranagar", "Whitefield", "HSR Layout",
                  "Jayanagar", "Marathahalli", "JP Nagar", "Electronic City"],
    "Mumbai": ["Andheri", "Bandra", "Powai", "Thane", "Borivali", "Goregaon"],
    "Delhi": ["Connaught Place", "Lajpat Nagar", "Dwarka", "Rohini",
              "Saket", "Vasant Kunj", "Karol Bagh"],
    "Hyderabad": ["Banjara Hills", "Jubilee Hills", "Madhapur",
                  "Secunderabad", "Kondapur", "HITEC City"],
    "Pune": ["Koregaon Park", "Hinjewadi", "Kothrud", "Viman Nagar", "Kharadi"],
}

STORE_TYPES = ["cafe", "pharmacy", "clothing", "supermarket", "restaurant"]

# ── Session state ─────────────────────────────────────────────────────────────
for _k, _v in {
    "analysis_result":    None,
    "comparison_results": None,
    "custom_store_types": [],
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# Weight preset session-state defaults
for _k, _v in [
    ("w_demand",        0.25),
    ("w_competition",   0.25),
    ("w_accessibility", 0.25),
    ("w_diversity",     0.25),
    ("active_preset",   "Equal Weights"),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Module-level cached API helpers ──────────────────────────────────────────
@st.cache_data(ttl=10)
def check_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        return r.json() if r.status_code == 200 else {"status": "error"}
    except Exception:
        return {"status": "offline"}


@st.cache_data(ttl=30)
def fetch_kpis():
    try:
        r = requests.get(f"{API_URL}/analytics/kpis", timeout=5)
        return r.json() if r.status_code == 200 else {"error": "bad response"}
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=20)
def fetch_history():
    try:
        r = requests.get(f"{API_URL}/history?limit=20", timeout=3)
        return r.json().get("analyses", []) if r.status_code == 200 else []
    except Exception:
        return []


def fetch_presets() -> dict:
    """Fetch all weight presets. Returns {name: preset_dict}."""
    try:
        r = requests.get(f"{API_URL}/presets", timeout=5)
        r.raise_for_status()
        return {p["name"]: p for p in r.json()["presets"]}
    except Exception:
        return {}


def normalize_weights(d: float, c: float, a: float, div: float):
    """Normalise four weights to sum to 1.0. Returns (d, c, a, div)."""
    total = d + c + a + div
    if total == 0:
        return 0.25, 0.25, 0.25, 0.25
    return (round(d/total, 4), round(c/total, 4),
            round(a/total, 4), round(div/total, 4))


# ── Step 6: Hero banner ───────────────────────────────────────────────────────
def render_hero_banner(score: float, recommendation: str):
    if score >= 70:
        color, label, bg = "#00C853", "STRONG VIABILITY", "#071A0A"
    elif score >= 40:
        color, label, bg = "#FFB300", "MODERATE VIABILITY", "#1A1400"
    else:
        color, label, bg = "#E8002D", "HIGH RISK", "#1A0505"
    st.markdown(f"""
    <div style="background:{bg};border-left:4px solid {color};
                padding:2rem 2.5rem;margin:1.5rem 0;border-radius:2px">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:4.5rem;
                  color:{color};line-height:1;letter-spacing:0.02em">{score:.0f}</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;
                  color:{color};letter-spacing:0.15em;margin-top:4px">{label}</div>
      <div style="font-family:'Inter',sans-serif;font-size:0.9rem;
                  color:#AAA;margin-top:0.75rem">{recommendation}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Step 7: Score metric card (replaces SVG iframe — always readable) ─────────
def render_gauge(label: str, value: float, max_val: float = 100):
    """Compact score card using native st.markdown — no iframes, always visible."""
    color = "#00C853" if value >= 70 else "#FFB300" if value >= 40 else "#E8002D"
    pct   = min(int(value / max_val * 100), 100)
    st.markdown(f"""
    <div style="background:#111;border:1px solid #1a1a1a;border-radius:4px;
                padding:16px 10px 14px;text-align:center;min-height:90px">
      <div style="font-family:'Bebas Neue',sans-serif;font-size:2.6rem;
                  line-height:1;color:{color};margin-bottom:6px">{value:.0f}</div>
      <div style="height:4px;background:#1a1a1a;border-radius:2px;margin:0 4px 8px">
        <div style="height:4px;width:{pct}%;background:{color};border-radius:2px"></div>
      </div>
      <div style="font-size:10px;letter-spacing:2px;color:#555;
                  font-family:'Inter',sans-serif">{label.upper()}</div>
    </div>
    """, unsafe_allow_html=True)



# ── Folium map renderer ───────────────────────────────────────────────────────
def render_map(lat: float, lon: float, radius_km: int,
               competitors: list, transport: list):
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB dark_matter")
    folium.Circle([lat, lon], radius=radius_km * 1000,
                  color="#E8002D", fill=True, fill_opacity=0.05).add_to(m)
    folium.Marker([lat, lon],
                  popup="Target Location",
                  icon=folium.Icon(color="red", icon="star")).add_to(m)
    for c in competitors:
        if "lat" in c and "lon" in c:
            folium.CircleMarker([c["lat"], c["lon"]], radius=5,
                                color="#FF6B35", fill=True,
                                popup=c.get("name", "Competitor")).add_to(m)
    for t in transport:
        if "lat" in t and "lon" in t:
            folium.CircleMarker([t["lat"], t["lon"]], radius=4,
                                color="#00C853", fill=True,
                                popup=t.get("name", "Transport")).add_to(m)
    st_folium(m, width=None, height=400)


# ── POI image scroller ────────────────────────────────────────────────────────
def render_poi_scroller(city: str, categories: list) -> None:
    """
    Fetch POI images from Unsplash via the backend and render a
    horizontal drag-to-scroll gallery. Silently returns on any failure.
    """
    if not categories:
        return
    try:
        resp = requests.get(
            f"{API_URL}/poi-images",
            params={"location": city, "categories": ",".join(categories[:6])},
            timeout=10,
        )
        if resp.status_code != 200:
            return
        images = resp.json().get("images", [])
        if not images:
            return
    except Exception:
        return

    cards_html = ""
    for img in images:
        if not img.get("url"):
            continue
        cat        = img["category"].replace("'", "\\'")
        photo_name = img["photographer"].replace("'", "\\'")
        photo_url  = img.get("photographer_url", "#")
        cards_html += f"""
        <div style="position:relative;flex-shrink:0;width:200px;height:140px;
                    border-radius:6px;overflow:hidden;background:#111;cursor:grab">
            <img src="{img['url']}" alt="{cat}"
                 style="width:200px;height:140px;object-fit:cover;display:block;
                        user-select:none;-webkit-user-drag:none;"
                 draggable="false" loading="lazy"/>
            <div style="position:absolute;top:8px;left:8px;background:rgba(0,0,0,0.72);
                        color:#fff;font-family:'Inter',sans-serif;font-size:10px;
                        font-weight:500;letter-spacing:0.04em;text-transform:uppercase;
                        padding:3px 8px;border-radius:3px;backdrop-filter:blur(4px);
                        pointer-events:none">{cat}</div>
            <a href="{photo_url}?utm_source=sitesense&utm_medium=referral"
               target="_blank" rel="noopener noreferrer"
               style="position:absolute;bottom:6px;right:8px;
                      color:rgba(255,255,255,0.55);font-family:'Inter',sans-serif;
                      font-size:9px;text-decoration:none;pointer-events:auto"
            >{photo_name}</a>
        </div>
        """

    if not cards_html:
        return

    scroller_html = f"""
    <div style="font-family:'Inter',sans-serif;font-size:11px;font-weight:500;
                letter-spacing:0.08em;text-transform:uppercase;color:#555;
                margin-bottom:10px">NEARBY AREA</div>
    <div id="poi-scroller" style="display:flex;gap:10px;overflow-x:auto;
         padding-bottom:8px;cursor:grab;user-select:none;
         -webkit-overflow-scrolling:touch;scrollbar-width:thin;
         scrollbar-color:#2A2A2A #0A0A0A">
        {cards_html}
    </div>
    <style>
        #poi-scroller::-webkit-scrollbar{{height:4px}}
        #poi-scroller::-webkit-scrollbar-track{{background:#0A0A0A}}
        #poi-scroller::-webkit-scrollbar-thumb{{background:#2A2A2A;border-radius:2px}}
        #poi-scroller.grabbing{{cursor:grabbing}}
    </style>
    <script>
        (function(){{
            const el = document.getElementById('poi-scroller');
            if (!el) return;
            let isDown=false, startX=0, scrollLeft=0;
            el.addEventListener('mousedown', e => {{
                isDown=true; el.classList.add('grabbing');
                startX=e.pageX-el.offsetLeft; scrollLeft=el.scrollLeft;
                e.preventDefault();
            }});
            document.addEventListener('mouseup', () => {{
                isDown=false; el.classList.remove('grabbing');
            }});
            el.addEventListener('mousemove', e => {{
                if (!isDown) return;
                el.scrollLeft = scrollLeft-(e.pageX-el.offsetLeft-startX)*1.2;
            }});
            el.addEventListener('touchstart', e => {{
                startX=e.touches[0].pageX-el.offsetLeft; scrollLeft=el.scrollLeft;
            }}, {{passive:true}});
            el.addEventListener('touchmove', e => {{
                el.scrollLeft = scrollLeft-(e.touches[0].pageX-el.offsetLeft-startX);
            }}, {{passive:true}});
        }})();
    </script>
    """
    components.html(scroller_html, height=190, scrolling=False)


# ── Header ────────────────────────────────────────────────────────────────────
health = check_health()
online = health.get("status") == "ok"
dot_color = "#00C853" if online else "#E8002D"
status_text = f"BACKEND ONLINE - {health.get('db_records', 0)} RECORDS" if online else "BACKEND OFFLINE"

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
            padding:0 0 2rem 0;border-bottom:1px solid #1a1a1a;margin-bottom:2rem">
  <div>
    <div style="font-family:'Bebas Neue',sans-serif;font-size:3rem;
                letter-spacing:0.05em;line-height:1">
      SITE<span style="color:#E8002D">SENSE</span> AI
    </div>
    <div style="font-size:11px;letter-spacing:0.2em;color:#444;margin-top:4px">
      RETAIL LOCATION INTELLIGENCE
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:8px">
    <div style="width:8px;height:8px;border-radius:50%;background:{dot_color}"></div>
    <span style="font-size:11px;color:{dot_color};letter-spacing:0.1em;
                 font-family:'Bebas Neue',sans-serif">{status_text}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_analyze, tab_compare, tab_history, tab_analytics, tab_guide = st.tabs([
    "ANALYZE", "COMPARE", "HISTORY", "ANALYTICS", "GUIDE"
])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYZE
# ═══════════════════════════════════════════════════════════════════════════
with tab_analyze:
    st.markdown("""
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                letter-spacing:0.05em;margin-bottom:1.5rem">
      FIND YOUR NEXT LOCATION
    </div>
    """, unsafe_allow_html=True)

    # ── Step 5: Chained location dropdowns ──────────────────────────────
    col_city, col_area, col_type, col_radius = st.columns([2, 2, 2, 1])
    with col_city:
        city = st.selectbox("City", list(CITY_AREAS.keys()), key="city_sel")
    with col_area:
        area = st.selectbox("Area / Neighbourhood", CITY_AREAS[city], key="area_sel")
    with col_type:
        # Merge built-ins + user-added custom types
        all_store_types = STORE_TYPES + [
            t for t in st.session_state.custom_store_types if t not in STORE_TYPES
        ]
        # If a custom type was just added, pre-select it
        _stype_default = st.session_state.get("_pending_store_type", None)
        _stype_idx = all_store_types.index(_stype_default) \
            if _stype_default and _stype_default in all_store_types else 0
        store_type = st.selectbox(
            "Store Type", all_store_types, index=_stype_idx, key="stype_sel"
        )
        # Clear pending after first render
        if "_pending_store_type" in st.session_state:
            del st.session_state["_pending_store_type"]
    with col_radius:
        radius_km = st.slider("Radius km", 1, 5, 1, key="radius_sel")

    # ── Custom store type search (Gemini-powered) ────────────────────────
    with st.expander("Search a custom store type"):
        _si1, _si2 = st.columns([4, 1])
        with _si1:
            custom_input = st.text_input(
                "What kind of store?",
                placeholder="e.g. bubble tea, co-working space, pet clinic",
                label_visibility="collapsed",
                key="custom_store_input",
            )
        with _si2:
            if st.button("Add", key="btn_add_store_type", use_container_width=True):
                raw = custom_input.strip()
                if not raw:
                    st.warning("Type something first.")
                else:
                    with st.spinner("Normalising via Gemini…"):
                        try:
                            import google.generativeai as genai
                            from app import config as _cfg
                            genai.configure(api_key=_cfg.GOOGLE_API_KEY)
                            _model = genai.GenerativeModel("gemini-1.5-flash")
                            _prompt = (
                                f"You are a retail category expert. "
                                f"The user wants to analyse the location suitability for: '{raw}'. "
                                f"Return ONLY a short, lowercase OSM amenity/shop tag that best "
                                f"represents this store type (1-3 words, no punctuation, "
                                f"e.g. 'bubble_tea', 'coworking_space', 'pet_clinic'). "
                                f"No explanation, no quotes."
                            )
                            _resp = _model.generate_content(_prompt)
                            normalised = _resp.text.strip().lower().replace(" ", "_")[:40]
                            normalised = "".join(
                                c for c in normalised if c.isalnum() or c == "_"
                            )
                            if normalised and normalised not in st.session_state.custom_store_types:
                                st.session_state.custom_store_types.append(normalised)
                            st.session_state["_pending_store_type"] = normalised
                            st.success(f"Added: **{normalised}**")
                            st.rerun()
                        except Exception as _e:
                            # Fallback: use the raw input cleaned up
                            _fallback = raw.lower().replace(" ", "_")[:40]
                            _fallback = "".join(
                                c for c in _fallback if c.isalnum() or c == "_"
                            )
                            if _fallback and _fallback not in st.session_state.custom_store_types:
                                st.session_state.custom_store_types.append(_fallback)
                            st.session_state["_pending_store_type"] = _fallback
                            st.info(f"Added (raw): **{_fallback}**")
                            st.rerun()

    location_query = f"{area}, {city}, India"
    st.caption(f"Querying: **{location_query}**")

    # ── Preset selector ──────────────────────────────────────────────────
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    presets = fetch_presets()
    preset_names = list(presets.keys()) if presets else ["Equal Weights"]
    active_idx = preset_names.index(st.session_state.active_preset) \
        if st.session_state.active_preset in preset_names else 0

    selected_preset = st.selectbox(
        "Weight Strategy",
        options=preset_names,
        index=active_idx,
        key="preset_selectbox",
        help="Load a saved weight configuration. Sliders update automatically.",
    )

    # Push preset values into session state on change
    if selected_preset in presets and st.session_state.active_preset != selected_preset:
        p = presets[selected_preset]
        st.session_state.w_demand        = p["demand"]
        st.session_state.w_competition   = p["competition"]
        st.session_state.w_accessibility = p["accessibility"]
        st.session_state.w_diversity     = p["diversity"]
        st.session_state.active_preset   = selected_preset
        st.rerun()

    st.markdown("<div style='height:1px;background:#1A1A1A;margin:8px 0 12px'></div>",
                unsafe_allow_html=True)

    # ── Weight sliders (bound to session state) ──────────────────────────
    _sc1, _sc2 = st.columns(2)
    with _sc1:
        demand_w = st.slider("Demand",        0.0, 1.0,
                             st.session_state.w_demand,        0.05, key="w_d")
        access_w = st.slider("Accessibility", 0.0, 1.0,
                             st.session_state.w_accessibility, 0.05, key="w_a")
    with _sc2:
        comp_w   = st.slider("Competition",   0.0, 1.0,
                             st.session_state.w_competition,   0.05, key="w_c")
        div_w    = st.slider("Diversity",     0.0, 1.0,
                             st.session_state.w_diversity,     0.05, key="w_dv")

    # ── Zero detection + live normalized display ─────────────────────────
    total_w = demand_w + comp_w + access_w + div_w
    if total_w == 0:
        st.warning("All weights are zero — defaulting to equal weighting.")
    nd, nc, na, ndiv = normalize_weights(demand_w, comp_w, access_w, div_w)
    st.markdown(
        f"""<div style='font-size:11px;color:#555;margin-top:4px'>
        Normalized &rarr; Demand <b style='color:#888'>{nd:.0%}</b> &nbsp;&middot;&nbsp;
        Competition <b style='color:#888'>{nc:.0%}</b> &nbsp;&middot;&nbsp;
        Accessibility <b style='color:#888'>{na:.0%}</b> &nbsp;&middot;&nbsp;
        Diversity <b style='color:#888'>{ndiv:.0%}</b>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:1px;background:#1A1A1A;margin:12px 0'></div>",
                unsafe_allow_html=True)

    # ── Save current weights as a named preset ───────────────────────────
    with st.expander("SAVE AS PRESET"):
        _sn1, _sn2 = st.columns([3, 1])
        with _sn1:
            preset_save_name = st.text_input(
                "Preset name",
                placeholder="e.g. High Street Retail",
                max_chars=50,
                label_visibility="collapsed",
                key="preset_name_input",
            )
        with _sn2:
            if st.button("Save", key="btn_save_preset", use_container_width=True):
                if not preset_save_name.strip():
                    st.error("Enter a name before saving.")
                else:
                    try:
                        r = requests.post(
                            f"{API_URL}/presets",
                            json={
                                "name": preset_save_name.strip(),
                                "demand":        demand_w,
                                "competition":   comp_w,
                                "accessibility": access_w,
                                "diversity":     div_w,
                            },
                            timeout=5,
                        )
                        if r.status_code in (200, 201):
                            st.success(f"Saved '{preset_save_name.strip()}'")
                            st.session_state.active_preset = preset_save_name.strip()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            detail = r.json().get("detail", "Unknown error")
                            st.error(f"Save failed: {detail}")
                    except Exception as e:
                        st.error(f"Could not reach API: {e}")

    # ── Analyze button ───────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("ANALYZE LOCATION", key="btn_analyze"):
        with st.spinner("Running multi-agent analysis…"):
            try:
                resp = requests.get(
                    f"{API_URL}/analyze",
                    params={
                        "location": location_query,
                        "store_type": store_type,
                        "radius_km": radius_km,
                        "demand_weight": nd,
                        "competition_weight": nc,
                        "accessibility_weight": na,
                        "diversity_weight": ndiv,
                        "save_to_history": True,
                    },
                    timeout=130,
                )
                data = resp.json()
                if "error" not in data:
                    st.session_state.analysis_result = data
                    fetch_history.clear()  # invalidate history cache
                    st.rerun()
                else:
                    st.error(f"Analysis error: {data['error']}")
            except Exception as e:
                st.error(f"Could not reach backend: {e}")

    # ── Results ──────────────────────────────────────────────────────────
    if st.session_state.analysis_result:
        data = st.session_state.analysis_result
        analysis_id = data.get("analysis_id")

        # Step 6 — Hero banner
        render_hero_banner(data["viability_score"], data["recommendation"])

        # Step 7 — Gauge row
        g1, g2, g3, g4 = st.columns(4)
        with g1: render_gauge("Demand",        data["demand_score"])
        with g2: render_gauge("Competition",   data["competition_score"])
        with g3: render_gauge("Accessibility", data["accessibility_score"])
        with g4: render_gauge("Diversity",     data["diversity_score"])

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Radar + AI Summary
        left_col, right_col = st.columns([3, 2])
        with left_col:
            cats = ["Demand", "Competition", "Accessibility", "Diversity"]
            vals = [data["demand_score"], data["competition_score"],
                    data["accessibility_score"], data["diversity_score"]]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]], theta=cats + [cats[0]],
                fill="toself",
                fillcolor="rgba(232,0,45,0.07)",
                line=dict(color="#E8002D", width=2),
                marker=dict(color="#E8002D", size=5),
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="#0A0A0A",
                    radialaxis=dict(visible=True, range=[0, 100],
                                   gridcolor="#1a1a1a", tickfont=dict(color="#333", size=8)),
                    angularaxis=dict(gridcolor="#1a1a1a",
                                     tickfont=dict(color="#888", size=11,
                                                   family="Bebas Neue")),
                ),
                paper_bgcolor="#0A0A0A", plot_bgcolor="#0A0A0A",
                showlegend=False, height=320,
                margin=dict(l=40, r=40, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

            # POI image scroller — below radar chart
            nearby = data.get("nearby_places_list") or []
            if not nearby:
                # fallback: derive categories from POI data stored in session
                poi = data.get("poi_data_json") or {}
                nearby = poi.get("amenities", [])
            top_cats = list(dict.fromkeys(
                p.get("type", "").strip() or p.get("category", "").strip()
                for p in nearby
                if (p.get("type") or p.get("category", "")).strip()
            ))[:6]
            if not top_cats:
                top_cats = [store_type]   # fallback to selected store type
            render_poi_scroller(city=city, categories=top_cats)

        with right_col:
            explanation = data.get("explanation", "No summary available.")
            st.markdown(f"""
            <div style="background:#111;border:1px solid #1a1a1a;padding:20px;height:100%">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:11px;
                          letter-spacing:3px;color:#333;margin-bottom:12px">AI ANALYSIS</div>
              <p style="font-size:13px;line-height:1.8;color:#888;margin:0">{explanation}</p>
            </div>
            """, unsafe_allow_html=True)

            # Step 11 — Thumbs up / down on Gemini summary
            if analysis_id:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                tu, td, _ = st.columns([1, 1, 6])
                with tu:
                    if st.button("+", key="thumb_up"):
                        requests.patch(
                            f"{API_URL}/analyses/{analysis_id}/explanation-rating",
                            json={"rating": 1}, timeout=3,
                        )
                        st.toast("Feedback saved!")
                with td:
                    if st.button("-", key="thumb_down"):
                        requests.patch(
                            f"{API_URL}/analyses/{analysis_id}/explanation-rating",
                            json={"rating": -1}, timeout=3,
                        )
                        st.toast("Feedback saved!")

        # Validation warnings
        if data.get("validation_warnings"):
            for w in data["validation_warnings"]:
                st.warning(w)

        # Map
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("""<div style="font-family:'Bebas Neue',sans-serif;font-size:14px;
                    letter-spacing:3px;color:#444;margin-bottom:8px">LOCATION MAP</div>""",
                    unsafe_allow_html=True)
        if data.get("latitude") and data.get("longitude"):
            render_map(
                data["latitude"], data["longitude"], radius_km,
                data.get("competitors_list", []),
                data.get("transport_nodes_list", []),
            )

        # Step 1 fix — PDF download (no nested buttons)
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if analysis_id:
            try:
                pdf_resp = requests.get(
                    f"{API_URL}/export-pdf/{analysis_id}", timeout=15
                )
                if pdf_resp.status_code == 200:
                    safe = data["location"].replace(" ", "_").replace(",", "")
                    st.download_button(
                        "DOWNLOAD PDF REPORT",
                        data=pdf_resp.content,
                        file_name=f"SiteSense_{safe}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.caption("PDF generation unavailable.")
            except Exception as e:
                st.caption(f"PDF unavailable: {e}")

        if st.button("CLEAR RESULTS", key="clear_results"):
            st.session_state.analysis_result = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — COMPARE
# ═══════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.markdown("""
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                letter-spacing:0.05em;margin-bottom:1.5rem">
      MULTI-LOCATION COMPARISON
    </div>
    """, unsafe_allow_html=True)

    c_type  = st.selectbox("Store Type", STORE_TYPES, key="cmp_type")
    c_rad   = st.slider("Radius km", 1, 5, 1, key="cmp_radius")

    loc_inputs = []
    for i in range(1, 4):
        cc, ca = st.columns(2)
        with cc:
            cc_sel = st.selectbox(f"City {i}", ["—"] + list(CITY_AREAS.keys()), key=f"cc{i}")
        with ca:
            areas_i = CITY_AREAS.get(cc_sel, []) if cc_sel != "—" else []
            ca_sel = st.selectbox(f"Area {i}", ["—"] + areas_i, key=f"ca{i}")
        if cc_sel != "—" and ca_sel != "—":
            loc_inputs.append(f"{ca_sel}, {cc_sel}, India")

    if st.button("COMPARE LOCATIONS", key="btn_compare") and loc_inputs:
        with st.spinner(f"Comparing {len(loc_inputs)} location(s)…"):
            try:
                resp = requests.post(
                    f"{API_URL}/analyze-multiple",
                    json={"locations": loc_inputs, "store_type": c_type, "radius_km": c_rad},
                    timeout=300,
                )
                result = resp.json()
                if "error" not in result:
                    st.session_state.comparison_results = result
                    st.rerun()
                else:
                    st.error(result["error"])
            except Exception as e:
                st.error(str(e))

    if st.session_state.comparison_results:
        results = st.session_state.comparison_results.get("results", [])
        valid = [r for r in results if "viability_score" in r]
        if valid:
            st.markdown("""<div style="font-family:'Bebas Neue',sans-serif;font-size:14px;
                        letter-spacing:3px;color:#444;margin:16px 0 8px">RANKED RESULTS</div>""",
                        unsafe_allow_html=True)
            for idx, r in enumerate(valid, 1):
                score = r["viability_score"]
                color = "#00C853" if score >= 70 else "#FFB300" if score >= 40 else "#E8002D"
                st.markdown(f"""
                <div style="background:#111;border:1px solid #1a1a1a;padding:16px;
                            margin-bottom:8px;display:flex;align-items:center;gap:16px">
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                              color:{color};min-width:60px">#{idx}</div>
                  <div style="flex:1">
                    <div style="font-family:'Bebas Neue',sans-serif;font-size:1.1rem;
                                color:#fff">{r['location']}</div>
                    <div style="font-size:12px;color:#666;margin-top:2px">{r['recommendation']}</div>
                  </div>
                  <div style="font-family:'Bebas Neue',sans-serif;font-size:2.5rem;color:{color}">
                    {score:.0f}
                  </div>
                </div>
                """, unsafe_allow_html=True)



# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — HISTORY  (Steps 8 & 9)
# ═══════════════════════════════════════════════════════════════════════════
with tab_history:
    st.markdown("""
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                letter-spacing:0.05em;margin-bottom:1.5rem">ANALYSIS HISTORY</div>
    """, unsafe_allow_html=True)

    if st.button("REFRESH HISTORY", key="refresh_hist"):
        fetch_history.clear()
        st.rerun()

    history = fetch_history()
    if not history:
        st.info("No analyses saved yet. Run an analysis first.")
    else:
        for row in history:
            score   = row.get("viability_score", 0)
            color   = "#00C853" if score >= 70 else "#FFB300" if score >= 40 else "#E8002D"
            outcome = row.get("outcome_status")
            if outcome == "Succeeded":
                badge = '<span style="background:#00C853;color:#000;font-size:10px;padding:2px 6px;border-radius:2px;margin-left:8px">Succeeded</span>'
            elif outcome == "Failed":
                badge = '<span style="background:#E8002D;color:#fff;font-size:10px;padding:2px 6px;border-radius:2px;margin-left:8px">Failed</span>'
            elif outcome == "Not Proceeded":
                badge = '<span style="background:#444;color:#fff;font-size:10px;padding:2px 6px;border-radius:2px;margin-left:8px">\u2014 NOT PROCEEDED</span>'
            else:
                badge = ""

            st.markdown(f"""
            <div style="background:#111;border:1px solid #1a1a1a;padding:14px 18px;
                        margin-bottom:6px;display:flex;align-items:center;gap:12px">
              <div style="font-family:'Bebas Neue',sans-serif;font-size:1.8rem;
                          color:{color};min-width:55px">{score:.0f}</div>
              <div style="flex:1">
                <div style="font-size:14px;color:#fff">{row['location']} {badge}</div>
                <div style="font-size:11px;color:#444;margin-top:2px">
                  {row['store_type'].upper()} \u00b7 {str(row.get('timestamp',''))[:16]}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            rid = row["id"]
            b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
            with b1:
                if st.button("Succeeded", key=f"s_{rid}"):
                    requests.patch(f"{API_URL}/analyses/{rid}/outcome",
                                   json={"status": "Succeeded"}, timeout=3)
                    fetch_history.clear(); st.rerun()
            with b2:
                if st.button("Failed", key=f"f_{rid}"):
                    requests.patch(f"{API_URL}/analyses/{rid}/outcome",
                                   json={"status": "Failed"}, timeout=3)
                    fetch_history.clear(); st.rerun()
            with b3:
                if st.button("Skip", key=f"d_{rid}"):
                    requests.patch(f"{API_URL}/analyses/{rid}/outcome",
                                   json={"status": "Not Proceeded"}, timeout=3)
                    fetch_history.clear(); st.rerun()
            with b4:
                if st.button("View", key=f"v_{rid}"):
                    poi    = row.get("poi_data_json") or {}
                    coords = row.get("coordinates") or {}
                    st.session_state.analysis_result = {
                        "location": row["location"],
                        "latitude": coords.get("lat", 0),
                        "longitude": coords.get("lon", 0),
                        "demand_score": row["demand_score"],
                        "competition_score": row["competition_score"],
                        "accessibility_score": row["accessibility_score"],
                        "diversity_score": row["diversity_score"],
                        "viability_score": row["viability_score"],
                        "recommendation": row["recommendation"],
                        "explanation": row.get("explanation", ""),
                        "validation_warnings": row.get("validation_warnings") or [],
                        "competitors_list": poi.get("competitors", []),
                        "transport_nodes_list": poi.get("transport", []),
                        "analysis_id": row["id"],
                    }
                    st.rerun()
            st.markdown("<hr style='border-color:#0d0d0d;margin:4px 0 8px'>",
                        unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — ANALYTICS  (Step 10)
# ═══════════════════════════════════════════════════════════════════════════
with tab_analytics:
    st.markdown("""
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                letter-spacing:0.05em;margin-bottom:1.5rem">PLATFORM ANALYTICS</div>
    """, unsafe_allow_html=True)

    if st.button("REFRESH KPIs", key="refresh_kpi"):
        fetch_kpis.clear()
        st.rerun()

    kpis = fetch_kpis()
    if "error" in kpis:
        st.error(f"Could not load KPIs: {kpis['error']}")
        st.info("Make sure the backend is running, then click REFRESH KPIs.")
    else:
        dist  = kpis.get("score_distribution", {})
        total = kpis.get("total_analyses", 0)

        st.markdown("""<div style="font-family:'Bebas Neue',sans-serif;font-size:13px;
                    letter-spacing:3px;color:#444;margin-bottom:12px">
                    SCORE DISTRIBUTION</div>""", unsafe_allow_html=True)
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total Analyses", str(total))
        d2.metric("Strong >=70",    str(dist.get("strong",   0)),
                  f"{dist.get('strong',0)/total*100:.0f}%" if total else "-")
        d3.metric("Moderate 40-69", str(dist.get("moderate", 0)),
                  f"{dist.get('moderate',0)/total*100:.0f}%" if total else "-")
        d4.metric("Risky <40",      str(dist.get("risky",    0)),
                  f"{dist.get('risky',0)/total*100:.0f}%" if total else "-")

        st.markdown("<hr style='border-color:#1a1a1a;margin:20px 0'>", unsafe_allow_html=True)
        st.markdown("""<div style="font-family:'Bebas Neue',sans-serif;font-size:13px;
                    letter-spacing:3px;color:#444;margin-bottom:12px">
                    ENGAGEMENT</div>""", unsafe_allow_html=True)
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("PDF Export Rate",  f"{kpis.get('pdf_export_rate', 0):.1f}%")
        e2.metric("AI Positive Rate", f"{kpis.get('explanation_positive_rate', 0):.1f}%")
        e3.metric("Outcomes Flagged", str(kpis.get("outcome_flagged_count", 0)))
        e4.metric("Last 30 Days",     str(kpis.get("analyses_last_30_days", 0)))

        cities = kpis.get("city_breakdown", {})
        if cities:
            st.markdown("<hr style='border-color:#1a1a1a;margin:20px 0'>", unsafe_allow_html=True)
            st.markdown("""<div style="font-family:'Bebas Neue',sans-serif;font-size:13px;
                        letter-spacing:3px;color:#444;margin-bottom:12px">
                        CITY BREAKDOWN</div>""", unsafe_allow_html=True)
            city_df = (pd.DataFrame(list(cities.items()), columns=["City", "Analyses"])
                       .sort_values("Analyses", ascending=False))
            st.bar_chart(city_df.set_index("City"))


# ═══════════════════════════════════════════════════════════════════════════
# TAB 5 — GUIDE
# ═══════════════════════════════════════════════════════════════════════════
with tab_guide:
    st.markdown("""
    <div style="font-family:'Bebas Neue',sans-serif;font-size:2rem;
                letter-spacing:0.05em;margin-bottom:1.5rem">HOW IT WORKS</div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        with st.expander("DEMAND SCORE"):
            st.write("Market demand from POI density. Scored 0-100 based on up to 200 surrounding POIs.")
        with st.expander("ACCESSIBILITY SCORE"):
            st.write("60% transit nodes (bus, metro, rail) + 40% surrounding POI density.")
        with st.expander("CUSTOM WEIGHTS"):
            st.write("Adjust sliders for your strategy. Growth = high Demand. Risk-averse = low Competition. Auto-normalises to sum 1.0.")
    with g2:
        with st.expander("COMPETITION SCORE"):
            st.write("Inverted: fewer competitors = higher score. Max 50 direct competitors in radius.")
        with st.expander("DIVERSITY SCORE"):
            st.write("Unique POI category types. More variety = healthier commercial ecosystem.")
        with st.expander("VIABILITY FORMULA"):
            st.code("Score = w_d*Demand + w_c*(100-Competition) + w_a*Accessibility + w_dv*Diversity")
            st.write("Strong >= 70 | Moderate 40-69 | High Risk < 40")

    st.markdown("""
    <div style="text-align:center;color:#222;font-size:11px;margin-top:40px;
                font-family:'Bebas Neue',sans-serif;letter-spacing:0.2em">
      SITESENSE AI v3.0 \u00b7 MULTI-AGENT RETAIL INTELLIGENCE \u00b7 2025
    </div>
    """, unsafe_allow_html=True)



