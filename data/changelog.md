# Changelog

All notable changes to the AI Career Threat Index dataset are documented here.
Versioning follows the format `YEAR.QUARTER` — e.g., `2026.2` is the second-quarter 2026 review.

## [2026.3] — 2026-07-23

The big one: methodology v2, 300 roles, full transparency.

### Coverage
- **76 → 300 roles**; 10 → 15 categories (adds Skilled Trades & Construction,
  Transportation & Logistics, Hospitality/Food & Personal Service, Science &
  Engineering, Public Service & Safety)
- Every role now carries a **BLS SOC 2018 code** and a **BLS-OES-anchored salary
  range** with a named anchor (`salarySource`)
- New **`data/soc-crosswalk.csv`**: all 867 SOC 2018 detailed occupations mapped to
  their nearest scored role with match quality
- New roles begin their history at Q3 2026 — earlier quarters are never backfilled

### Methodology v2 (breaking change in how scores are derived, not in the schema)
- Composite is now computed from **four published sub-scores** —
  `taskAutomation`, `toolMaturity`, `adoption`, and the new **`agenticExposure`**
  (exposure to autonomous multi-step agents, distinct from copilot-style tools) —
  via an open realization-model formula. Full rubric: `pipeline/RUBRIC.md`.
- Sub-scores and one-sentence rationales are published per role; the dataset
  regenerates deterministically from per-role source files (`pipeline/roles/`).
- Historical quarters (Q1 2025 – Q2 2026) were published under methodology v1
  (50/30/20 composite) and are retained as published.
- Quarterly moves larger than ±8 points now require a stated **restatement**
  reason, recorded on the role and in the quarterly report.
- Two editorial tiers: tier 1 (~130 head roles: full insight + industry
  modifiers), tier 2 (concise insight).

### Schema (additive only)
- JSON adds: `socCode`, `tier`, `subscores`, `rationales`, `agenticRisk`,
  `salarySource`, optional `restatement`
- CSV appends columns after `score_q2_2026`: `score_q3_2026`, `soc_code`, `tier`,
  `sub_task_automation`, `sub_tool_maturity`, `sub_adoption`,
  `sub_agentic_exposure`, `agentic_risk` — existing column order unchanged
- Defense-skill links are now absolute URLs

### Infrastructure
- Interactive explorer on GitHub Pages (`site/`)
- Zero-dependency MCP server (`mcp/`) — query the dataset from any MCP client
- CI now proves the dataset regenerates deterministically from sources, runs the
  full integrity suite, and smoke-tests the MCP server
- Quarterly Winners & Losers report: `reports/2026-q3-winners-losers.md`

### Notable Q2 → Q3 movements
The v2 realization model repriced the index: roles whose v1 scores leaned on tool
hype without end-to-end automatability came down (25 of 76 existing roles fell 5+
points; four fell far enough to require formal restatements — radiologist 45→34,
healthcare administrator 42→30, lab technician 48→30, paralegal 58→48), while
AI-tooling-saturated tech roles drifted up (data scientist +8, cybersecurity
analyst +6). Mean drift across the 76 carried-over roles: −1.7 points. Full tables:
`reports/2026-q3-winners-losers.md`.

## [2026.2] — 2026-05-06

Initial public release of the dataset to GitHub. Snapshots the May 6, 2026 state.

### Coverage
- 76 roles across 10 categories
- 4 risk bands (Low / Moderate / High / Very High)
- Historical scores: Q1 2025, Q3 2025, Q1 2026, Q2 2026
- Industry modifiers: Tech, Finance, Healthcare, Government, Retail, Manufacturing

### Notable score movements (Q1 2025 → Q2 2026)
| Role | Q1 2025 | Q2 2026 | Δ | Note |
|---|---|---|---|---|
| Data Entry Clerk | 78 | 88 | +10 | OCR + agentic doc processing closing the last gap |
| Content Writer | 48 | 68 | +20 | Tied for largest increase (with Copywriter); commodity content production now AI-default |
| Tax Preparer | 58 | 72 | +14 | TurboTax-class AI handles individual returns end-to-end |
| Copywriter | 45 | 65 | +20 | Tied for largest increase (with Content Writer); AI marketing copy at scale |
| Receptionist | 60 | 75 | +15 | AI phone systems + digital check-in widespread |
| Insurance Underwriter | 52 | 68 | +16 | Personal lines fully automated |
| Tutor | 38 | 55 | +17 | Khanmigo-class tutors rolling out |
| Software Engineer | 18 | 25 | +7 | Slow rise — AI is augmentation, not replacement |
| Nurse (RN) | 12 | 18 | +6 | Documentation automation; core role unchanged |
| Mental Health Counselor | 8 | 10 | +2 | Most resilient role; barely changed |

### Methodology baseline
- Three-factor weighted composite: 50% task automation potential, 30% AI tool maturity, 20% industry adoption
- Methodology reviewed quarterly
- Score changes <5 points absorbed without band changes

## Future releases

- **2026.3** — Q3 2026 review (target: late August 2026)
  - Re-grade tasks against latest LLM and vertical-AI tool releases
  - Refresh adoption signals from updated employer surveys
  - Add 5–10 new roles based on community feedback
  - Add geographic modifier (US vs. EU vs. emerging markets)

- **2026.4** — Q4 2026 review (target: late November 2026)
  - Year-over-year cohort analysis
  - Annual research report aggregating cross-role insights
