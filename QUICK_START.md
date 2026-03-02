## SiteSense AI v2.0 - Quick Start Guide

### ⚡ 3-Step Setup

**1. Install Dependencies**
```bash
pip install -r requirements.txt
```

**2. Run Backend** (Terminal 1)
```bash
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Output: INFO:     Uvicorn running on http://127.0.0.1:8000
```

**3. Run Frontend** (Terminal 2)
```bash
& ".\.venv\Scripts\streamlit.exe" run frontend/dashboard.py
# Output: You can now view your Streamlit app in your browser at http://localhost:8501
```

**Browser opens automatically to http://localhost:8501**

---

### 📊 Dashboard Overview

#### Tab 1: 📍 Analyze
- **Single location analysis**
- Enter location, store type, radius
- Adjust custom weights (optional)
- Click "Analyze" to run
- View results: metrics, viability, map, explanation
- Download PDF report

#### Tab 2: 🔄 Compare
- **Compare 1-3 locations side-by-side**
- Enter up to 3 location names
- Same store type & radius for all
- Results auto-ranked by viability
- Best location highlighted

#### Tab 3: ⚙️ Guide
- **Educational reference**
- Expandable metric explanations
- Viability formula breakdown
- Strategic weight suggestions

#### Tab 4: 📊 History
- **Previous analyses**
- Shows 10 most recent
- "View" to reload analysis
- "Delete" to remove from history

---

### 🎯 Example Workflows

**Workflow 1: Quick Analysis**
1. Open Tab 1
2. Change location to "London" (default: Paris)
3. Keep defaults (store_type: cafe, radius: 1)
4. Click "Analyze"
5. Wait 10-15 seconds
6. View results immediately

**Workflow 2: Growth Strategy**
1. Open Tab 1
2. Set weights: Demand=0.4, Competition=0.1, Accessibility=0.3, Diversity=0.2
3. Enter location: "Barcelona"
4. Analyze
5. High viability = growth opportunity

**Workflow 3: Site Selection**
1. Open Tab 2
2. Enter 3 cities: "Paris", "Amsterdam", "Berlin"
3. Store type: pharmacy (change from cafe)
4. Click "Compare"
5. Wait 30-45 seconds
6. Ranked table shows best location
7. Make data-driven decision

**Workflow 4: Review Past Decision**
1. Open Tab 4 (History)
2. Find previous analysis
3. Click "View" to reload full results
4. Compare with new analysis

---

### 🎨 Understanding Color Coding

**✅ Green (Strong) - Score > 60**
- Excellent location
- Recommended for expansion
- High viability

**⚠️ Yellow (Moderate) - Score 40-60**
- Mixed indicators
- Requires additional analysis
- Consider carefully

**❌ Red (Risky) - Score < 40**
- Challenging location
- Higher risk
- Consider alternatives

---

### 📈 Metrics Explained

**🎯 Demand Score**
- How many businesses nearby (POI density)
- Higher = more customers & activity
- Scale: 0-200 POIs

**⚔️ Competition**
- How many competitors nearby
- **Lower is better** (less saturation)
- Scale: 0-50 competitors
- Shows as inverse in viability (less competition = higher viability)

**🚌 Accessibility**
- Public transport + foot traffic
- 60% public transport (buses, trains, metros)
- 40% POI density (foot traffic proxy)
- +5 bonus in dense areas (>50 POIs)

**🏙️ Diversity**
- Area has many different business types
- More = economic vitality
- Supports stable, diverse revenue

---

### ⚙️ Custom Weights Explained

**What are weights?**
Sliders that control how much each metric influences the final viability score.

**How do they work?**
- Default: all 0.25 (balanced, equal importance)
- Adjust sliders for your strategy
- Auto-normalize to sum to 1.0
- Weights recompute viability dynamically

**Example Strategies:**

