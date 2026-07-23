# Scoring rubric — methodology v2 (effective Q3 2026)

Every role's 0–100 displacement score is computed from four published sub-scores.
Sub-scores are **structured editorial estimates**: expert judgments made against the
anchors below, informed by O*NET task lists, public AI capability evidence, and
adoption research. They are not measurements, and we don't claim otherwise.

## The formula (realization model)

```
realization = 0.45 + 0.30 · (toolMaturity / 100) + 0.25 · (adoption / 100)
score       = clamp( round( taskAutomation · realization + 0.10 · agenticExposure ), 0, 100 )
```

Rationale: **task automation potential sets the ceiling** — you cannot be displaced
from work AI can't do. **Tool maturity** and **employer adoption** determine how much
of that ceiling is realized today (a role whose tasks are automatable in principle
but with immature, unadopted tooling realizes only ~45% of its ceiling).
**Agentic exposure** adds forward pressure from autonomous multi-step agents that is
not yet fully reflected in shipped tools.

Methodology v1 (through Q2 2026) was a 50/30/20 weighted composite without the
agentic factor. Historical quarterly scores are retained as published under v1;
Q3 2026 is the first v2 quarter. Where honest v2 sub-scores force a move of more
than ±8 points from Q2 2026, the move is flagged as a **restatement** in the
changelog with a reason, rather than silently absorbed.

## Sub-score anchors

### taskAutomation (0–100)
Share of the role's core work-hours that current AI could perform **end-to-end at
professional quality with ≥90% reliability** — not merely assist with.

- **0–10**: Work is dominated by physical dexterity in unstructured environments,
  in-person presence, or licensed physical acts (plumber, dental hygienist, firefighter).
- **11–25**: Mostly physical/interpersonal with a modest digital-paperwork share
  (electrician, registered nurse, chef).
- **26–45**: Substantial digital component but judgment, liability, or relationships
  gate most tasks (software engineer, accountant, teacher, financial analyst).
- **46–65**: Half or more of core output is drafting, processing, matching, or
  summarizing digital information (paralegal, bookkeeper, translator, copywriter).
- **66–85**: Role output is predominantly routine digital production or scripted
  interaction (data entry clerk, telemarketer, basic customer-service chat).
- **86–100**: Reserved; essentially fully automatable output. Rarely used.

### toolMaturity (0–100)
How mature and production-deployed the AI tools targeting this role's automatable
tasks are (quality, reliability, integration into the role's actual toolchain).

- **0–20**: Little to no purpose-built tooling; research demos only.
- **21–45**: Generic LLM tools apply but nothing role-specific has traction.
- **46–70**: Credible role-specific products exist and are improving fast.
- **71–90**: Mature, widely-shipped products embedded in the standard toolchain
  (coding copilots, transcription, translation, image generation).
- **91–100**: Commodity, near-solved capability.

### adoption (0–100)
Share of US employers of this role actively using AI for the automatable tasks
(not pilots or policy memos — actual production use affecting workflows).

- **0–15**: Rare; regulated, unionized, or conservative sectors.
- **16–35**: Early adopters only.
- **36–60**: Common in large firms and tech-forward sectors, spreading to mid-market.
- **61–80**: Mainstream expectation for the function (mid-2026: marketing content,
  customer support deflection, code assistance).
- **81–100**: Near-universal.

### agenticExposure (0–100)
Share of the role's work that **autonomous multi-step agents** (plan → act → verify
loops with tool use, not chat copilots) could credibly own within current frontier
capability. This is the forward-pressure factor: what changes when AI stops
assisting and starts owning workflows end-to-end.

- **0–10**: Physical-world work; agents don't reach it (trades, patient care).
- **11–30**: Isolated back-office slices could be agent-owned (scheduling,
  documentation, ordering) but the core role can't be.
- **31–55**: Meaningful workflows are agent-ownable today or within a product cycle:
  research-summarize-draft loops, triage queues, reconciliations, test maintenance.
- **56–80**: The role is substantially a pipeline of digital decisions and handoffs
  an agent can traverse (claims processing, order management, routine scheduling
  and dispatch, tier-1 support).
- **81–100**: The role is effectively an agent spec (bulk data operations,
  scripted outreach).

## Calibration examples (v2, Q3 2026)

| Role | TA | TM | AD | AG | → score | note |
|---|---|---|---|---|---|---|
| Software Engineer | 28 | 82 | 62 | 42 | 28·(0.45+0.246+0.155)+4.2 ≈ **28** | continuity with Q2 (25) |
| Data Entry Clerk | 88 | 85 | 65 | 82 | 88·(0.45+0.255+0.1625)+8.2 ≈ **84** | Very High |
| Paralegal | 52 | 74 | 55 | 55 | 52·(0.45+0.222+0.1375)+5.5 ≈ **48** | Moderate |
| Registered Nurse | 12 | 55 | 40 | 12 | 12·(0.45+0.165+0.10)+1.2 ≈ **10** | Low |
| Copywriter | 60 | 88 | 70 | 50 | 60·(0.45+0.264+0.175)+5 ≈ **58** | High |
| Plumber | 6 | 35 | 18 | 6 | 6·(0.45+0.105+0.045)+0.6 ≈ **4** | Low |

## Risk bands and hysteresis

Low 0–35 · Moderate 36–50 · High 51–75 · Very High 76–100.
A role whose new score lands within 5 points of a band boundary retains its prior
band (stability rule, applied mechanically by `score.py`).

`agenticRisk` band uses the same cut points applied to `agenticExposure`.

## Salary anchoring

Salary ranges approximate the p25–p75 spread of BLS OES published estimates for the
role's SOC occupation (national, latest release), rounded to the nearest $5k, with
an upward allowance for head roles where market postings clearly exceed OES
(e.g., senior tech). `salarySource` on each role records the anchor used.

## Sources

- O*NET 29.1 database — task lists and occupation definitions (occupation reference
  vendored at `pipeline/reference/onet_occupations.txt`)
- BLS Occupational Employment and Wage Statistics (OES), latest national release
- BLS SOC 2018 occupation taxonomy (derived reference at
  `pipeline/reference/soc_2018_detailed.csv`)
- Public adoption research: WEF Future of Jobs, McKinsey State of AI, BCG,
  Gallup workplace AI surveys, Anthropic Economic Index
- Public AI capability evidence: model cards, benchmark reports, shipped product
  capabilities as of mid-2026
