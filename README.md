# Job_Market_Dashboard
# 📊 Job Market Pulse

A full-stack **Job Market Analytics dashboard** — Flask REST API + React (Vite) frontend with interactive charts, built on top of a realistic synthetic dataset of 6,000 Indian tech-job postings.

![React](https://img.shields.io/badge/React-19-61DAFB.svg)
![Flask](https://img.shields.io/badge/Flask-3.x-000000.svg)
![Recharts](https://img.shields.io/badge/Recharts-charts-8884d8.svg)

---

## ✨ What it does

A single-page analytics dashboard answering the core job-market questions:

| Question | Visualization |
|---|---|
| Most in-demand skills | Horizontal bar chart |
| Average salary by role | Horizontal bar chart |
| Salary growth & volume by experience | Area chart + bar chart |
| Remote vs Hybrid vs Onsite | Donut chart + avg pay |
| Top hiring cities | Horizontal bar chart |
| Monthly hiring trend (top 5 cities) | Multi-line chart |
| Top recruiting companies | Horizontal bar chart |
| Category breakdown (volume vs pay) | Scatter chart |

All charts respond live to **category / city / work-mode filters**, backed by a Flask API that aggregates the dataset server-side (no heavy computation in the browser).

---

## 🗂️ Project Structure

```
job-market-webapp/
├── backend/
│   ├── app.py                     # Flask REST API (11 endpoints)
│   ├── job_postings_clean.csv     # Cleaned dataset (6,000 rows)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main dashboard layout
│   │   ├── api/client.js          # Fetch wrapper for the Flask API
│   │   └── components/            # Header, Ticker, FilterBar, Panel, charts
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md   ← you are here
```

---

## 🚀 Running the project

You need **two terminals** — one for the backend, one for the frontend.

### 1. Backend (Flask API)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

The API starts at **http://localhost:5000**. Verify it's working by visiting `http://localhost:5000/api/health` — you should see `{"status": "ok", "rows": 6000}`.

### 2. Frontend (React)

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at **http://localhost:5173**.

> The frontend reads the API URL from `frontend/.env` (`VITE_API_URL`). It's already set to `http://localhost:5000/api` — no changes needed for local development.

That's it — open `http://localhost:5173` in your browser and the dashboard will load live data from your Flask backend.

---

## 🔌 API Reference

All endpoints support optional query filters: `?category=...&city=...&work_mode=...`

| Endpoint | Description |
|---|---|
| `GET /api/health` | Health check + row count |
| `GET /api/overview` | KPI summary (avg salary, remote %, top city/skill, etc.) |
| `GET /api/skills?top_n=15` | Most in-demand skills |
| `GET /api/salary-by-role` | Salary stats grouped by job title |
| `GET /api/salary-by-experience` | Average salary per experience band |
| `GET /api/experience-distribution` | Posting counts per experience band |
| `GET /api/work-mode` | Remote/Hybrid/Onsite counts + avg salary |
| `GET /api/cities?top_n=10` | Posting counts & avg salary per city |
| `GET /api/hiring-trend?top_cities=5` | Monthly posting counts for top N cities |
| `GET /api/companies?top_n=15` | Top recruiting companies |
| `GET /api/categories` | Posting counts & avg salary per job category |
| `GET /api/filters` | Distinct values for filter dropdowns |

---

## 🎨 Design

The UI uses a custom dark "market terminal" theme rather than a generic dashboard template:

- **Palette:** deep ink navy background, amber/teal/terracotta accents
- **Type:** Space Grotesk (display) + IBM Plex Sans (body) + IBM Plex Mono (data/labels)
- **Signature element:** a scrolling stat ticker bar at the top, echoing a stock-market ticker but for hiring data

Fully responsive — collapses to a single column on mobile, with a horizontally scrollable ticker and wrapping filter controls.

---

## 📊 About the Dataset

The dataset (`backend/job_postings_clean.csv`) is **synthetically generated** to mirror realistic Indian tech-hiring patterns:
- 15 job roles, each with realistic skill sets and salary bands
- Salaries scale with experience (diminishing returns) and city cost-of-living
- Remote/Hybrid/Onsite ratios vary realistically by role category
- Posting volume weighted toward large IT services firms, matching real hiring volume

This avoids scraping LinkedIn/Naukri directly, which violates their Terms of Service and produces datasets that go stale almost immediately.

Want to use a real dataset instead? Replace `backend/job_postings_clean.csv` with your own CSV — just make sure it has these columns: `job_title, company, city, category, work_mode, experience_required, skills_list, salary_lpa, posted_date`. The `skills_list` column should contain a Python-list-style string, e.g. `"['SQL', 'Python', 'Excel']"`.

---

## 🛠️ Tech Stack

**Backend:** Flask, Flask-CORS, Pandas
**Frontend:** React 19, Vite, Recharts
**Fonts:** Space Grotesk, IBM Plex Sans, IBM Plex Mono (Google Fonts)

---

## 📈 Possible Extensions

- Add authentication + a "saved searches" feature
- Deploy backend (Render/Railway) + frontend (Vercel/Netlify) for a live demo link
- Add a salary-prediction endpoint (regression model) and a "what would I earn?" calculator
- Swap the CSV for a proper database (PostgreSQL/SQLite) as the dataset grows
- Add CSV export of the currently filtered view

---

## 📄 License

MIT — use this freely as a portfolio piece or a starting point for your own analytics project.
