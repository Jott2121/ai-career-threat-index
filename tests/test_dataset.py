"""Data-integrity tests for the AI Career Threat Index.

This is a *dataset* repo, so the tests validate the data itself: schema, score
ranges, category vocabulary, CSV/JSON agreement, and internal consistency of the
published risk labels with the documented risk bands (including the ±5-point
boundary-stability rule stated in metadata.riskBandsNote).

Stdlib + pytest only.
"""
import csv
import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parent.parent / "data"
JSON_PATH = DATA / "ai-career-threat-index.json"
CSV_PATH = DATA / "ai-career-threat-index.csv"

EXPECTED_ROLE_COUNT = 76
EXPECTED_CATEGORY_COUNT = 10
RISK_LEVELS = {"Low", "Moderate", "High", "Very High"}
BOUNDARY_STABILITY = 5  # metadata.riskBandsNote: within 5 pts of a boundary may retain prior band

REQUIRED_ROLE_FIELDS = ("slug", "title", "category", "score", "riskLevel",
                        "tasksAtRisk", "tasksGrowing", "salaryTrend", "salary",
                        "defenseSkills", "insight", "historicalScores")

EXPECTED_CSV_COLUMNS = ["slug", "title", "category", "score", "risk_level",
                        "salary_low_usd", "salary_high_usd", "salary_trend",
                        "tasks_at_risk_count", "tasks_growing_count",
                        "defense_skill_1", "defense_skill_2", "defense_skill_3",
                        "insight", "score_q1_2025", "score_q3_2025",
                        "score_q1_2026", "score_q2_2026"]


@pytest.fixture(scope="module")
def dataset():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def roles(dataset):
    return dataset["roles"]


@pytest.fixture(scope="module")
def csv_rows():
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --- JSON structure ---------------------------------------------------------

def test_json_is_valid_and_has_expected_top_level_keys(dataset):
    assert set(dataset.keys()) >= {"metadata", "categories", "roles"}


def test_role_count_is_76(roles):
    assert len(roles) == EXPECTED_ROLE_COUNT


def test_metadata_rolecount_matches_actual(dataset, roles):
    assert dataset["metadata"]["roleCount"] == len(roles)


def test_every_role_has_required_fields(roles):
    missing = {r.get("slug", "?"): [f for f in REQUIRED_ROLE_FIELDS if f not in r]
               for r in roles}
    offenders = {k: v for k, v in missing.items() if v}
    assert not offenders, f"roles missing fields: {offenders}"


def test_slugs_are_unique(roles):
    slugs = [r["slug"] for r in roles]
    assert len(set(slugs)) == len(slugs)


# --- Score / label integrity ------------------------------------------------

def test_all_scores_within_0_100(roles):
    bad = [(r["slug"], r["score"]) for r in roles if not 0 <= r["score"] <= 100]
    assert not bad, f"scores out of range: {bad}"


def test_risk_levels_are_from_the_known_set(roles):
    bad = [(r["slug"], r["riskLevel"]) for r in roles if r["riskLevel"] not in RISK_LEVELS]
    assert not bad, f"unknown riskLevel values: {bad}"


def _bands(dataset):
    return [(b["name"], b["range"][0], b["range"][1])
            for b in dataset["metadata"]["riskBands"]]


def _allowed_levels(score, bands):
    """Levels a score may legitimately carry: its strict band, plus an adjacent
    band when the score is within BOUNDARY_STABILITY points of that boundary
    (the documented quarterly-stability rule)."""
    allowed = {name for name, lo, hi in bands if lo <= score <= hi}
    ordered = sorted(bands, key=lambda b: b[1])
    for i in range(len(ordered) - 1):
        hi = ordered[i][2]
        if abs(score - hi) <= BOUNDARY_STABILITY or abs(score - (hi + 1)) <= BOUNDARY_STABILITY:
            allowed.add(ordered[i][0])
            allowed.add(ordered[i + 1][0])
    return allowed


