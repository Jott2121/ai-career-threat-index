# AI Career Threat Index

> Open dataset of AI displacement risk for 76 professions. Three-factor methodology, quarterly review, MIT licensed.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Roles](https://img.shields.io/badge/Roles-76-blue)
![Categories](https://img.shields.io/badge/Categories-10-blue)
![Updated](https://img.shields.io/badge/Updated-2026--05--06-green)
![Version](https://img.shields.io/badge/Version-2026.2-green)
[![HF Dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Dataset-yellow)](https://huggingface.co/datasets/Jott2121/ai-career-threat-index)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21227026.svg)](https://doi.org/10.5281/zenodo.21227026)

The **AI Career Threat Index** is a structured dataset that scores 76 professions on AI displacement risk. Each role is decomposed into representative tasks, mapped against current AI capability, and weighted by industry adoption rate to produce a 0–100 score.

This is the canonical data repository. The interactive tool, full methodology, citation snippets, and per-role deep dives live at **[meritforgeai.com](https://www.meritforgeai.com/data/ai-career-threat-index/)**.

## Why this dataset exists

Most discussion of AI and jobs is anecdotal. This dataset gives one numeric answer per role plus a structured breakdown of the tasks driving the score. It's intended for journalists, researchers, career coaches, HR teams, and developers building career-related applications.

Intended use cases:
- Editorial pieces citing displacement risk by occupation
- HR workforce planning models
- Resume-tool integrations that show users their role's risk
- Academic research on AI labor-market impact
- Personal career-strategy decisions

## Quick start

### Download

```bash
# JSON (full dataset)
curl -O https://www.meritforgeai.com/data/ai-career-threat-index.json

# CSV (flat table, one row per role)
curl -O https://www.meritforgeai.com/data/ai-career-threat-index.csv

# This repo (versioned)
git clone https://github.com/Jott2121/ai-career-threat-index.git
```

### Use it in code

**Python:**
```python
import requests
data = requests.get("https://www.meritforgeai.com/data/ai-career-threat-index.json").json()

# Find the most resilient role
lowest = min(data["roles"], key=lambda r: r["score"])
print(f"Most AI-resilient: {lowest['title']} ({lowest['score']}/100)")

# Filter by risk band
high_risk = [r for r in data["roles"] if r["riskLevel"] in ("High", "Very High")]
print(f"{len(high_risk)} roles in High or Very High risk")
```

**JavaScript:**
```javascript
const data = await fetch('https://www.meritforgeai.com/data/ai-career-threat-index.json').then(r => r.json());

// All roles in a category, sorted by score
const techRoles = data.roles
  .filter(r => r.category === 'Technology')
  .sort((a, b) => b.score - a.score);
```

**R:**
```r
library(jsonlite)
data <- fromJSON("https://www.meritforgeai.com/data/ai-career-threat-index.json", flatten = TRUE)
roles <- data$roles
mean(roles$score)  # mean displacement score across all roles
```

More examples in [`examples/`](examples/).

## Schema

Each role record has the following fields:

| Field | Type | Description |
|---|---|---|
| `slug` | string | URL-safe identifier (e.g., `software-engineer`) |
| `title` | string | Role display name |
| `category` | string | One of 10 broad role families |
| `score` | integer 0–100 | AI displacement risk; higher = more exposed |
| `riskLevel` | enum | `Low` (0–35), `Moderate` (36–50), `High` (51–75), `Very High` (76–100) |
| `tasksAtRisk` | string[] | Tasks AI handles today with ≥90% reliability |
| `tasksGrowing` | string[] | Tasks gaining value as AI displaces routine work |
| `salaryRange` | string | Display-formatted USD range |
| `salary` | object | `{ low, high, currency }` parsed numeric range |
| `salaryTrend` | enum | `rising` \| `stable` \| `mixed` \| `declining` |
| `defenseSkills` | object[] | Top three skills to build for this role: `[{ skill, link }]` |
| `insight` | string | Headline finding (one paragraph) |
| `historicalScores` | object | Quarterly scoring snapshots: `{ "Q1 2025": 18, ... }` |
| `industryModifiers` | object | Per-industry score adjustments: `{ "Tech": 5, "Government": -10, ... }` |

Note: scores within 5 points of a band boundary may retain their prior band across quarterly reviews for stability.

Top-level structure:

```json
{
  "metadata": { "name": "...", "version": "2026.2", "lastUpdated": "2026-05-06", ... },
  "categories": ["Technology", "Business & Finance", ...],
  "roles": [ /* 76 role records */ ]
}
```

## Methodology

The 0–100 score is a weighted composite of three factors:

1. **Task automation potential (50%)**: Percentage of the role's tasks current AI can perform with ≥90% reliability
2. **AI tool maturity (30%)**: Maturity and deployment of relevant AI capabilities
3. **Industry adoption rate (20%)**: Percentage of employers actively using AI for those tasks

Sources: O*NET task lists, public AI capability benchmarks, employer surveys (BCG, Gallup, WEF, McKinsey), job posting analytics, BLS Occupational Employment Statistics.

Reviewed quarterly. Mid-quarter changes <5 points absorbed without band changes to avoid noise.

**Full methodology**: [meritforgeai.com/methodology/threat-index/](https://www.meritforgeai.com/methodology/threat-index/)

## Data files

- [`data/ai-career-threat-index.json`](data/ai-career-threat-index.json): Full dataset, structured
- [`data/ai-career-threat-index.csv`](data/ai-career-threat-index.csv): Flat table, one row per role
- [`data/changelog.md`](data/changelog.md): Version history and notable score movements

## Examples

The [`examples/`](examples/) directory contains starter code for common use cases:

- `python-analysis.py`: Risk-band aggregation, salary-trend correlations
- `js-fetch.html`: Browser-side fetch and rendering
- `r-correlation.R`: Salary range vs. risk score correlation analysis

## License

[MIT License](LICENSE). Commercial use permitted with attribution.

When citing in editorial content, please link to MeritForge AI on first mention. Suggested citation:

```
The MeritForge Team (2026). AI Career Threat Index. MeritForge AI.
https://www.meritforgeai.com/data/ai-career-threat-index/
```

BibTeX, Chicago, and additional formats: [press kit](https://www.meritforgeai.com/press/).

## Contributing

Found an error? Disagree with a score? Have access to better adoption-rate data for an industry?

- Open a GitHub issue describing what you've spotted
- Or open a pull request with a proposed fix
- Or email <feedback@meritforgeai.com>

Methodology refinements get incorporated into the next quarterly review with attribution where appropriate.

## About

Maintained by [The MeritForge Team](https://www.meritforgeai.com/about/), an independent research group publishing AI career intelligence at [MeritForge AI](https://www.meritforgeai.com). Methodology reviewed quarterly.

The dataset combines labor-market data with structured, transparent methodology, closer to the way the World Economic Forum's Future of Jobs report or PwC's automation studies work than to a black-box ML model.

## Related links

- 🌐 [MeritForge AI website](https://www.meritforgeai.com)
- 🧪 [Use the interactive Threat Index tool](https://www.meritforgeai.com/tools/ai-career-threat-index/)
- 📊 [Dataset landing page](https://www.meritforgeai.com/data/ai-career-threat-index/)
- 📐 [Full methodology](https://www.meritforgeai.com/methodology/threat-index/)
- 📰 [Press kit & citation snippets](https://www.meritforgeai.com/press/)

---

⭐ **If this dataset was useful, please star this repo.** Stars help researchers and journalists find the dataset.

Built and maintained by [Jeff Otterson](https://github.com/Jott2121)
