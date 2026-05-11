"""
preprocess_state_pyramids.py

Reads data/population_state.csv and produces a small CSV for state-level
population pyramid small multiples. Four states selected to span the
demographic spectrum:

  - Sabah        (youngest, classic pyramid)
  - Selangor     (largest, transitional)
  - Kuala Lumpur (most urban, working-age bulge)
  - Perak        (oldest, narrowing base)

Output: 4 states x 18 age bands x 2 sexes = 144 rows.

Run from the repo root:
    python scripts/preprocess_state_pyramids.py
"""

import csv
from collections import defaultdict
from pathlib import Path

INPUT  = Path("data/population_state.csv")
OUTPUT = Path("data/state_pyramids.csv")

# DOSM uses these state names (no normalisation needed for this chart
# since we don't join to a GeoJSON)
SELECTED_STATES = ["Sabah", "Selangor", "W.P. Kuala Lumpur", "Perak"]

# Display labels for the chart
STATE_LABELS = {
    "Sabah":             "Sabah",
    "Selangor":          "Selangor",
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "Perak":             "Perak",
}

# Padded age band labels (matching the convention used elsewhere in the project
# to avoid Excel date corruption of '5-9', '0-4' etc.)
AGE_ORDER = [
    "00-04","05-09","10-14","15-19","20-24","25-29","30-34","35-39",
    "40-44","45-49","50-54","55-59","60-64","65-69","70-74",
    "75-79","80-84","85+"
]
AGE_INDEX = {band: i for i, band in enumerate(AGE_ORDER)}


def get_year(d):
    return int(d[:4]) if "-" in d[:5] else int(d[-4:])


print(f"Reading {INPUT} ...")

# First pass: latest year
years_seen = set()
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] in ("male", "female") and row["ethnicity"] == "overall" and row["age"] in AGE_INDEX:
            years_seen.add(get_year(row["date"]))

LATEST = max(years_seen)
print(f"Latest year: {LATEST}")

# Aggregate population by (state, age, sex)
buckets = defaultdict(float)

with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["state"] not in SELECTED_STATES:    continue
        if row["sex"] not in ("male", "female"):   continue
        if row["ethnicity"] != "overall":          continue
        if row["age"] not in AGE_INDEX:            continue
        if get_year(row["date"]) != LATEST:        continue

        key = (row["state"], row["age"], row["sex"])
        buckets[key] += float(row["population"])


# Build output, with male values negated so they extend left in the pyramid
out_rows = []
for state in SELECTED_STATES:
    for age in AGE_ORDER:
        for sex in ("male", "female"):
            pop_thousands = buckets.get((state, age, sex), 0.0)
            signed = -pop_thousands if sex == "male" else pop_thousands
            out_rows.append({
                "state":      STATE_LABELS[state],
                "state_order": SELECTED_STATES.index(state),
                "age":        age,
                "age_order":  AGE_INDEX[age],
                "sex":        sex.capitalize(),
                "population": round(pop_thousands, 1),
                "signed_pop": round(signed, 1),
                "year":       LATEST,
            })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["state","state_order","age","age_order","sex","population","signed_pop","year"]
    )
    writer.writeheader()
    writer.writerows(out_rows)

# Report
print(f"Wrote {OUTPUT}  ({len(out_rows)} rows)")
print()
for state in SELECTED_STATES:
    label = STATE_LABELS[state]
    total = sum(buckets.get((state, age, sex), 0)
                for age in AGE_ORDER for sex in ("male", "female"))
    elderly = sum(buckets.get((state, age, sex), 0)
                  for age in AGE_ORDER[13:]   # 65-69 onwards
                  for sex in ("male", "female"))
    print(f"  {label:<14}  total {total:>8,.0f}k  elderly {100*elderly/total:>5.1f}%")