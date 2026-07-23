#!/usr/bin/env python3
"""
AI Career Threat Index — Python analysis examples.

Run: python python-analysis.py

Uses only the standard library + requests.
"""

import json
import sys
from collections import Counter
from urllib.request import urlopen

DATA_URL = "https://raw.githubusercontent.com/Jott2121/ai-career-threat-index/main/data/ai-career-threat-index.json"


def load():
    """Fetch the live dataset. Falls back to local file if unreachable."""
    try:
        with urlopen(DATA_URL, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Live fetch failed ({e}); falling back to local data/", file=sys.stderr)
        with open("../data/ai-career-threat-index.json") as f:
            return json.load(f)


def summary_by_band(roles):
    """Count of roles in each risk band."""
    bands = Counter(r["riskLevel"] for r in roles)
    print("\n=== Risk band distribution ===")
    for band in ("Low", "Moderate", "High", "Very High"):
        n = bands.get(band, 0)
        bar = "█" * n
        print(f"  {band:10s} {n:3d} {bar}")


def salary_vs_score(roles):
    """Mean salary midpoint per risk band — does pay correlate with displacement risk?"""
    by_band = {}
    for r in roles:
        if r["salary"]["low"] and r["salary"]["high"]:
            mid = (r["salary"]["low"] + r["salary"]["high"]) / 2
            by_band.setdefault(r["riskLevel"], []).append(mid)
    print("\n=== Mean salary by risk band ===")
    for band in ("Low", "Moderate", "High", "Very High"):
        salaries = by_band.get(band, [])
        if salaries:
            mean = sum(salaries) / len(salaries)
            print(f"  {band:10s} ${mean:>8,.0f}  (n={len(salaries)})")


def biggest_movers(roles):
    """Roles with the largest score change since Q1 2025."""
    movers = []
    for r in roles:
        h = r.get("historicalScores", {})
        if "Q1 2025" in h and "Q2 2026" in h:
            delta = h["Q2 2026"] - h["Q1 2025"]
            movers.append((r["title"], h["Q1 2025"], h["Q2 2026"], delta))
    movers.sort(key=lambda x: -x[3])
    print("\n=== Top 10 score risers (Q1 2025 → Q2 2026) ===")
    for title, q1, q2, delta in movers[:10]:
        print(f"  +{delta:>2d}  {title:35s}  {q1} → {q2}")


def most_resilient(roles, n=10):
    """Roles least exposed to AI displacement."""
    sorted_roles = sorted(roles, key=lambda r: r["score"])
    print(f"\n=== Top {n} most resilient roles ===")
    for r in sorted_roles[:n]:
        print(f"  {r['score']:>3d}/100  {r['title']:35s}  ({r['category']})")


def role_lookup(roles, slug):
    """Print full data for a specific role slug."""
    role = next((r for r in roles if r["slug"] == slug), None)
    if not role:
        print(f"No role with slug '{slug}'")
        return
    print(f"\n=== {role['title']} ===")
    print(f"Score: {role['score']}/100 ({role['riskLevel']})")
    print(f"Salary: {role['salaryRange']} ({role['salaryTrend']})")
    print(f"\nTasks at risk:")
    for t in role["tasksAtRisk"]:
        print(f"  - {t}")
    print(f"\nTasks growing in value:")
    for t in role["tasksGrowing"]:
        print(f"  - {t}")
    print(f"\nDefense skills:")
    for s in role["defenseSkills"]:
        print(f"  - {s['skill']}")
    print(f"\nInsight: {role['insight']}")


def main():
    data = load()
    roles = data["roles"]
    print(f"Loaded {len(roles)} roles, version {data['metadata']['version']}, updated {data['metadata']['lastUpdated']}")
    summary_by_band(roles)
    salary_vs_score(roles)
    biggest_movers(roles)
    most_resilient(roles)
    role_lookup(roles, "software-engineer")


if __name__ == "__main__":
    main()