| Strategy | Demand | Competition | Accessibility | Diversity |
|----------|--------|-------------|----------------|-----------|
| **Balanced** | 0.25 | 0.25 | 0.25 | 0.25 |
| **Growth** | 0.40 | 0.10 | 0.30 | 0.20 |
| **Risk-Averse** | 0.20 | 0.40 | 0.20 | 0.20 |
| **Accessibility** | 0.20 | 0.20 | 0.40 | 0.20 |

---

### 📄 PDF Report Contents

Downloaded PDF includes:
- ✅ Location name & details
- ✅ All 4 metric scores
- ✅ Viability score & recommendation
- ✅ Executive explanation (Gemini AI)
- ✅ Report timestamp
- ✅ Professional formatting

**To download:**
1. Run an analysis (Tab 1)
2. Scroll to "Export Report"
3. Click "📄 Download PDF Report"
4. File saves as: `Report_LocationName.pdf`

---

### ⏱️ How Long Does Analysis Take?

**Single location:** 10-15 seconds
- Geocoding: 2-3s
- POI fetching: 5-7s
- Agent processing: 1-2s
- Gemini explanation: 1-3s
- Database save: <1s

**Multi-location (3x):** 30-45 seconds
- Same as 3x single analyses in sequence
- Results ranked automatically

---

### 🚨 Error Messages & Solutions

**"Location not found"**
- Try full address instead of abbreviation
- Example: "Paris, France" instead of "Paris"

**"Request timed out"**
- Network issue or API overloaded
- Try again in 30 seconds
- Or use smaller radius (1 instead of 5 km)

**"Cannot connect to API"**
- Backend not running
- Check Terminal 1: should show "Uvicorn running on http://127.0.0.1:8000"

**"PDF generation failed"**
- Try again or check disk space
- Does not affect analysis results

---

### 💾 Database & History

**Where is data stored?**
- `analysis_history.db` - SQLite database in project root
- Stores: location, scores, weights, explanation, timestamp
- No internet/cloud required
- All data stays local

**How to clear history?**
```python
# Delete analysis_history.db to clear all history
# Then click "Analyze" to recreate empty database
```

---

### 🔧 Configuration & Settings

**API Base URL:**
- Edit in `frontend/dashboard.py` line 33
- Default: `http://127.0.0.1:8000`

**API Timeout:**
- Single analysis: 130 seconds (line in dashboard.py)
- Multi-location: 300 seconds
- Adjust if backend is slow

**Gemini API Key:**
- Set in `.env` file: `GEMINI_API_KEY=your_key_here`
- Required for explanations
- If missing: system shows fallback explanation

---

### 📞 Support & Troubleshooting

**App won't start?**
1. Check Python version: `python --version` (need 3.11+)
2. Verify virtual environment: `.venv\Scripts\python.exe`
3. Check dependencies: `pip list` (should show streamlit, fastapi, etc.)

**Analysis hangs?**
1. Check network connection
2. Increase timeout or reduce radius
3. Try different location

**PDF won't download?**
1. Check browser download settings
2. Ensure disk space available
3. Try different location name

**History not appearing?**
1. Analysis must have completed successfully
2. Check `analysis_history.db` exists
3. Refresh browser (F5)

---

### 🎓 Learning Resources

**In-app Help:**
- Tab 3: Guide tab with expandable explanations
- Hover tooltips on all input fields
- Metric descriptions in result cards

**Documentation:**
- `UPGRADE_GUIDE.md` - Complete technical documentation
- `README.md` - Original project overview

**Examples:**
1. Run analysis on "Paris" (default)
2. Try "London" with pharmacy store type
3. Compare "New York", "Los Angeles", "Chicago"
4. Adjust weights for growth strategy

---

## 🚀 You're Ready!

**Quick recap:**
1. ✅ Backend running on port 8000
2. ✅ Frontend running on port 8501
3. ✅ Go to http://localhost:8501
4. ✅ Run your first analysis
5. ✅ Download PDF report
6. ✅ Compare multiple locations
7. ✅ Review analysis history

**Enjoy SiteSense AI v2.0! 🗺️**

