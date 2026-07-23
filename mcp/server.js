#!/usr/bin/env node
/* AI Career Threat Index — MCP server (stdio, zero dependencies).
 *
 * Lets any MCP client (Claude Desktop, Claude Code, etc.) query the dataset:
 *   claude mcp add threat-index -- node /path/to/repo/mcp/server.js
 *
 * Data resolution: ../data/*.{json,csv} relative to this file when run from a
 * clone; otherwise fetched once from the GitHub raw URLs, so this single file
 * works anywhere Node >= 18 does.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const readline = require("readline");

const RAW = "https://raw.githubusercontent.com/Jott2121/ai-career-threat-index/main/data/";
const LOCAL = path.join(__dirname, "..", "data");
const PREV_Q = "Q2 2026";

let dataset = null;
let crosswalk = null; // soc_code -> row

function parseCsv(text) {
  const rows = [];
  let row = [], field = "", inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(field); field = "";
      if (row.length > 1 || row[0] !== "") rows.push(row);
      row = [];
    } else field += c;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const [head, ...rest] = rows;
  return rest.map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

async function loadText(name) {
  const local = path.join(LOCAL, name);
  if (fs.existsSync(local)) return fs.readFileSync(local, "utf8");
  const res = await fetch(RAW + name);
  if (!res.ok) throw new Error(`fetch ${name}: HTTP ${res.status}`);
  return res.text();
}

async function ensureData() {
  if (!dataset) dataset = JSON.parse(await loadText("ai-career-threat-index.json"));
  return dataset;
}
async function ensureCrosswalk() {
  if (!crosswalk) {
    const rows = parseCsv(await loadText("soc-crosswalk.csv"));
    crosswalk = new Map(rows.map((r) => [r.soc_code, r]));
  }
  return crosswalk;
}

function compact(r) {
  return {
    slug: r.slug, title: r.title, category: r.category, socCode: r.socCode,
    score: r.score, riskLevel: r.riskLevel,
    agenticExposure: r.subscores.agenticExposure, agenticRisk: r.agenticRisk,
    salaryRange: r.salaryRange, salaryTrend: r.salaryTrend,
  };
}
function full(r) {
  const prev = r.historicalScores[PREV_Q];
  return { ...r, deltaVsPreviousQuarter: prev === undefined ? null : r.score - prev };
}
function findRole(roles, query) {
  const q = String(query).toLowerCase().trim();
  return roles.find((r) => r.slug === q)
    || roles.find((r) => r.title.toLowerCase() === q)
    || roles.find((r) => r.title.toLowerCase().includes(q) || r.slug.includes(q.replace(/\s+/g, "-")));
}

const TOOLS = [
  {
    name: "lookup_role",
    description: "Look up one profession's full AI displacement record: 0-100 score, risk band, the four published sub-scores with rationales (task automation, tool maturity, adoption, agentic exposure), tasks at risk, tasks gaining value, defense skills, salary range, quarterly score history.",
    inputSchema: { type: "object", properties: { query: { type: "string", description: "Role title, slug, or partial name, e.g. 'paralegal' or 'truck driver'" } }, required: ["query"] },
  },
  {
    name: "list_roles",
    description: "List roles, optionally filtered by category and/or risk band, sorted by score (most exposed first). Categories: Technology, Business & Finance, Marketing & Sales, Administrative & Operations, Healthcare, Legal, Education, Creative, HR & Recruiting, Project & Product Management, Skilled Trades & Construction, Transportation & Logistics, Hospitality, Food & Personal Service, Science & Engineering, Public Service & Safety.",
    inputSchema: { type: "object", properties: {
      category: { type: "string" },
      riskLevel: { type: "string", enum: ["Low", "Moderate", "High", "Very High"] },
      limit: { type: "number", description: "Max results (default 25)" } } },
  },
  {
    name: "compare_roles",
    description: "Compare two or more roles side by side: scores, sub-scores, salary, trajectory.",
    inputSchema: { type: "object", properties: { queries: { type: "array", items: { type: "string" }, description: "2-6 role titles or slugs" } }, required: ["queries"] },
  },
  {
    name: "top_movers",
    description: "Roles whose displacement score moved most since last quarter (Q2 2026 -> Q3 2026).",
    inputSchema: { type: "object", properties: { direction: { type: "string", enum: ["up", "down"], description: "up = risk rising (default)" }, limit: { type: "number" } } },
  },
  {
    name: "safest_roles",
    description: "The most AI-resilient roles (lowest displacement scores), optionally within a category.",
    inputSchema: { type: "object", properties: { category: { type: "string" }, limit: { type: "number" } } },
  },
  {
    name: "riskiest_roles",
    description: "The most AI-exposed roles (highest displacement scores), optionally within a category.",
    inputSchema: { type: "object", properties: { category: { type: "string" }, limit: { type: "number" } } },
  },
  {
    name: "crosswalk_soc",
    description: "Map any BLS SOC 2018 occupation code (e.g. '47-2111') to the nearest scored role in the index, with match quality.",
    inputSchema: { type: "object", properties: { soc_code: { type: "string" } }, required: ["soc_code"] },
  },
];

async function callTool(name, args = {}) {
  const d = await ensureData();
  const roles = d.roles;
  switch (name) {
    case "lookup_role": {
      const r = findRole(roles, args.query || "");
      if (!r) return { error: `No role matching '${args.query}'. Try list_roles or a broader term.` };
      return full(r);
    }
    case "list_roles": {
      let rows = roles;
      if (args.category) rows = rows.filter((r) => r.category.toLowerCase() === String(args.category).toLowerCase());
      if (args.riskLevel) rows = rows.filter((r) => r.riskLevel === args.riskLevel);
      return { count: rows.length, roles: rows.sort((a, b) => b.score - a.score).slice(0, args.limit || 25).map(compact) };
    }
    case "compare_roles": {
      const found = (args.queries || []).map((q) => {
        const r = findRole(roles, q);
        return r ? full(r) : { error: `no match for '${q}'` };
      });
      return { comparison: found };
    }
    case "top_movers": {
      const moved = roles
        .filter((r) => r.historicalScores[PREV_Q] !== undefined)
        .map((r) => ({ ...compact(r), delta: r.score - r.historicalScores[PREV_Q] }));
      const dir = args.direction === "down" ? 1 : -1;
      moved.sort((a, b) => (a.delta - b.delta) * dir);
      return { movers: moved.slice(0, args.limit || 10) };
    }
    case "safest_roles":
    case "riskiest_roles": {
      let rows = roles;
      if (args.category) rows = rows.filter((r) => r.category.toLowerCase() === String(args.category).toLowerCase());
      const sorted = rows.slice().sort((a, b) => name === "safest_roles" ? a.score - b.score : b.score - a.score);
      return { roles: sorted.slice(0, args.limit || 10).map(compact) };
    }
    case "crosswalk_soc": {
      const xw = await ensureCrosswalk();
      const row = xw.get(String(args.soc_code).trim());
      if (!row) return { error: `SOC code '${args.soc_code}' not found in the SOC 2018 taxonomy.` };
      const role = roles.find((r) => r.slug === row.nearest_role_slug);
      return { soc: row, nearestRole: role ? full(role) : null };
    }
    default:
      throw { code: -32601, message: `Unknown tool: ${name}` };
  }
}

/* ---- MCP stdio plumbing (newline-delimited JSON-RPC 2.0) ---- */
function send(msg) { process.stdout.write(JSON.stringify(msg) + "\n"); }

