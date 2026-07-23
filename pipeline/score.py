#!/usr/bin/env python3
"""Assemble the published dataset from per-role source files.

Reads  pipeline/roles/*.json   (one source file per role — the source of truth)
       pipeline/reference/soc_2018_detailed.csv
Emits  data/ai-career-threat-index.json
       data/ai-career-threat-index.csv
       data/soc-crosswalk.csv
       reports/<quarter>-winners-losers.md

Deterministic: same inputs always produce byte-identical outputs.
Stdlib only. Run from anywhere: paths resolve relative to this file.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROLES_DIR = ROOT / "pipeline" / "roles"
SOC_REF = ROOT / "pipeline" / "reference" / "soc_2018_detailed.csv"
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"

VERSION = "2026.3"
LAST_UPDATED = "2026-07-23"
CURRENT_QUARTER = "Q3 2026"
PREV_QUARTER = "Q2 2026"
QUARTER_SLUG = "2026-q3"

CATEGORIES = [
    "Technology", "Business & Finance", "Marketing & Sales",
    "Administrative & Operations", "Healthcare", "Legal", "Education",
    "Creative", "HR & Recruiting", "Project & Product Management",
    "Skilled Trades & Construction", "Transportation & Logistics",
    "Hospitality, Food & Personal Service", "Science & Engineering",
    "Public Service & Safety",
]

BANDS = [("Low", 0, 35), ("Moderate", 36, 50), ("High", 51, 75), ("Very High", 76, 100)]
HYSTERESIS = 5          # points from a boundary within which the prior band is retained
RESTATEMENT_DELTA = 8   # |Q3 - Q2| above this requires an explicit restatement reason

SUBS = ("taskAutomation", "toolMaturity", "adoption", "agenticExposure")
SALARY_TRENDS = {"rising", "stable", "mixed", "declining"}
SITE = "https://www.meritforgeai.com"


def composite(s):
    """Realization model, methodology v2. See pipeline/RUBRIC.md."""
    realization = 0.45 + 0.30 * s["toolMaturity"] / 100 + 0.25 * s["adoption"] / 100
    raw = s["taskAutomation"] * realization + 0.10 * s["agenticExposure"]
    return max(0, min(100, round(raw)))


def strict_band(score):
    for name, lo, hi in BANDS:
        if lo <= score <= hi:
            return name
    raise ValueError(score)


def banded(score, prev_band):
    """Strict band, except retain an adjacent prior band near a boundary."""
    band = strict_band(score)
    if not prev_band or prev_band == band:
        return band
    names = [b[0] for b in BANDS]
    i, j = names.index(band), names.index(prev_band)
    if abs(i - j) != 1:
        return band
    lo, hi = BANDS[names.index(band)][1], BANDS[names.index(band)][2]
    boundary = lo if j < i else hi  # the boundary shared with the prior band
    edge = boundary if j < i else boundary + 1
    if min(abs(score - boundary), abs(score - edge)) <= HYSTERESIS:
        return prev_band
    return band


def fail(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def load_sources():
    files = sorted(ROLES_DIR.glob("*.json"))
    if not files:
        fail(f"no role sources in {ROLES_DIR}")
    roles = []
    for f in files:
        try:
            src = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"{f.name}: invalid JSON ({e})")
        if src.get("slug") != f.stem:
            fail(f"{f.name}: slug {src.get('slug')!r} != filename")
        roles.append(src)
    return roles


def validate(src, soc_ref):
    slug = src["slug"]
    for field in ("title", "category", "socCode", "tier", "subscores", "rationales",
                  "tasksAtRisk", "tasksGrowing", "salary", "salarySource",
                  "salaryTrend", "defenseSkills", "insight"):
        if field not in src:
            fail(f"{slug}: missing {field}")
    if src["category"] not in CATEGORIES:
        fail(f"{slug}: unknown category {src['category']!r}")
    if src["socCode"] not in soc_ref:
        fail(f"{slug}: socCode {src['socCode']} not in SOC 2018 reference")
    if src["tier"] not in (1, 2):
        fail(f"{slug}: tier must be 1 or 2")
    for k in SUBS:
        v = src["subscores"].get(k)
        if not isinstance(v, int) or not 0 <= v <= 100:
            fail(f"{slug}: subscore {k}={v!r} not an int in 0..100")
        if not src["rationales"].get(k, "").strip():
            fail(f"{slug}: missing rationale for {k}")
    sal = src["salary"]
    if not (isinstance(sal.get("low"), int) and isinstance(sal.get("high"), int)
            and 0 < sal["low"] <= sal["high"] and sal.get("currency") == "USD"):
        fail(f"{slug}: bad salary {sal}")
    if src["salaryTrend"] not in SALARY_TRENDS:
        fail(f"{slug}: bad salaryTrend {src['salaryTrend']!r}")
    if not (3 <= len(src["tasksAtRisk"]) <= 6 and 2 <= len(src["tasksGrowing"]) <= 5):
        fail(f"{slug}: tasksAtRisk needs 3-6 items, tasksGrowing 2-5")
    if len(src["defenseSkills"]) != 3:
        fail(f"{slug}: exactly 3 defenseSkills required")
    if src["tier"] == 1 and not src.get("industryModifiers"):
        fail(f"{slug}: tier 1 requires industryModifiers")
    hist = src.get("historicalScores", {})
    if CURRENT_QUARTER in hist:
        fail(f"{slug}: {CURRENT_QUARTER} must not be pre-set in historicalScores")
    if not hist and src.get("prevRiskLevel"):
        fail(f"{slug}: prevRiskLevel without history")


def build_role(src):
    score = composite(src["subscores"])
    hist = dict(src.get("historicalScores", {}))
    prev = hist.get(PREV_QUARTER)
    restated = None
    if prev is not None and abs(score - prev) > RESTATEMENT_DELTA:
        if not src.get("restatement", "").strip():
            fail(f"{src['slug']}: moved {prev}->{score} (>±{RESTATEMENT_DELTA}) "
                 f"without a 'restatement' reason")
        restated = src["restatement"].strip()
    hist[CURRENT_QUARTER] = score
    skills = [{"skill": d["skill"],
               "link": (SITE + d["link"]) if d["link"].startswith("/") else d["link"]}
              for d in src["defenseSkills"]]
    role = {
        "slug": src["slug"],
        "title": src["title"],
        "category": src["category"],
        "socCode": src["socCode"],
        "tier": src["tier"],
        "score": score,
        "riskLevel": banded(score, src.get("prevRiskLevel")),
        "subscores": {k: src["subscores"][k] for k in SUBS},
        "rationales": {k: src["rationales"][k] for k in SUBS},
        "agenticRisk": strict_band(src["subscores"]["agenticExposure"]),
        "tasksAtRisk": src["tasksAtRisk"],
        "tasksGrowing": src["tasksGrowing"],
        "salaryTrend": src["salaryTrend"],
        "salaryRange": f"${src['salary']['low']:,} - ${src['salary']['high']:,}",
        "salary": src["salary"],
        "salarySource": src["salarySource"],
        "defenseSkills": skills,
        "insight": src["insight"],
        "historicalScores": hist,
    }
    if src.get("industryModifiers"):
        role["industryModifiers"] = src["industryModifiers"]
    if restated:
        role["restatement"] = restated
    return role


def emit_json(roles):
    order = {c: i for i, c in enumerate(CATEGORIES)}
    roles = sorted(roles, key=lambda r: (order[r["category"]], -r["score"], r["slug"]))
    doc = {
        "metadata": {
            "name": "AI Career Threat Index",
            "version": VERSION,
            "lastUpdated": LAST_UPDATED,
            "license": "MIT",
            "creator": "MeritForge AI",
            "source": "https://github.com/Jott2121/ai-career-threat-index",
            "canonicalUrl": "https://github.com/Jott2121/ai-career-threat-index",
            "siteUrl": f"{SITE}/data/ai-career-threat-index/",
            "methodologyUrl": "https://github.com/Jott2121/ai-career-threat-index/blob/main/pipeline/RUBRIC.md",
            "methodologyVersion": 2,
            "formula": ("score = clamp(round(taskAutomation * (0.45 + 0.30*toolMaturity/100 "
                        "+ 0.25*adoption/100) + 0.10*agenticExposure), 0, 100)"),
            "description": (
                "Open dataset scoring 300 professions on AI displacement risk (MIT licensed). "
                "Each role carries four published sub-scores (task automation potential, tool "
                "maturity, employer adoption, agentic exposure) combined by an open formula "
                "into a 0-100 score (higher = greater displacement risk). Scores are structured "
                "editorial estimates against a published rubric, not measurements."),
            "riskBands": [{"name": n, "range": [lo, hi]} for n, lo, hi in BANDS],
            "riskBandsNote": ("Scores within 5 points of a band boundary may retain their "
                              "prior band across quarterly reviews for stability."),
            "roleCount": len(roles),
            "categoryCount": len(CATEGORIES),
        },
        "categories": CATEGORIES,
        "roles": roles,
    }
    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / "ai-career-threat-index.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return doc, out


QUARTER_COLS = [("score_q1_2025", "Q1 2025"), ("score_q3_2025", "Q3 2025"),
                ("score_q1_2026", "Q1 2026"), ("score_q2_2026", "Q2 2026"),
                ("score_q3_2026", "Q3 2026")]

CSV_COLUMNS = ["slug", "title", "category", "score", "risk_level",
               "salary_low_usd", "salary_high_usd", "salary_trend",
               "tasks_at_risk_count", "tasks_growing_count",
               "defense_skill_1", "defense_skill_2", "defense_skill_3",
               "insight",
               "score_q1_2025", "score_q3_2025", "score_q1_2026", "score_q2_2026",
               # v2026.3 additions — append-only
               "score_q3_2026", "soc_code", "tier",
               "sub_task_automation", "sub_tool_maturity", "sub_adoption",
               "sub_agentic_exposure", "agentic_risk"]


def emit_csv(doc):
    out = DATA_DIR / "ai-career-threat-index.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in doc["roles"]:
            row = {
                "slug": r["slug"], "title": r["title"], "category": r["category"],
                "score": r["score"], "risk_level": r["riskLevel"],
                "salary_low_usd": r["salary"]["low"], "salary_high_usd": r["salary"]["high"],
                "salary_trend": r["salaryTrend"],
                "tasks_at_risk_count": len(r["tasksAtRisk"]),
                "tasks_growing_count": len(r["tasksGrowing"]),
                "defense_skill_1": r["defenseSkills"][0]["skill"],
                "defense_skill_2": r["defenseSkills"][1]["skill"],
                "defense_skill_3": r["defenseSkills"][2]["skill"],
                "insight": r["insight"],
                "soc_code": r["socCode"], "tier": r["tier"],
                "sub_task_automation": r["subscores"]["taskAutomation"],
                "sub_tool_maturity": r["subscores"]["toolMaturity"],
                "sub_adoption": r["subscores"]["adoption"],
                "sub_agentic_exposure": r["subscores"]["agenticExposure"],
                "agentic_risk": r["agenticRisk"],
            }
            for col, q in QUARTER_COLS:
                row[col] = r["historicalScores"].get(q, "")
            w.writerow(row)
    return out


def emit_crosswalk(doc):
    soc_ref = {}
    with open(SOC_REF, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc_ref[row["soc_code"]] = row["title"]
    by_code = {}
    for r in doc["roles"]:
        by_code.setdefault(r["socCode"], []).append(r)
    for v in by_code.values():
        v.sort(key=lambda r: (r["tier"], r["slug"]))

    def nearest(code):
        if code in by_code:
            return by_code[code][0], "exact"
        for plen, quality in ((6, "close"), (5, "close"), (4, "approximate")):
            pool = [r for c, rs in by_code.items() if c[:plen] == code[:plen] for r in rs]
            if pool:
                pool.sort(key=lambda r: (r["tier"], r["slug"]))
                return pool[0], quality
        pool = [r for c, rs in by_code.items() if c[:2] == code[:2] for r in rs]
        if pool:
            pool.sort(key=lambda r: (r["tier"], r["slug"]))
            return pool[0], "approximate"
        return None, "unmatched"

    out = DATA_DIR / "soc-crosswalk.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["soc_code", "soc_title", "nearest_role_slug", "nearest_role_title",
                    "match_quality", "score", "risk_level"])
        for code in sorted(soc_ref):
            role, quality = nearest(code)
            if role:
                w.writerow([code, soc_ref[code], role["slug"], role["title"],
                            quality, role["score"], role["riskLevel"]])
            else:
                w.writerow([code, soc_ref[code], "", "", "unmatched", "", ""])
    return out, soc_ref


def emit_report(doc):
    roles = doc["roles"]
    existing = [r for r in roles if PREV_QUARTER in r["historicalScores"]]
    new = [r for r in roles if PREV_QUARTER not in r["historicalScores"]]
    for r in existing:
        r["_delta"] = r["score"] - r["historicalScores"][PREV_QUARTER]
    up = sorted(existing, key=lambda r: -r["_delta"])[:10]
    down = sorted(existing, key=lambda r: r["_delta"])[:10]
    agentic = sorted(roles, key=lambda r: -r["subscores"]["agenticExposure"])[:15]
    restated = [r for r in existing if r.get("restatement")]

    REPORTS_DIR.mkdir(exist_ok=True)
    out = REPORTS_DIR / f"{QUARTER_SLUG}-winners-losers.md"
    L = []
    L.append(f"# AI Career Threat Index — {CURRENT_QUARTER} Winners & Losers")
    L.append("")
    L.append(f"Dataset v{VERSION} · {len(roles)} roles ({len(new)} new this quarter) · "
             f"methodology v2 (first quarter with published sub-scores and the "
             f"agentic-exposure factor). Scores are structured editorial estimates "
             f"against a [published rubric](../pipeline/RUBRIC.md).")
    L.append("")
    L.append(f"## Biggest risers ({PREV_QUARTER} → {CURRENT_QUARTER})")
    L.append("")
    L.append("| Role | Category | Q2 | Q3 | Δ |")
    L.append("|---|---|---|---|---|")
    for r in up:
        L.append(f"| {r['title']} | {r['category']} | "
                 f"{r['historicalScores'][PREV_QUARTER]} | {r['score']} | +{r['_delta']} |")
    L.append("")
    L.append("## Biggest fallers")
    L.append("")
    L.append("| Role | Category | Q2 | Q3 | Δ |")
    L.append("|---|---|---|---|---|")
    for r in down:
        L.append(f"| {r['title']} | {r['category']} | "
                 f"{r['historicalScores'][PREV_QUARTER]} | {r['score']} | {r['_delta']} |")
    L.append("")
    L.append("## Most exposed to autonomous agents (new factor)")
    L.append("")
    L.append("| Role | Agentic exposure | Overall score |")
    L.append("|---|---|---|")
    for r in agentic:
        L.append(f"| {r['title']} | {r['subscores']['agenticExposure']} | {r['score']} |")
    L.append("")
    if restated:
        L.append("## Restatements")
        L.append("")
        L.append(f"Moves larger than ±{RESTATEMENT_DELTA} points require a stated reason:")
        L.append("")
        for r in restated:
            L.append(f"- **{r['title']}** ({r['historicalScores'][PREV_QUARTER]} → "
                     f"{r['score']}): {r['restatement']}")
        L.append("")
    for r in existing:
        del r["_delta"]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    return out


def main():
    soc_ref = {}
    with open(SOC_REF, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc_ref[row["soc_code"]] = row["title"]
    sources = load_sources()
    slugs = [s["slug"] for s in sources]
    if len(set(slugs)) != len(slugs):
        fail("duplicate slugs")
    for src in sources:
        validate(src, soc_ref)
    roles = [build_role(src) for src in sources]
    doc, jpath = emit_json(roles)
    cpath = emit_csv(doc)
    xpath, _ = emit_crosswalk(doc)
    rpath = emit_report(doc)
    print(f"OK: {len(roles)} roles -> {jpath.name}, {cpath.name}, {xpath.name}, {rpath.name}")
    from collections import Counter
    print("bands:", dict(Counter(r['riskLevel'] for r in roles)))
    print("tiers:", dict(Counter(r['tier'] for r in roles)))


if __name__ == "__main__":
    main()
