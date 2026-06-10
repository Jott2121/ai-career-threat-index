# Changelog

All notable changes to the AI Career Threat Index dataset are documented here.
Versioning follows the format `YEAR.QUARTER` — e.g., `2026.2` is the second-quarter 2026 review.

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