const rl = readline.createInterface({ input: process.stdin, terminal: false });
rl.on("line", async (line) => {
  line = line.trim();
  if (!line) return;
  let msg;
  try { msg = JSON.parse(line); } catch { return; }
  if (msg.method === undefined) return;            // ignore responses
  const { id, method, params } = msg;
  const reply = (result) => id !== undefined && send({ jsonrpc: "2.0", id, result });
  const fail = (code, message) => id !== undefined && send({ jsonrpc: "2.0", id, error: { code, message } });
  try {
    if (method === "initialize") {
      reply({
        protocolVersion: params?.protocolVersion || "2025-06-18",
        capabilities: { tools: {} },
        serverInfo: { name: "ai-career-threat-index", version: "2026.3.0" },
      });
    } else if (method === "notifications/initialized" || method.startsWith("notifications/")) {
      /* no-op */
    } else if (method === "ping") {
      reply({});
    } else if (method === "tools/list") {
      reply({ tools: TOOLS });
    } else if (method === "tools/call") {
      const out = await callTool(params.name, params.arguments || {});
      reply({ content: [{ type: "text", text: JSON.stringify(out, null, 2) }], isError: !!out?.error });
    } else {
      fail(-32601, `Method not found: ${method}`);
    }
  } catch (e) {
    fail(e.code || -32000, e.message || String(e));
  }
});
rl.on("close", () => process.exit(0));