def test_risk_bands_are_contiguous_and_cover_0_to_100(dataset):
    bands = sorted(_bands(dataset), key=lambda b: b[1])
    assert bands[0][1] == 0 and bands[-1][2] == 100
    for (n1, lo1, hi1), (n2, lo2, hi2) in zip(bands, bands[1:]):
        assert lo2 == hi1 + 1, f"gap/overlap between {n1} and {n2}"


def test_risklevel_consistent_with_bands_and_stability_rule(dataset, roles):
    bands = _bands(dataset)
    bad = [(r["slug"], r["score"], r["riskLevel"])
           for r in roles if r["riskLevel"] not in _allowed_levels(r["score"], bands)]
    assert not bad, f"riskLevel inconsistent with bands (+/-{BOUNDARY_STABILITY} rule): {bad}"


def test_salary_low_not_greater_than_high(roles):
    bad = [r["slug"] for r in roles if r["salary"]["low"] > r["salary"]["high"]]
    assert not bad, f"salary low>high: {bad}"


def test_latest_historical_score_equals_current_score(roles):
    bad = [(r["slug"], r["historicalScores"].get("Q2 2026"), r["score"])
           for r in roles if r["historicalScores"].get("Q2 2026") != r["score"]]
    assert not bad, f"latest quarter != current score: {bad}"


def test_every_role_has_at_least_one_defense_skill(roles):
    bad = [r["slug"] for r in roles if not r.get("defenseSkills")]
    assert not bad, f"roles with no defenseSkills: {bad}"


# --- Category vocabulary -----------------------------------------------------

def test_ten_categories_declared(dataset):
    assert len(dataset["categories"]) == EXPECTED_CATEGORY_COUNT


def test_every_role_category_is_declared(dataset, roles):
    declared = set(dataset["categories"])
    bad = [(r["slug"], r["category"]) for r in roles if r["category"] not in declared]
    assert not bad, f"roles with undeclared category: {bad}"


# --- CSV structure and CSV/JSON agreement -----------------------------------

def test_csv_has_expected_columns(csv_rows):
    assert list(csv_rows[0].keys()) == EXPECTED_CSV_COLUMNS


def test_csv_row_count_is_76(csv_rows):
    assert len(csv_rows) == EXPECTED_ROLE_COUNT


def test_csv_and_json_agree_on_every_role(roles, csv_rows):
    by_slug = {row["slug"]: row for row in csv_rows}
    assert set(by_slug) == {r["slug"] for r in roles}
    mismatches = []
    for r in roles:
        row = by_slug[r["slug"]]
        if int(row["score"]) != r["score"]:
            mismatches.append((r["slug"], "score", row["score"], r["score"]))
        if row["risk_level"] != r["riskLevel"]:
            mismatches.append((r["slug"], "risk_level", row["risk_level"], r["riskLevel"]))
        if row["category"] != r["category"]:
            mismatches.append((r["slug"], "category", row["category"], r["category"]))
        if int(row["salary_low_usd"]) != r["salary"]["low"]:
            mismatches.append((r["slug"], "salary_low", row["salary_low_usd"], r["salary"]["low"]))
    assert not mismatches, f"CSV/JSON disagreements: {mismatches}"


def test_csv_quarterly_scores_are_valid(csv_rows):
    cols = ["score_q1_2025", "score_q3_2025", "score_q1_2026", "score_q2_2026"]
    bad = []
    for row in csv_rows:
        for c in cols:
            v = int(row[c])
            if not 0 <= v <= 100:
                bad.append((row["slug"], c, v))
    assert not bad, f"quarterly scores out of range: {bad}"


def test_csv_latest_quarter_equals_score(csv_rows):
    bad = [(row["slug"], row["score_q2_2026"], row["score"])
           for row in csv_rows if row["score_q2_2026"] != row["score"]]
    assert not bad, f"csv score_q2_2026 != score: {bad}"
