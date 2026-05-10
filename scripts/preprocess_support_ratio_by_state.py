"""
preprocess_support_ratio_by_state.py

Reads data/population_state.csv and produces a small CSV with each
state's working-age support ratio (workers per elderly person) for
the most recent year.

A higher ratio means more workers supporting each retiree — a
"younger" demographic pressure profile.

State names are normalised to match data/malaysia_states.geojson.

Run from the repo root:
    python scripts/preprocess_support_ratio_by_state.py
"""

import csv
from collections import defaultdict
from pathlib import Path

INPUT  = Path("data/population_state.csv")
OUTPUT = Path("data/support_ratio_by_state.csv")

STATE_NAME_FIXES = {
    "Melaka":            "Malacca",
    "Pulau Pinang":      "Penang",
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "W.P. Labuan":       "Labuan",
    "W.P. Putrajaya":    "Putrajaya",
}

# DOSM 5-year bands grouped into life-stage categories
CHILD_BANDS    = {"0-4", "5-9", "10-14"}
WORKING_BANDS  = {"15-19", "20-24", "25-29", "30-34", "35-39", "40-44",
                  "45-49", "50-54", "55-59", "60-64"}
ELDERLY_BANDS  = {"65-69", "70-74", "75-79", "80-84", "85+"}
ALL_BANDS = CHILD_BANDS | WORKING_BANDS | ELDERLY_BANDS


def get_year(d):
    return int(d[:4]) if "-" in d[:5] else int(d[-4:])


print(f"Reading {INPUT} ...")

# First pass: latest year
years_seen = set()
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] == "both" and row["ethnicity"] == "overall" and row["age"] in ALL_BANDS:
            years_seen.add(get_year(row["date"]))

LATEST = max(years_seen)
print(f"Latest year in dataset: {LATEST}")

# buckets[state] -> {"children": float, "working": float, "elderly": float}
buckets = defaultdict(lambda: {"children": 0.0, "working": 0.0, "elderly": 0.0})

with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] != "both":             continue
        if row["ethnicity"] != "overall":    continue
        if row["age"] not in ALL_BANDS:      continue
        if get_year(row["date"]) != LATEST:  continue

        state = STATE_NAME_FIXES.get(row["state"], row["state"])
        pop   = float(row["population"])

        if   row["age"] in CHILD_BANDS:   buckets[state]["children"] += pop
        elif row["age"] in WORKING_BANDS: buckets[state]["working"]  += pop
        elif row["age"] in ELDERLY_BANDS: buckets[state]["elderly"]  += pop


# Build output
out_rows = []
for state in sorted(buckets.keys()):
    b = buckets[state]
    if b["elderly"] == 0:
        continue
    total = b["children"] + b["working"] + b["elderly"]
    out_rows.append({
        "state":          state,
        "support_ratio":  round(b["working"] / b["elderly"], 1),
        "elderly_pct":    round(100 * b["elderly"] / total, 2),
        "working_k":      round(b["working"], 1),
        "elderly_k":      round(b["elderly"], 1),
        "year":           LATEST,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["state","support_ratio","elderly_pct","working_k","elderly_k","year"]
    )
    writer.writeheader()
    writer.writerows(out_rows)

# Report
print(f"Wrote {OUTPUT}  ({len(out_rows)} states)")
print()
print(f"{'State':<22} {'Ratio':>7} {'Elderly %':>10}")
print("-" * 42)
for r in sorted(out_rows, key=lambda r: r["support_ratio"]):
    print(f"{r['state']:<22} {r['support_ratio']:>7.1f} {r['elderly_pct']:>10.2f}")