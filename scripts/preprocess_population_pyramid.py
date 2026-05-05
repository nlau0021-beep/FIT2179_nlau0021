"""
preprocess_population_pyramid.py

Reads data/population_state.csv and produces a small CSV suitable for
a population pyramid: 18 age bands x 2 sexes = 36 rows for the latest year.

Run from the repo root:
    python scripts/preprocess_population_pyramid.py
"""

import csv
from collections import defaultdict
from pathlib import Path

INPUT  = Path("data/population_state.csv")
OUTPUT = Path("data/population_pyramid_national.csv")

AGE_ORDER = [
    "0-4","5-9","10-14","15-19","20-24","25-29","30-34","35-39",
    "40-44","45-49","50-54","55-59","60-64","65-69","70-74",
    "75-79","80-84","85+"
]
AGE_INDEX = {band: i for i, band in enumerate(AGE_ORDER)}

print(f"Reading {INPUT} ...")

# Find latest year
years_seen = set()
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] in ("male", "female") and row["ethnicity"] == "overall" and row["age"] in AGE_INDEX:
            # DOSM dates: handle both 'YYYY-MM-DD' and 'DD/MM/YYYY' formats
            d = row["date"]
            year = int(d[:4]) if "-" in d[:5] else int(d[-4:])
            years_seen.add(year)

LATEST = max(years_seen)
print(f"Latest year in dataset: {LATEST}")

def get_year(d):
    return int(d[:4]) if "-" in d[:5] else int(d[-4:])

# Aggregate population by (age, sex) summed across all states
buckets = defaultdict(float)  # buckets[(age, sex)] = pop
with INPUT.open(newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["sex"] not in ("male", "female"): continue
        if row["ethnicity"] != "overall":         continue
        if row["age"] not in AGE_INDEX:           continue
        if get_year(row["date"]) != LATEST:       continue

        buckets[(row["age"], row["sex"])] += float(row["population"])

# Build rows. For pyramid, male population is negated so it extends left.
out_rows = []
for age in AGE_ORDER:
    for sex in ("male", "female"):
        pop_thousands = buckets.get((age, sex), 0.0)
        signed = -pop_thousands if sex == "male" else pop_thousands
        out_rows.append({
            "age":          age,
            "age_order":    AGE_INDEX[age],
            "sex":          sex.capitalize(),
            "population":   round(pop_thousands, 1),
            "signed_pop":   round(signed, 1),
            "year":         LATEST,
        })

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with OUTPUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["age","age_order","sex","population","signed_pop","year"]
    )
    writer.writeheader()
    writer.writerows(out_rows)

print(f"Wrote {OUTPUT}  ({len(out_rows)} rows)")
print()
print(f"{'Age':<8} {'Male (k)':>10} {'Female (k)':>12}")
print("-" * 32)
for age in AGE_ORDER:
    m = buckets.get((age, "male"), 0)
    f_ = buckets.get((age, "female"), 0)
    print(f"{age:<8} {m:>10,.0f} {f_:>12,.0f}")