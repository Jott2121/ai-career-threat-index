# AI Career Threat Index — repo map

Open dataset (MIT): 300 US professions scored 0–100 on AI displacement risk,
methodology v2 (four published sub-scores incl. agentic exposure). Public repo —
keep it free of any employer or personal-workplace references.

## Source of truth & flow

`pipeline/roles/*.json` (one file per role) → `python3 pipeline/score.py` →
`data/*.json|csv` + `data/soc-crosswalk.csv` + `reports/<q>-winners-losers.md`.
Never hand-edit files in `data/`, `assets/`, or `reports/` — regenerate them.

## Commands

- Rebuild everything: `python3 pipeline/score.py && python3 pipeline/generate_svgs.py`
- Validate one role file: `python3 pipeline/validate_role.py pipeline/roles/<slug>.json`
- Tests (CI-equivalent): `pytest tests/`
- CI also fails if `data/`/`assets/`/`reports/` don't match regenerated output.

## Key constraints

- Methodology/rubric: `pipeline/RUBRIC.md`. Formula lives in `score.py::composite`
  and is mirrored in tests + README — change all three together or not at all.
- CSV columns are append-only (downstream consumers); JSON changes additive only.
- New roles never get back-dated `historicalScores` (test enforces).
- Quarterly moves >±8 need a `restatement` reason in the role source.
- SOC codes must exist in `pipeline/reference/soc_2018_detailed.csv`.
- Quarterly release ritual: update quarter constants in `score.py`
  (VERSION/LAST_UPDATED/CURRENT_QUARTER/PREV_QUARTER/QUARTER_SLUG), add the new
  quarter column in `QUARTER_COLS`+tests, rescore sources, regenerate, tag release.

## Surfaces

- `site/` = zero-dependency Pages explorer (deployed by `.github/workflows/pages.yml`).
- `mcp/server.js` = zero-dependency MCP stdio server (also published to npm as
  `threat-index-mcp` when authed).
- Data also mirrored to meritforgeai.com `public/data/` (static files only — the
  site itself is otherwise frozen).
