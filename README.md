# SiteSense AI — Retail Location Intelligence Platform

> **Multi-agent AI system that scores retail locations across Demand, Competition, Accessibility, and Diversity — powered by LangGraph, Gemini, and real-world geospatial data.**

---

## What It Does

SiteSense AI helps retail businesses answer one question fast:

**"Is this location worth opening a store in?"**

You pick a city, neighbourhood, store type, and analysis radius. Eight specialized AI agents run in parallel, pulling live data from OpenStreetMap, geocoding the address, scoring the location across four dimensions, and generating a plain-English recommendation — all in under 2 minutes.

---

## Demo

| Analyze Tab | Score Cards + Radar |
|---|---|
| City → Area → Store Type dropdowns | Demand / Competition / Accessibility / Diversity |
| Weight Strategy presets | AI summary + thumbs feedback |
| Custom store type search (Gemini) | Nearby Area image scroller (Unsplash) |
| PDF report download | Folium map with competitors + transit |

---

## Key Features

### AI Pipeline (8 Agents via LangGraph)
| Agent | Role |
|---|---|
| **Geocoder** | Resolves location to lat/lon |
| **Demand** | Foot traffic proxies from nearby amenities |
| **Competition** | Counts and scores nearby competitors |
| **Accessibility** | Transit nodes, walkability |
| **Diversity** | Neighbourhood demographic mix |
| **Validation** | Data quality checks, flags gaps |
| **Decision** | Weighted composite viability score (0–100) |
| **Explanation** | Gemini generates plain-English summary |

### Backend (FastAPI + SQLite)
- `GET /analyze` — Full 8-agent pipeline, persists to DB
- `POST /analyze-multiple` — Multi-location comparison with ranked output
- `GET /presets` / `POST /presets` — Named weight preset CRUD (5 built-ins seeded)
- `GET /poi-images` — Async Unsplash image fetch with graceful degradation
- `GET /analytics/kpis` — Live KPI aggregation (score distributions, engagement)
- `GET /export-pdf/{id}` — Streamed PDF report (ReportLab)
- `PATCH /analyses/{id}/outcome` — Track real-world outcome (Succeeded / Failed)
- Non-destructive SQLite schema migrations — existing records never touched

### Frontend (Streamlit)
- **Nike-inspired dark theme** — Bebas Neue font, `#0A0A0A` background, `#E8002D` accents
- **Chained dropdowns** — City → Area → Store Type (Pan-India coverage)
- **Weight Strategy** — Preset selectbox (Equal / Growth / Risk-Averse / Transit-First / Diversity-Led) with live normalisation display
- **Custom store type search** — Type anything, Gemini normalises it to an OSM tag, appends to dropdown
- **Score cards** — Demand / Competition / Accessibility / Diversity with progress bars
- **Radar chart** — Plotly polar chart with AI summary panel
- **POI image scroller** — Horizontal drag-to-scroll gallery from Unsplash, per-category badges
- **History tab** — Outcome tracking, restore full analysis from history
- **Analytics tab** — Score distribution charts, city breakdown, engagement KPIs

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Orchestration | LangGraph |
| LLM | Google Gemini 1.5 Flash |
| Geospatial Data | OpenStreetMap via Overpass API |
| Backend | FastAPI + Uvicorn |
| Database | SQLite (via `sqlite3`, no ORM) |
| PDF | ReportLab |
| Image API | Unsplash |
| HTTP Client | httpx (async) |
| Frontend | Streamlit |
| Maps | Folium + streamlit-folium |
| Charts | Plotly |

---

## Project Structure

```
retail-location-bi/
├── app/
│   ├── main.py            # FastAPI app, all endpoints
│   ├── orchestrator.py    # LangGraph pipeline runner
│   ├── database.py        # SQLite schema, CRUD, migrations
│   ├── data_fetch.py      # Overpass API with retry + failover
│   ├── config.py          # Env vars (GOOGLE_API_KEY, UNSPLASH_ACCESS_KEY)
│   ├── agent_logger.py    # Per-agent structured logging
│   └── explanation_agent.py  # Gemini summary agent
├── frontend/
│   └── dashboard.py       # Streamlit UI (single file)
├── analysis_history.db    # SQLite database (auto-created)
├── requirements.txt
└── .env                   # Local secrets (not committed)
```

---

## Setup

### 1. Clone
```bash
git clone https://github.com/RiteshRagav/retail-location-bi.git
cd retail-location-bi
```

### 2. Create virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file in the project root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
```

- **Gemini key** → [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Unsplash key** → [Unsplash Developers](https://unsplash.com/oauth/applications) (Access Key, not Secret)

> The Unsplash key is optional. If absent, the image scroller silently renders nothing.

### 5. Run the backend
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 6. Run the frontend (separate terminal)
```bash
python -m streamlit run frontend/dashboard.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

---

## Usage

1. **Pick a location** — Select City, Area, Store Type, and Radius from the dropdowns
2. **Choose a weight strategy** — Select a preset or drag the four sliders manually
3. **Custom store type** — Can't find your store type? Type it in the search box — Gemini will normalise it
4. **Run analysis** — Click ANALYZE LOCATION and wait ~60–90 seconds
5. **Review results** — Score cards, radar chart, AI summary, map, and nearby images
6. **Track outcomes** — Mark each analysis as Succeeded / Failed in the History tab
7. **Download PDF** — Export the full report for sharing

---

## Weight Presets

| Preset | Demand | Competition | Accessibility | Diversity |
|---|---|---|---|---|
| Equal Weights | 25% | 25% | 25% | 25% |
| Growth | 40% | 15% | 25% | 20% |
| Risk-Averse | 20% | 40% | 20% | 20% |
| Transit-First | 20% | 20% | 45% | 15% |
| Diversity-Led | 20% | 15% | 20% | 45% |

Custom presets can be saved and named from the UI — they persist across sessions.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System status + DB record count |
| `GET` | `/analyze` | Run full 8-agent analysis |
| `POST` | `/analyze-multiple` | Compare multiple locations |
| `GET` | `/history` | Recent analysis list |
| `GET` | `/analytics/kpis` | Aggregated platform KPIs |
| `GET` | `/export-pdf/{id}` | Download PDF report |
| `GET` | `/presets` | List weight presets |
| `POST` | `/presets` | Save / update a preset |
| `GET` | `/poi-images` | Fetch Unsplash images for a location |
| `PATCH` | `/analyses/{id}/outcome` | Record real-world outcome |
| `PATCH` | `/analyses/{id}/explanation-rating` | Rate AI summary (+1 / -1) |

Full interactive docs at **http://127.0.0.1:8000/docs** when the backend is running.

---

## Database

The SQLite database (`analysis_history.db`) is auto-created on first run. Schema migrations are **non-destructive** — existing records are never modified or deleted when the schema evolves.

Tables:
- `analysis_history` — All analysis results, scores, weights, POI data, outcomes
- `weight_presets` — Named weight configurations (5 built-ins + user-saved)
- `user_events` — Lightweight event log for analytics

---

## License

MIT License — free to use, modify, and distribute.

---

## Author

Built by **Ritesh Ragav**

- GitHub: [@RiteshRagav](https://github.com/RiteshRagav)
- Repo: [retail-location-bi](https://github.com/RiteshRagav/retail-location-bi)
