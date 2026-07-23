"""Data-integrity tests for the AI Career Threat Index (v2026.3, methodology v2).

This is a *dataset* repo, so the tests validate the data itself: schema, score
ranges, sub-score arithmetic against the published formula, category vocabulary,
CSV/JSON agreement, SOC crosswalk referential integrity, the no-fabricated-
history rule for new roles, and consistency of published risk labels with the
documented bands (including the ±5-point boundary-stability rule).

Stdlib + pytest only.
"""
import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
JSON_PATH = DATA / "ai-career-threat-index.json"
CSV_PATH = DATA / "ai-career-threat-index.csv"
CROSSWALK_PATH = DATA / "soc-crosswalk.csv"
SOC_REF = ROOT / "pipeline" / "reference" / "soc_2018_detailed.csv"

EXPECTED_ROLE_COUNT = 300
EXPECTED_CATEGORY_COUNT = 15
RISK_LEVELS = {"Low", "Moderate", "High", "Very High"}
BOUNDARY_STABILITY = 5
CURRENT_Q = "Q3 2026"
QUARTERS = ["Q1 2025", "Q3 2025", "Q1 2026", "Q2 2026", "Q3 2026"]

REQUIRED_ROLE_FIELDS = ("slug", "title", "category", "socCode", "tier", "score",
                        "riskLevel", "subscores", "rationales", "agenticRisk",
                        "tasksAtRisk", "tasksGrowing", "salaryTrend", "salary",
                        "salarySource", "defenseSkills", "insight",
                        "historicalScores")
SUBS = ("taskAutomation", "toolMaturity", "adoption", "agenticExposure")

EXPECTED_CSV_COLUMNS = ["slug", "title", "category", "score", "risk_level",
                        "salary_low_usd", "salary_high_usd", "salary_trend",
                        "tasks_at_risk_count", "tasks_growing_count",
                        "defense_skill_1", "defense_skill_2", "defense_skill_3",
                        "insight", "score_q1_2025", "score_q3_2025",
                        "score_q1_2026", "score_q2_2026",
                        # v2026.3 additions — appended, never reordered
                        "score_q3_2026", "soc_code", "tier",
                        "sub_task_automation", "sub_tool_maturity",
                        "sub_adoption", "sub_agentic_exposure", "agentic_risk"]


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


@pytest.fixture(scope="module")
def soc_reference():
    with open(SOC_REF, encoding="utf-8") as f:
        return {row["soc_code"]: row["title"] for row in csv.DictReader(f)}


