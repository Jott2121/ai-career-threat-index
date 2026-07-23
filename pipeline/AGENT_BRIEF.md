# Data-agent brief — v2026.3 role generation

You are producing role source files for the AI Career Threat Index. Work only within
your assigned category. Repo root: `/Users/jeffreyotterson/ai-career-threat-index`.

**Read `pipeline/RUBRIC.md` in full before scoring anything.** Every sub-score must
follow its anchors and stay consistent with the calibration examples. SOC codes must
exist in `pipeline/reference/soc_2018_detailed.csv` (grep it for the exact code; use
the closest detailed occupation when a modern role has no dedicated SOC code).

## File contract

One JSON file per role at `pipeline/roles/<slug>.json`:

```json
{
  "slug": "example-role",
  "title": "Example Role",
  "category": "<your assigned category, exactly>",
  "socCode": "15-1252",
  "tier": 1,
  "subscores": {"taskAutomation": 28, "toolMaturity": 82, "adoption": 62, "agenticExposure": 42},
  "rationales": {
    "taskAutomation": "Boilerplate, tests and docs are automatable end-to-end; architecture and cross-team judgment are not.",
    "toolMaturity": "Coding copilots and agentic dev tools are mature and embedded in the standard toolchain.",
    "adoption": "Most large employers now expect AI-assisted development in this function.",
    "agenticExposure": "Agents can own test maintenance and small scoped changes, not system design."
  },
  "tasksAtRisk": ["four to five", "concrete task phrases", "AI handles today", "at >=90% reliability"],
  "tasksGrowing": ["three to four", "tasks gaining value", "as routine work automates"],
  "salary": {"low": 110000, "high": 200000, "currency": "USD"},
  "salarySource": "BLS OES May 2024, SOC 15-1252, p25-p75 rounded",
  "salaryTrend": "rising",
  "defenseSkills": [
    {"skill": "Concrete, role-specific skill", "link": "/guides/ai-coding-tools/"},
    {"skill": "Second skill", "link": "/guides/ai-skills-resume/"},
    {"skill": "Third skill", "link": "/guides/ai-career-paths/"}
  ],
  "insight": "Tier 1: 2-3 punchy, specific sentences. Tier 2: 1-2 sentences.",
  "industryModifiers": {"Tech": 5, "Finance": 3, "Government": -10}
}
```

## Rules

- **subscores**: ints 0–100 per RUBRIC anchors. **rationales**: one specific sentence
  per factor — these are published verbatim, make them count.
- Formula (computed by the pipeline, shown by the validator):
  `score = clamp(round(TA*(0.45 + 0.30*TM/100 + 0.25*AD/100) + 0.10*AG), 0, 100)`
- **salary**: BLS OES national estimates, roughly p25–p75, rounded to the nearest $5k,
  integers. `salarySource` names the SOC anchor. Head tech/finance roles may extend the
  high end toward market postings — say so in salarySource.
- **defenseSkills**: exactly 3. `link` MUST be one of:
  `/guides/ai-agents-guide/`, `/guides/ai-career-paths/`, `/guides/ai-coding-tools/`,
  `/guides/ai-skills-resume/`, `/guides/best-ai-certifications/`.
  Skills are concrete and mid-2026 relevant (agentic-AI literacy where it fits).
  Never generic filler like "adaptability".
- **insight**: no hype words (revolutionary, unprecedented), concrete mechanisms,
  numbers only when defensible.
- **tier 1** requires `industryModifiers`: 3–5 sectors, int adjustments −15..+15.
  Tier 2: omit the field.
- **Existing seed files** (Task A): fill `socCode`, `salarySource`, `subscores`,
  `rationales`; refresh `tasksAtRisk`/`tasksGrowing`/`insight`/`defenseSkills` for the
  mid-2026 agentic era; keep `slug`/`category`/`tier` as-is; NEVER modify
  `historicalScores` or `prevRiskLevel`. Aim for continuity: honest drift is typically
  +1..+6 points vs Q2 2026. If your honest sub-scores move the composite more than ±8
  vs Q2 2026, keep them and add `"restatement": "<one-line reason>"`.
- **New roles** (Task B): omit `historicalScores`, `prevRiskLevel`, `restatement`
  entirely. Use the tier assigned in your roster.
- Slugs: kebab-case; must not collide with ANY existing file in `pipeline/roles/`
  (check with `ls`).

## Validate every file

```
cd /Users/jeffreyotterson/ai-career-threat-index && python3 pipeline/validate_role.py pipeline/roles/<slug>.json
```

Iterate until every file prints `OK`. Zero validation failures allowed.

## Return format (your final text)

One line per file: `slug score band delta(if existing)`, then any restatements with
reasons, then any roster substitutions you made and why.
