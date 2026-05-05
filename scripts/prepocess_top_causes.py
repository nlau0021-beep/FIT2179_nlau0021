"""
preprocess_top_causes.py

Reads the locally-downloaded WHO 'Top causes of death' CSV (one row per
country/cause/sex) and produces a small CSV with Malaysia's top 10 causes
of death, classified into broad categories for visual encoding.

Run from the repo root:
    python scripts/preprocess_top_causes.py
"""

import csv
from pathlib import Path

INPUT  = Path("data/who_top_causes_of_death.csv")
OUTPUT = Path("data/top_causes_malaysia.csv")

COUNTRY_CODE = "MYS"
TOP_N = 10

# Classify each cause into one of four broad categories.
# This drives colour encoding in the chart and reinforces the "NCDs dominate"
# storytelling beat. Sources: WHO Global Health Estimates groupings.
CATEGORY = {
    # Cardiovascular / circulatory NCDs
    "Ischaemic heart disease":             "Cardiovascular",
    "Stroke":                              "Cardiovascular",
    "Hypertensive heart disease":          "Cardiovascular",
    "Rheumatic heart disease":             "Cardiovascular",
    # Cancers (NCD)
    "Trachea, bronchus, lung cancers":     "Cancer",
    "Breast cancer":                       "Cancer",
    "Liver cancer":                        "Cancer",
    "Colon and rectum cancers":            "Cancer",
    "Stomach cancer":                      "Cancer",
    # Respiratory NCD
    "Chronic obstructive pulmonary disease": "Respiratory NCD",
    # Other NCDs
    "Diabetes mellitus":                   "Other NCD",
    "Kidney diseases":                     "Other NCD",
    "Alzheimer disease and other dementias": "Other NCD",
    "Cirrhosis of the liver":              "Other NCD",
    # Communicable / infectious
    "COVID-19":                            "Communicable",
    "Lower respiratory infections":        "Communicable",
    "Tuberculosis":                        "Communicable",
    "HIV/AIDS":                            "Communicable",
    # Injuries
    "Road injury":                         "Injury",
    "Self-harm":                           "Injury",
    "Drowning":                            "Injury",
    "Falls":                               "Injury",
    "Interpersonal violence":              "Injury",
}

print(f"Reading {INPUT} ...")

# Read all Malaysia rows
mys_rows = []
with INPUT.open(newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["DIM_COUNTRY_CODE"] != COUNTRY_CODE: continue
        if row["DIM_SEX_CODE"] != "BTSX":           continue  # both sexes
        mys_rows.append({
            "cause": row["DIM_GHECAUSE_TITLE"].strip(),
            "rate":  float(row["VAL_DTHS_RATE100K_NUMERIC"]),
            "year":  int(row["DIM_YEAR_CODE"]),
        })

print(f"Found {len(mys_rows)} causes for Malaysia")

# Sort by death rate descending and take top N
mys_rows.sort(key=lambda r: r["rate"], reverse=True)
top = mys_rows[:TOP_N]

# Tag each with its broad category (default to 'Other NCD' if unclassified)
for r in top:
    r["category"] = CATEGORY.get(r["cause"], "Other NCD")
    # Add a rank for explicit ordering
    r["rank"] = top.index(r) + 1

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["rank", "cause", "category", "rate", "year"])
    writer.writeheader()
    writer.writerows(top)

print(f"Wrote {OUTPUT}  ({len(top)} rows)")
print()
print(f"{'Rank':>4}  {'Cause':<42} {'Rate':>8}  {'Category':<18}")
print("-" * 80)
for r in top:
    print(f"{r['rank']:>4}  {r['cause']:<42} {r['rate']:>8.1f}  {r['category']:<18}")