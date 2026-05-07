"""
preprocess_ncd_premature.py

Reads the locally-downloaded WHO 'Premature mortality from NCDs (30-70)' CSV
(every country, every year) and produces a small CSV for the ASEAN
comparison chart.

Output: 6 countries x 22 years x TOTAL only = 132 rows, ~5 KB.

Run from the repo root:
    python scripts/preprocess_ncd_premature.py
"""

import csv
from pathlib import Path

INPUT  = Path("data/who_ncd_premature_mortality.csv")
OUTPUT = Path("data/ncd_premature_asean.csv")

# Six ASEAN countries chosen for relevance to a Malaysian audience.
# Excludes very small ASEAN states (Brunei) and those without consistent
# data (Myanmar, Cambodia, Laos sometimes have gaps).
ASEAN_COUNTRIES = {
    "Malaysia",
    "Singapore",
    "Thailand",
    "Indonesia",
    "Viet Nam",   # WHO uses 'Viet Nam' not 'Vietnam'
    "Philippines",
}

print(f"Reading {INPUT} ...")

rows_out = []
with INPUT.open(newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        if row["GEO_NAME_SHORT"] not in ASEAN_COUNTRIES: continue
        if row["DIM_SEX"] != "TOTAL":                    continue

        country = row["GEO_NAME_SHORT"]
        # Normalise 'Viet Nam' -> 'Vietnam' for nicer display
        if country == "Viet Nam":
            country = "Vietnam"

        rows_out.append({
            "country":  country,
            "year":     int(row["DIM_TIME"]),
            "rate":     float(row["RATE_PER_100_N"]),
            "is_focus": "true" if country == "Malaysia" else "false",
        })

# Sort by country then year
rows_out.sort(key=lambda r: (r["country"], r["year"]))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["country","year","rate","is_focus"])
    writer.writeheader()
    writer.writerows(rows_out)

# Report
print(f"Wrote {OUTPUT}  ({len(rows_out)} rows)")
print()
print("Latest-year values (2021):")
print(f"{'Country':<15} {'Rate (%)':>10}")
print("-" * 28)
latest = sorted(
    [r for r in rows_out if r["year"] == 2021],
    key=lambda r: r["rate"]
)
for r in latest:
    print(f"{r['country']:<15} {r['rate']:>10.1f}")