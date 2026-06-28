"""
app.py
-------
Flask REST API for the Job Market Analytics dashboard.

Serves pre-aggregated analytics from job_postings_clean.csv so the
React frontend never has to process raw rows in the browser.

Run:
    python app.py
Then the API is available at http://localhost:5000/api/...
"""

import ast
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow the React dev server (different port) to call this API

DATA_PATH = Path(__file__).parent / "job_postings_clean.csv"

EXP_ORDER = ["0-1 years", "1-3 years", "3-5 years", "5-8 years", "8+ years"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["posted_date"] = pd.to_datetime(df["posted_date"])
    df["skills_list"] = df["skills_list"].apply(ast.literal_eval)
    return df


# Load once at startup; this dataset is small enough to keep in memory.
df = load_data()


def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    """Optional query-string filters shared by multiple endpoints."""
    category = request.args.get("category")
    city = request.args.get("city")
    work_mode = request.args.get("work_mode")

    if category:
        data = data[data["category"] == category]
    if city:
        data = data[data["city"] == city]
    if work_mode:
        data = data[data["work_mode"] == work_mode]
    return data


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "rows": len(df)})


@app.route("/api/overview")
def overview():
    """Top-line KPI numbers for the dashboard header cards."""
    filtered = apply_filters(df)
    return jsonify({
        "total_postings": int(len(filtered)),
        "avg_salary": round(float(filtered["salary_lpa"].mean()), 1) if len(filtered) else 0,
        "median_salary": round(float(filtered["salary_lpa"].median()), 1) if len(filtered) else 0,
        "remote_pct": round(float((filtered["work_mode"] == "Remote").mean() * 100), 1) if len(filtered) else 0,
        "top_city": filtered["city"].value_counts().idxmax() if len(filtered) else None,
        "top_skill": filtered["skills_list"].explode().value_counts().idxmax() if len(filtered) else None,
        "companies_count": int(filtered["company"].nunique()),
    })


@app.route("/api/skills")
def skills():
    """Most in-demand skills, ranked by number of postings mentioning them."""
    filtered = apply_filters(df)
    top_n = int(request.args.get("top_n", 15))
    counts = filtered["skills_list"].explode().value_counts().head(top_n)
    return jsonify([{"skill": k, "count": int(v)} for k, v in counts.items()])


@app.route("/api/salary-by-role")
def salary_by_role():
    filtered = apply_filters(df)
    grouped = (
        filtered.groupby("job_title")["salary_lpa"]
        .agg(["mean", "median", "min", "max", "count"])
        .round(1)
        .sort_values("mean", ascending=False)
    )
    return jsonify([
        {
            "role": role,
            "mean": row["mean"],
            "median": row["median"],
            "min": row["min"],
            "max": row["max"],
            "count": int(row["count"]),
        }
        for role, row in grouped.iterrows()
    ])


@app.route("/api/salary-by-experience")
def salary_by_experience():
    filtered = apply_filters(df)
    grouped = filtered.groupby("experience_required")["salary_lpa"].mean().reindex(EXP_ORDER).round(1)
    return jsonify([
        {"experience": exp, "avg_salary": (None if pd.isna(val) else val)}
        for exp, val in grouped.items()
    ])


@app.route("/api/experience-distribution")
def experience_distribution():
    filtered = apply_filters(df)
    counts = filtered["experience_required"].value_counts().reindex(EXP_ORDER).fillna(0)
    return jsonify([{"experience": exp, "count": int(val)} for exp, val in counts.items()])


@app.route("/api/work-mode")
def work_mode():
    filtered = apply_filters(df)
    counts = filtered["work_mode"].value_counts()
    salary = filtered.groupby("work_mode")["salary_lpa"].mean().round(1)
    return jsonify([
        {
            "mode": mode,
            "count": int(counts.get(mode, 0)),
            "avg_salary": float(salary.get(mode, 0)),
        }
        for mode in counts.index
    ])


@app.route("/api/cities")
def cities():
    filtered = apply_filters(df)
    top_n = int(request.args.get("top_n", 10))
    counts = filtered["city"].value_counts().head(top_n)
    salary = filtered.groupby("city")["salary_lpa"].mean().round(1)
    return jsonify([
        {"city": city, "postings": int(count), "avg_salary": float(salary.get(city, 0))}
        for city, count in counts.items()
    ])


@app.route("/api/hiring-trend")
def hiring_trend():
    """Monthly postings count, optionally split by the top N cities."""
    filtered = apply_filters(df)
    top_n_cities = int(request.args.get("top_cities", 5))
    top_cities = filtered["city"].value_counts().head(top_n_cities).index.tolist()

    subset = filtered[filtered["city"].isin(top_cities)].copy()
    subset["month"] = subset["posted_date"].dt.to_period("M").astype(str)

    grouped = subset.groupby(["month", "city"]).size().reset_index(name="postings")

    months = sorted(grouped["month"].unique())
    series = {city: {m: 0 for m in months} for city in top_cities}
    for _, row in grouped.iterrows():
        series[row["city"]][row["month"]] = int(row["postings"])

    return jsonify({
        "months": months,
        "cities": top_cities,
        "series": series,
    })


@app.route("/api/companies")
def companies():
    filtered = apply_filters(df)
    top_n = int(request.args.get("top_n", 15))
    counts = filtered["company"].value_counts().head(top_n)
    return jsonify([{"company": k, "count": int(v)} for k, v in counts.items()])


@app.route("/api/categories")
def categories():
    filtered = apply_filters(df)
    counts = filtered["category"].value_counts()
    salary = filtered.groupby("category")["salary_lpa"].mean().round(1)
    return jsonify([
        {"category": cat, "count": int(count), "avg_salary": float(salary.get(cat, 0))}
        for cat, count in counts.items()
    ])


@app.route("/api/filters")
def filters():
    """Distinct filter values for the dashboard's dropdown controls."""
    return jsonify({
        "categories": sorted(df["category"].unique().tolist()),
        "cities": sorted(df["city"].unique().tolist()),
        "work_modes": sorted(df["work_mode"].unique().tolist()),
    })


if __name__ == "__main__":
    # use_reloader=False avoids duplicate listeners on Windows (port 5000 conflicts).
    app.run(debug=True, port=5000, use_reloader=False)
