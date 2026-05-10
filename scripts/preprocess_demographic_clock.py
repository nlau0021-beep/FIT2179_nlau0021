"""
preprocess_demographic_clock.py

Reads data/population_state.csv and produces a small CSV combining
four demographic indicators per state for the latest year:

  - median_age          : interpolated from 5-year age bands
  - growth_rate_pct     : annual % growth in total pop, latest vs 5y ago
  - elderly_pct         : % of population aged 65+
  - total_k             : total population in thousands

These four together place each state in the 2D demographic-clock
plane (median age × growth rate, sized by population, coloured by
elderly share).

State names are normalised to match data/malaysia_states.geojson.

Run from the repo root:
    python scripts/preprocess_demographic_clock.py
"""

import csv
from collections import defaultdict
from pathlib import Path

INPUT  = Path("data/population_state.csv")
OUTPUT = Path("data/demographic_clock.csv")

STATE_NAME_FIXES = {
    "Melaka":            "Malacca",
    "Pulau Pinang":      "Penang",
    "W.P. Kuala Lumpur": "Kuala Lumpur",
    "W.P. Labuan":       "Labuan",
    "W.P. Putrajaya":    "Putrajaya",
}

# 5-year age bands and their lower bound + width, for median interpolation
AGE_BANDS = [
    ("00-04",  0,  5), ("05-09",  5,  5), ("10-14", 10,  5),
    ("15-19", 15,  5), ("20-24", 20,  5), ("25-29", 25,  5),
    ("30-34", 30,  5), ("35-39", 35,  5), ("40-44", 40,  5),
    ("45-49", 45,  5), ("50-54", 50,  5), ("55-59", 55,  5),
    ("60-64", 60,  5), ("65-69", 65,  5), ("70-74", 70,  5),
    ("75-79", 75,  5), ("80-84", 80,  5), ("85+",   85, 10),
]
AGE_BAND_NAMES = {b[0] for b in AGE_BANDS}
ELDERLY_BANDS  = {"65-69", "70-74", "75-79", "80-84", "85+"}


def get_year(d):
    return int(d[:4]) if "-" in d[:5] else int(d[-4:])


def median_age(band_pop):
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

# First pass: find latest year, and pick a 'previous' year 5 years earlier
years_seen = set()
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] == "both" and row["ethnicity"] == "overall" and row["age"] in AGE_BAND_NAMES:
            years_seen.add(get_year(row["date"]))

LATEST = max(years_seen)
PREV   = LATEST - 5
print(f"Comparing {PREV} vs {LATEST}")

# buckets for the latest year (need band-level for median + elderly + total)
# and just totals for the previous year
latest_bands = defaultdict(lambda: defaultdict(float))
prev_totals  = defaultdict(float)

with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] != "both":             continue
        if row["ethnicity"] != "overall":    continue
        if row["age"] not in AGE_BAND_NAMES: continue

        year = get_year(row["date"])
        state = STATE_NAME_FIXES.get(row["state"], row["state"])
        pop   = float(row["population"])

        if year == LATEST:
            latest_bands[state][row["age"]] += pop
        elif year == PREV:
            prev_totals[state] += pop


# Build output
out_rows = []
for state in sorted(latest_bands.keys()):
    bands = latest_bands[state]
    total_now  = sum(bands.values())
    total_prev = prev_totals.get(state, 0)
    elderly    = sum(p for b, p in bands.items() if b in ELDERLY_BANDS)

    if total_now == 0 or total_prev == 0:
        continue  # skip states without comparable data (e.g., Putrajaya pre-2010)

    # Compounded annual growth rate over 5 years, expressed as %
    growth_rate = ((total_now / total_prev) ** (1/5) - 1) * 100

    out_rows.append({
        "state":           state,
        "median_age":      median_age(bands),
        "growth_rate_pct": round(growth_rate, 2),
        "elderly_pct":     round(100 * elderly / total_now, 2),
        "total_k":         round(total_now, 1),
        "year":            LATEST,
    })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["state","median_age","growth_rate_pct","elderly_pct","total_k","year"]
    )
    writer.writeheader()
    writer.writerows(out_rows)

# Report
print(f"Wrote {OUTPUT}  ({len(out_rows)} states)")
print()
print(f"{'State':<22} {'Median':>8} {'Growth%':>8} {'Eld%':>6} {'Pop k':>9}")
print("-" * 58)
for r in sorted(out_rows, key=lambda r: r["median_age"], reverse=True):
    print(f"{r['state']:<22} {r['median_age']:>8.1f} {r['growth_rate_pct']:>8.2f} "
          f"{r['elderly_pct']:>6.2f} {r['total_k']:>9,.0f}")