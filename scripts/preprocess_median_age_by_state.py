"""
preprocess_median_age_by_state.py

Reads the locally-downloaded DOSM population_state.csv and produces a small
CSV with median age by state for the most recent year, ready for the
choropleth map.

The state names are normalised to match the geoBoundaries Malaysia ADM1
GeoJSON, which uses 'Kuala Lumpur', 'Labuan', 'Putrajaya' instead of
DOSM's 'W.P. ...' prefix.

If your map ends up with white (uncoloured) states, open
data/malaysia_states.geojson, search for "shapeName", and update the
STATE_NAME_FIXES map below to match the GeoJSON's exact spelling.

Run from the repo root:
    python scripts/preprocess_median_age_by_state.py
"""

import csv
from collections import defaultdict
from pathlib import Path

INPUT  = Path("data/population_state.csv")
OUTPUT = Path("data/median_age_by_state.csv")

# Map DOSM state name -> name used in the GeoJSON.
# Adjust if your GeoJSON uses different spellings.
STATE_NAME_FIXES = {
    "Melaka":    "Malacca",
    "Pulau Pinang":    "Penang",
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "W.P. Labuan":       "Labuan",
    "W.P. Putrajaya":    "Putrajaya",
}

AGE_BANDS = [
    ("00-04", 0,   5), ("05-09", 5,   5), ("10-14", 10,  5),
    ("15-19", 15,  5), ("20-24", 20,  5), ("25-29", 25,  5),
    ("30-34", 30,  5), ("35-39", 35,  5), ("40-44", 40,  5),
    ("45-49", 45,  5), ("50-54", 50,  5), ("55-59", 55,  5),
    ("60-64", 60,  5), ("65-69", 65,  5), ("70-74", 70,  5),
    ("75-79", 75,  5), ("80-84", 80,  5), ("85+",   85, 10),
]
AGE_BAND_NAMES = {b[0] for b in AGE_BANDS}


def median_age(band_pop):
    """Linear interpolation within the band that contains the 50th percentile."""
    total = sum(band_pop.values())
    if total == 0:
        return None
    target = total / 2
    cumulative = 0
    for name, lower, width in AGE_BANDS:
        pop = band_pop.get(name, 0)
        if cumulative + pop >= target:
            into_band = target - cumulative
            return round(lower + (into_band / pop) * width, 2) if pop > 0 else lower
        cumulative += pop
    return None


print(f"Reading {INPUT} ...")

# First pass: find latest year
years_seen = set()
with INPUT.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["sex"] == "both" and row["ethnicity"] == "overall" and row["age"] in AGE_BAND_NAMES:
            years_seen.add(int(row["date"][-4:]))

LATEST = max(years_seen)
print(f"Latest year in dataset: {LATEST}")

# Second pass: aggregate
buckets = defaultdict(lambda: defaultdict(float))
state_totals = defaultdict(float)

with INPUT.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["sex"] != "both":             continue
        if row["ethnicity"] != "overall":    continue
        if row["age"] not in AGE_BAND_NAMES: continue
        if int(row["date"][-4:]) != LATEST:   continue

        state = STATE_NAME_FIXES.get(row["state"], row["state"])
        pop   = float(row["population"])
        buckets[state][row["age"]] += pop
        state_totals[state] += pop

# Build output
out_rows = []
for state in sorted(buckets.keys()):
    out_rows.append({
        "state":        state,
        "median_age":   median_age(buckets[state]),
        "population_k": round(state_totals[state], 1),
        "year":         LATEST,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["state","median_age","population_k","year"])
    writer.writeheader()
    writer.writerows(out_rows)

# Report
print(f"Wrote {OUTPUT}  ({len(out_rows)} states)")
print()
print(f"{'State':<22} {'Median age':>10} {'Population (k)':>16}")
print("-" * 50)
for r in sorted(out_rows, key=lambda r: r["median_age"] or 0, reverse=True):
    print(f"{r['state']:<22} {r['median_age']:>10.2f} {r['population_k']:>16,.0f}")

print()
print("⚠ If any state appears uncoloured on the map, the name in this CSV does NOT")
print("  match the GeoJSON's properties.shapeName. Open data/malaysia_states.geojson,")
print("  find the correct spelling, and add an entry to STATE_NAME_FIXES.")
