"""
preprocess_population_ethnicity.py

Reads the locally-downloaded DOSM population_state.csv, applies the same
filters and aggregations the Vega-Lite spec used to do client-side, and
writes a tiny pre-aggregated CSV ready for the chart to load.

No third-party dependencies — uses only Python's standard library.

Run from the repo root:
    python scripts/preprocess_population_ethnicity.py
"""

import csv
from collections import defaultdict
from pathlib import Path

# Paths are relative to the repo root (where you run the script from)
INPUT  = Path("data/population_state.csv")
OUTPUT = Path("data/population_ethnicity_national.csv")

ETHNICITY_LABELS = {
    "bumi_malay":      ("Malay",            1),
    "bumi_other":      ("Other Bumiputera", 2),
    "chinese":         ("Chinese",          3),
    "indian":          ("Indian",           4),
    "other_citizen":   ("Other citizen",    5),
    "other_noncitizen":("Non-citizen",      6),
}

print(f"Reading {INPUT} ...")

# Sum population across all states, keyed by (year, ethnicity)
totals = defaultdict(float)
input_rows = 0

with INPUT.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        input_rows += 1

        # Apply the same filters that were in the Vega-Lite transform chain
        if row["sex"] != "both":
            continue
        if row["age"] != "overall":
            continue
        if row["ethnicity"] == "overall":
            continue
        if row["ethnicity"] not in ETHNICITY_LABELS:
            continue  # skip pre-1991 'bumi' aggregate or any unknown values

        year = int(row["date"][-4:])
        if year < 1991:
            continue

        # population is in thousands; sum across all 16 states
        totals[(year, row["ethnicity"])] += float(row["population"])

print(f"Read {input_rows:,} input rows")

# Build output rows
out_rows = []
for (year, eth), pop_thousands in totals.items():
    label, order = ETHNICITY_LABELS[eth]
    out_rows.append({
        "year": year,
        "Ethnicity": label,
        "stack_order": order,
        "pop_millions": round(pop_thousands / 1000, 3),
    })

out_rows.sort(key=lambda r: (r["year"], r["stack_order"]))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f, fieldnames=["year", "Ethnicity", "stack_order", "pop_millions"]
    )
    writer.writeheader()
    writer.writerows(out_rows)

# Quick verification
years      = sorted({r["year"] for r in out_rows})
ethnicities = sorted({r["Ethnicity"] for r in out_rows})
total_2025 = sum(r["pop_millions"] for r in out_rows if r["year"] == max(years))

print(f"Wrote {OUTPUT}")
print(f"Rows: {len(out_rows)}  ({len(years)} years × {len(ethnicities)} ethnicities)")
print(f"Total population in {max(years)}: {total_2025:.2f} million  (DOSM-published is ~35M)")
print()
print("First 12 rows:")
for r in out_rows[:12]:
    print(f"  {r['year']}  {r['Ethnicity']:<18} {r['pop_millions']:>7.3f}")
print("  ...")
print("Last 6 rows:")
for r in out_rows[-6:]:
    print(f"  {r['year']}  {r['Ethnicity']:<18} {r['pop_millions']:>7.3f}")