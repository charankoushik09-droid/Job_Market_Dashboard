"""
Convert indian_tech_jobs_2026.csv (Kaggle) into job_postings_clean.csv
for the Job Market Pulse Flask API.

Run from backend/:
    python prepare_kaggle_data.py
"""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

INPUT_PATH = Path(__file__).parent / "indian_tech_jobs_2026.csv"
OUTPUT_PATH = Path(__file__).parent / "job_postings_clean.csv"

EXP_ORDER = ["0-1 years", "1-3 years", "3-5 years", "5-8 years", "8+ years"]

WORK_MODE_MAP = {
    "On-site": "Onsite",
    "Hybrid": "Hybrid",
    "Remote": "Remote",
}

CITY_ALIASES = {
    "Bangalore": "Bengaluru",
    "Gurgaon": "Gurugram",
}


def experience_band(min_yrs: float, max_yrs: float, tier: str) -> str:
    if tier == "Fresher" or (min_yrs == 0 and max_yrs <= 1):
        return "0-1 years"
    yrs = min_yrs if min_yrs > 0 else max_yrs
    if yrs <= 1:
        return "0-1 years"
    if yrs <= 3:
        return "1-3 years"
    if yrs <= 5:
        return "3-5 years"
    if yrs <= 8:
        return "5-8 years"
    return "8+ years"


def parse_skills(raw: str) -> list[str]:
    if pd.isna(raw) or raw == "Not Available":
        return []
    skills = [s.strip() for s in str(raw).split(",") if s.strip()]
    # Drop generic noise tokens that aren't useful in charts
    skip = {"basic", "not available", "analytical", "programming"}
    return [s for s in skills if s.lower() not in skip][:12]


def resolve_city(row: pd.Series) -> str:
    city = str(row.get("primary_city") or row.get("scraped_city") or "Unknown")
    if city == "Remote":
        loc = str(row.get("location") or "")
        if loc and loc != "Remote":
            city = loc.split(",")[0].strip()
        else:
            city = str(row.get("scraped_city") or "Remote")
    return CITY_ALIASES.get(city, city)


def resolve_salary(row: pd.Series, group_medians: dict[tuple, float], role_medians: dict[str, float], overall: float) -> float:
    min_lpa = float(row.get("salary_min_lpa") or 0)
    max_lpa = float(row.get("salary_max_lpa") or 0)
    midpoint = float(row.get("salary_midpoint_lpa") or 0)

    if min_lpa > 0 and max_lpa > 0:
        return round((min_lpa + max_lpa) / 2, 1)
    if midpoint > 0:
        return round(midpoint, 1)

    key = (row["role_category"], row["experience_tier"])
    if key in group_medians:
        return group_medians[key]
    if row["role_category"] in role_medians:
        return role_medians[row["role_category"]]
    return overall


def build_imputation_tables(df: pd.DataFrame) -> tuple[dict, dict, float]:
    disclosed = df.copy()
    disclosed["salary_lpa"] = disclosed.apply(
        lambda r: (r["salary_min_lpa"] + r["salary_max_lpa"]) / 2
        if r["salary_min_lpa"] > 0 and r["salary_max_lpa"] > 0
        else r["salary_midpoint_lpa"],
        axis=1,
    )
    disclosed = disclosed[disclosed["salary_lpa"] > 0]

    group_medians = (
        disclosed.groupby(["role_category", "experience_tier"])["salary_lpa"]
        .median()
        .round(1)
        .to_dict()
    )
    role_medians = disclosed.groupby("role_category")["salary_lpa"].median().round(1).to_dict()
    overall = round(float(disclosed["salary_lpa"].median()), 1)
    return group_medians, role_medians, overall


def transform(df: pd.DataFrame) -> pd.DataFrame:
    group_medians, role_medians, overall = build_imputation_tables(df)

    out = pd.DataFrame()
    out["job_title"] = df["job_title"].astype(str).str.strip()
    out["company"] = df["company_name"].astype(str).str.strip()
    out["city"] = df.apply(resolve_city, axis=1)
    out["category"] = df["role_category"].astype(str).str.strip()
    out["work_mode"] = df["work_mode"].map(WORK_MODE_MAP).fillna("Onsite")
    out["experience_required"] = df.apply(
        lambda r: experience_band(
            float(r["experience_min_yrs"]),
            float(r["experience_max_yrs"]),
            str(r["experience_tier"]),
        ),
        axis=1,
    )
    out["salary_lpa"] = df.apply(
        lambda r: resolve_salary(r, group_medians, role_medians, overall),
        axis=1,
    )
    out["posted_date"] = (
        pd.to_datetime(df["scraped_at"], errors="coerce")
        - pd.to_timedelta(df["days_since_posted"].fillna(0), unit="D")
    ).dt.strftime("%Y-%m-%d")

    skills = df["skills_required"].apply(parse_skills)
    out["skills_list"] = skills.apply(lambda s: str(s))

    # Rows with no skills get a placeholder so explode() still works
    empty_skills = out["skills_list"] == "[]"
    if empty_skills.any():
        out.loc[empty_skills, "skills_list"] = "['General']"

    out = out[out["job_title"].notna() & (out["job_title"] != "")]
    out = out[out["category"].notna() & (out["category"] != "")]
    out["experience_required"] = pd.Categorical(out["experience_required"], categories=EXP_ORDER, ordered=True)
    out = out.sort_values("posted_date", ascending=False).reset_index(drop=True)

    return out


def validate(df: pd.DataFrame) -> None:
    # Ensure skills_list is valid Python literals
    for sample in df["skills_list"].head(20):
        ast.literal_eval(sample)

    assert set(df["work_mode"].unique()).issubset({"Remote", "Hybrid", "Onsite"})
    assert set(df["experience_required"].astype(str).unique()).issubset(set(EXP_ORDER))
    assert (df["salary_lpa"] > 0).all(), "All rows must have a positive salary_lpa"


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    raw = pd.read_csv(INPUT_PATH)
    clean = transform(raw)
    validate(clean)
    clean.to_csv(OUTPUT_PATH, index=False)

    disclosed = ((raw["salary_min_lpa"] > 0) & (raw["salary_max_lpa"] > 0)) | (raw["salary_midpoint_lpa"] > 0)
    print(f"Input rows:     {len(raw):,}")
    print(f"Output rows:    {len(clean):,}")
    print(f"Disclosed pay:  {disclosed.sum():,} ({disclosed.mean()*100:.1f}%)")
    print(f"Imputed pay:    {(~disclosed).sum():,}")
    print(f"Cities:         {clean['city'].nunique()}")
    print(f"Categories:     {clean['category'].nunique()}")
    print(f"Saved -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