@pytest.fixture(scope="module")
def crosswalk_rows():
    with open(CROSSWALK_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# --- JSON structure ---------------------------------------------------------

def test_json_top_level_keys(dataset):
    assert set(dataset.keys()) >= {"metadata", "categories", "roles"}


def test_role_count(roles):
    assert len(roles) == EXPECTED_ROLE_COUNT


def test_metadata_counts_match(dataset, roles):
    assert dataset["metadata"]["roleCount"] == len(roles)
    assert dataset["metadata"]["categoryCount"] == len(dataset["categories"])


def test_every_role_has_required_fields(roles):
    offenders = {r.get("slug", "?"): [f for f in REQUIRED_ROLE_FIELDS if f not in r]
                 for r in roles}
    offenders = {k: v for k, v in offenders.items() if v}
    assert not offenders, f"roles missing fields: {offenders}"


def test_slugs_are_unique(roles):
    slugs = [r["slug"] for r in roles]
    assert len(set(slugs)) == len(slugs)


# --- Methodology v2: sub-scores and formula ---------------------------------

def expected_score(s):
    realization = 0.45 + 0.30 * s["toolMaturity"] / 100 + 0.25 * s["adoption"] / 100
    return max(0, min(100, round(s["taskAutomation"] * realization
                                 + 0.10 * s["agenticExposure"])))


def test_subscores_are_ints_in_range(roles):
    bad = [(r["slug"], k, r["subscores"].get(k)) for r in roles for k in SUBS
           if not isinstance(r["subscores"].get(k), int)
           or not 0 <= r["subscores"][k] <= 100]
    assert not bad, f"bad subscores: {bad}"


def test_score_matches_published_formula(roles):
    bad = [(r["slug"], r["score"], expected_score(r["subscores"]))
           for r in roles if r["score"] != expected_score(r["subscores"])]
    assert not bad, f"score != formula(subscores): {bad}"


def test_every_subscore_has_a_rationale(roles):
    bad = [(r["slug"], k) for r in roles for k in SUBS
           if not r["rationales"].get(k, "").strip()]
    assert not bad, f"missing rationales: {bad}"


def test_agentic_risk_band_matches_agentic_exposure(roles):
    def band(v):
        return ("Low" if v <= 35 else "Moderate" if v <= 50
                else "High" if v <= 75 else "Very High")
    bad = [(r["slug"], r["subscores"]["agenticExposure"], r["agenticRisk"])
           for r in roles if r["agenticRisk"] != band(r["subscores"]["agenticExposure"])]
    assert not bad, f"agenticRisk inconsistent: {bad}"


# --- Score / label integrity ------------------------------------------------

def test_all_scores_within_0_100(roles):
    bad = [(r["slug"], r["score"]) for r in roles if not 0 <= r["score"] <= 100]
    assert not bad


def test_risk_levels_known(roles):
    bad = [(r["slug"], r["riskLevel"]) for r in roles if r["riskLevel"] not in RISK_LEVELS]
    assert not bad


def _bands(dataset):
    return [(b["name"], b["range"][0], b["range"][1])
            for b in dataset["metadata"]["riskBands"]]


def _allowed_levels(score, bands):
    allowed = {name for name, lo, hi in bands if lo <= score <= hi}
    ordered = sorted(bands, key=lambda b: b[1])
    for i in range(len(ordered) - 1):
        hi = ordered[i][2]
        if abs(score - hi) <= BOUNDARY_STABILITY or abs(score - (hi + 1)) <= BOUNDARY_STABILITY:
            allowed.add(ordered[i][0])
            allowed.add(ordered[i + 1][0])
    return allowed


def test_risk_bands_contiguous(dataset):
    bands = sorted(_bands(dataset), key=lambda b: b[1])
    assert bands[0][1] == 0 and bands[-1][2] == 100
    for (n1, lo1, hi1), (n2, lo2, hi2) in zip(bands, bands[1:]):
        assert lo2 == hi1 + 1, f"gap/overlap between {n1} and {n2}"


def test_risklevel_consistent_with_bands(dataset, roles):
    bands = _bands(dataset)
    bad = [(r["slug"], r["score"], r["riskLevel"])
           for r in roles if r["riskLevel"] not in _allowed_levels(r["score"], bands)]
    assert not bad, f"riskLevel outside bands+stability: {bad}"


def test_salary_sane(roles):
    bad = [r["slug"] for r in roles
           if not (10_000 <= r["salary"]["low"] <= r["salary"]["high"] <= 600_000)]
    assert not bad, f"suspicious salary ranges: {bad}"


def test_history_is_chronological_subset_and_current(roles):
    bad = []
    for r in roles:
        qs = list(r["historicalScores"].keys())
        if qs != [q for q in QUARTERS if q in r["historicalScores"]]:
            bad.append((r["slug"], "quarter order"))
        if r["historicalScores"].get(CURRENT_Q) != r["score"]:
            bad.append((r["slug"], "latest != score"))
    assert not bad, bad


def test_new_roles_have_no_fabricated_history(roles):
    """A role first published in Q3 2026 must not carry earlier quarters."""
    bad = [r["slug"] for r in roles
           if len(r["historicalScores"]) > 1
           and "Q2 2026" not in r["historicalScores"]]
    assert not bad, f"gap-history roles (fabrication suspects): {bad}"


def test_exactly_three_defense_skills_with_https_links(roles):
    bad = [r["slug"] for r in roles
           if len(r["defenseSkills"]) != 3
           or any(not d["link"].startswith("https://") for d in r["defenseSkills"])]
    assert not bad, f"defenseSkills problems: {bad}"


def test_tier1_roles_have_industry_modifiers(roles):
    bad = [r["slug"] for r in roles if r["tier"] == 1 and not r.get("industryModifiers")]
    assert not bad, f"tier-1 roles missing industryModifiers: {bad}"


def test_tier_distribution_sane(roles):
    t1 = sum(1 for r in roles if r["tier"] == 1)
    assert 100 <= t1 <= 160, f"tier-1 count {t1} outside expected 100-160"


# --- SOC codes ---------------------------------------------------------------

def test_every_soc_code_exists_in_reference(roles, soc_reference):
    bad = [(r["slug"], r["socCode"]) for r in roles if r["socCode"] not in soc_reference]
    assert not bad, f"unknown SOC codes: {bad}"


# --- Category vocabulary -----------------------------------------------------

def test_category_count(dataset):
    assert len(dataset["categories"]) == EXPECTED_CATEGORY_COUNT


def test_every_role_category_declared(dataset, roles):
    declared = set(dataset["categories"])
    bad = [(r["slug"], r["category"]) for r in roles if r["category"] not in declared]
    assert not bad


def test_every_category_populated(dataset, roles):
    used = {r["category"] for r in roles}
    empty = set(dataset["categories"]) - used
    assert not empty, f"declared but empty categories: {empty}"


# --- CSV structure and CSV/JSON agreement -----------------------------------

def test_csv_columns_exact_order(csv_rows):
    assert list(csv_rows[0].keys()) == EXPECTED_CSV_COLUMNS


def test_csv_row_count(csv_rows):
    assert len(csv_rows) == EXPECTED_ROLE_COUNT


def test_csv_and_json_agree(roles, csv_rows):
    by_slug = {row["slug"]: row for row in csv_rows}
    assert set(by_slug) == {r["slug"] for r in roles}
    mismatches = []
    for r in roles:
        row = by_slug[r["slug"]]
        checks = [
            ("score", int(row["score"]), r["score"]),
            ("risk_level", row["risk_level"], r["riskLevel"]),
            ("category", row["category"], r["category"]),
            ("salary_low", int(row["salary_low_usd"]), r["salary"]["low"]),
            ("soc_code", row["soc_code"], r["socCode"]),
            ("tier", int(row["tier"]), r["tier"]),
            ("sub_agentic", int(row["sub_agentic_exposure"]),
             r["subscores"]["agenticExposure"]),
        ]
        mismatches += [(r["slug"], name, got, want)
                       for name, got, want in checks if got != want]
    assert not mismatches, f"CSV/JSON disagreements: {mismatches[:10]}"


def test_csv_history_matches_json(roles, csv_rows):
    by_slug = {row["slug"]: row for row in csv_rows}
    col_q = {"score_q1_2025": "Q1 2025", "score_q3_2025": "Q3 2025",
             "score_q1_2026": "Q1 2026", "score_q2_2026": "Q2 2026",
             "score_q3_2026": "Q3 2026"}
    bad = []
    for r in roles:
        row = by_slug[r["slug"]]
        for col, q in col_q.items():
            want = r["historicalScores"].get(q)
            got = row[col]
            if want is None:
                if got != "":
                    bad.append((r["slug"], col, got, "expected empty"))
            elif got == "" or int(got) != want:
                bad.append((r["slug"], col, got, want))
    assert not bad, f"CSV history mismatches: {bad[:10]}"


# --- SOC crosswalk -----------------------------------------------------------

def test_crosswalk_covers_full_soc_taxonomy(crosswalk_rows, soc_reference):
    assert {r["soc_code"] for r in crosswalk_rows} == set(soc_reference)


def test_crosswalk_targets_exist(crosswalk_rows, roles):
    slugs = {r["slug"] for r in roles}
    bad = [r["soc_code"] for r in crosswalk_rows
           if r["match_quality"] != "unmatched" and r["nearest_role_slug"] not in slugs]
    assert not bad, f"crosswalk points at unknown roles: {bad[:10]}"


def test_crosswalk_exact_matches_roundtrip(crosswalk_rows, roles):
    by_slug = {r["slug"]: r for r in roles}
    bad = [r["soc_code"] for r in crosswalk_rows
           if r["match_quality"] == "exact"
           and by_slug[r["nearest_role_slug"]]["socCode"] != r["soc_code"]]
    assert not bad


def test_crosswalk_quality_vocabulary(crosswalk_rows):
    allowed = {"exact", "close", "approximate", "unmatched"}
    bad = {r["match_quality"] for r in crosswalk_rows} - allowed
    assert not bad
