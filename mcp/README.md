# threat-index-mcp

An MCP (Model Context Protocol) server for the [AI Career Threat Index](https://github.com/Jott2121/ai-career-threat-index) —
so your AI assistant can answer "how exposed is my job to AI?" with real, versioned data
instead of vibes.

Zero dependencies. Node ≥ 18. Reads the dataset from the repo when run from a clone,
otherwise fetches it from GitHub raw — the single `server.js` file works anywhere.

## Add it to Claude Code

```bash
git clone https://github.com/Jott2121/ai-career-threat-index.git
claude mcp add threat-index -- node ./ai-career-threat-index/mcp/server.js
```

## Add it to Claude Desktop

```json
{
  "mcpServers": {
    "threat-index": {
      "command": "node",
      "args": ["/path/to/ai-career-threat-index/mcp/server.js"]
    }
  }
}
```

## Tools

| Tool | What it answers |
|---|---|
| `lookup_role` | Full record for one role: score, band, four sub-scores with rationales, tasks, defense skills, salary, history |
| `list_roles` | Roles filtered by category / risk band |
| `compare_roles` | Side-by-side comparison of 2–6 roles |
| `top_movers` | Biggest quarter-over-quarter score changes |
| `safest_roles` / `riskiest_roles` | Extremes, overall or per category |
| `crosswalk_soc` | Any BLS SOC 2018 code → nearest scored role |

Try: *"Compare paralegal, bookkeeper and welder — which is most exposed to autonomous
agents, and what should each build to defend?"*

## License

MIT, same as the dataset. Scores are structured editorial estimates against a
[published rubric](../pipeline/RUBRIC.md), not measurements.
