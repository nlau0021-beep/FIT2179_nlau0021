"""
preprocess_elderly_share_by_state.py

Reads data/population_state.csv and produces three small CSVs (one per
reference year) with the percentage of population aged 65+ in each
state. One file per year so each small-multiples map's lookup
matches exactly one row per state.

State names are normalised to match data/malaysia_states.geojson.

Run from the repo root:
    python scripts/preprocess_elderly_share_by_state.py
"""

import csv
from collections import defaultdict
from pathlib import Path

INPUT  = Path("data/population_state.csv")
OUTPUT_DIR = Path("data")

REFERENCE_YEARS = [1991, 2008, 2025]

STATE_NAME_FIXES = {
    "Melaka":            "Malacca",
    "Pulau Pinang":      "Penang",
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "W.P. Labuan":       "Labuan",
    "W.P. Putrajaya":    "Putrajaya",
}

ELDERLY_BANDS = {"65-69", "70-74", "75-79", "80-84", "85+"}
ALL_BANDS = {
    "0-4","5-9","10-14","15-19","20-24","25-29","30-34","35-39",
    "40-44","45-49","50-54","55-59","60-64","65-69","70-74",
    "75-79","80-84","85+"
}


def get_year(d):
    return int(d[:4]) if "-" in d[:5] else int(d[-4:])


print(f"Reading {INPUT} ...")

# buckets[(year, state)] -> {"total": float, "elderly": float}
buckets = defaultdict(lambda: {"total": 0.0, "elderly": 0.0})

with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] != "both":             continue
        if row["ethnicity"] != "overall":    continue
        if row["age"] not in ALL_BANDS:      continue

        year = get_year(row["date"])
        if year not in REFERENCE_YEARS:      continue

        state = STATE_NAME_FIXES.get(row["state"], row["state"])
        pop   = float(row["population"])

        buckets[(year, state)]["total"] += pop
        if row["age"] in ELDERLY_BANDS:
            buckets[(year, state)]["elderly"] += pop


# Write one CSV per year
for year in REFERENCE_YEARS:
    output = OUTPUT_DIR / f"elderly_share_{year}.csv"
    rows = []
    for (y, state), pops in buckets.items():
        if y != year or pops["total"] == 0:
            continue
        rows.append({
            "state":       state,
            "elderly_pct": round(100 * pops["elderly"] / pops["total"], 2),
            "total_k":     round(pops["total"], 1),
        })
    rows.sort(key=lambda r: r["state"])

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["state", "elderly_pct", "total_k"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {output}  ({len(rows)} states)")

print()
print("Per-year top 5:")
for year in REFERENCE_YEARS:
    print(f"\n{year}:")
    rows = sorted(
        [(s, p["elderly"]/p["total"]*100) for (y, s), p in buckets.items() if y == year and p["total"] > 0],
        key=lambda x: x[1], reverse=True
    )
    for state, pct in rows[:5]:
        print(f"  {state:<22} {pct:>6.2f}%")