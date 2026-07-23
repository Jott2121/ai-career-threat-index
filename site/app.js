/* AI Career Threat Index explorer — zero dependencies.
   Data contract: ./data/ai-career-threat-index.json (copied in at deploy). */
"use strict";

const BAND_COLORS = {
  "Low": "var(--band-low)",
  "Moderate": "var(--band-moderate)",
  "High": "var(--band-high)",
  "Very High": "var(--band-veryhigh)",
};
const QUARTERS = ["Q1 2025", "Q3 2025", "Q1 2026", "Q2 2026", "Q3 2026"];
const PREV_Q = "Q2 2026";

let DATA = null;
const state = { q: "", category: "", band: "", sort: "score", dir: -1 };

const $ = (sel, el = document) => el.querySelector(sel);
const app = $("#app");
const tooltip = $("#tooltip");

const esc = (s) => String(s).replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtSalary = (n) => "$" + Math.round(n / 1000) + "k";
const midSalary = (r) => (r.salary.low + r.salary.high) / 2;
const delta = (r) => {
  const prev = r.historicalScores[PREV_Q];
  return prev === undefined ? null : r.score - prev;
};

/* ---------- theme ---------- */
function initTheme() {
  const saved = localStorage.getItem("acti-theme");
  if (saved) document.documentElement.dataset.theme = saved;
  $("#theme-toggle").addEventListener("click", () => {
    const cur = document.documentElement.dataset.theme ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("acti-theme", next);
  });
}

/* ---------- tooltip ---------- */
function showTip(html, x, y) {
  tooltip.innerHTML = html;
  tooltip.style.display = "block";
  const pad = 12;
  const w = tooltip.offsetWidth, h = tooltip.offsetHeight;
  tooltip.style.left = Math.min(x + pad, innerWidth - w - pad) + "px";
  tooltip.style.top = (y + h + pad * 2 > innerHeight ? y - h - pad : y + pad) + "px";
  tooltip.setAttribute("aria-hidden", "false");
}
function hideTip() {
  tooltip.style.display = "none";
  tooltip.setAttribute("aria-hidden", "true");
}

/* ---------- shared bits ---------- */
function bandChip(band) {
  return `<span class="band"><span class="dot" style="background:${BAND_COLORS[band]}"></span>${esc(band)}</span>`;
}

function sparkline(r, w = 90, h = 24) {
  const pts = QUARTERS.filter((q) => r.historicalScores[q] !== undefined)
    .map((q) => r.historicalScores[q]);
  if (pts.length < 2) return `<span class="chip">new</span>`;
  const min = Math.min(...pts), max = Math.max(...pts);
  const span = Math.max(max - min, 4);
  const step = w / (pts.length - 1);
  const xy = pts.map((v, i) =>
    [i * step, h - 3 - ((v - min) / span) * (h - 6)]);
  const d = xy.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const last = xy[xy.length - 1];
  return `<svg class="spark" width="${w}" height="${h}" aria-label="score history">
    <path d="${d}"/><circle cx="${last[0]}" cy="${last[1]}" r="3"/></svg>`;
}

/* ---------- list view ---------- */
function applyFilters() {
  let rows = DATA.roles.slice();
  const q = state.q.trim().toLowerCase();
  if (q) rows = rows.filter((r) =>
    r.title.toLowerCase().includes(q) || r.slug.includes(q) ||
    r.category.toLowerCase().includes(q) || r.socCode.startsWith(q));
  if (state.category) rows = rows.filter((r) => r.category === state.category);
  if (state.band) rows = rows.filter((r) => r.riskLevel === state.band);
  const key = {
    title: (r) => r.title.toLowerCase(),
    category: (r) => r.category,
    score: (r) => r.score,
    agentic: (r) => r.subscores.agenticExposure,
    salary: (r) => midSalary(r),
    delta: (r) => delta(r) ?? -999,
  }[state.sort];
  rows.sort((a, b) => {
    const ka = key(a), kb = key(b);
    return (ka < kb ? -1 : ka > kb ? 1 : 0) * state.dir;
  });
  return rows;
}

function renderSummary() {
  const counts = {};
  for (const r of DATA.roles) counts[r.riskLevel] = (counts[r.riskLevel] || 0) + 1;
  $("#summary-chips").innerHTML =
    `<span class="chip">v${esc(DATA.metadata.version)} · ${DATA.roles.length} roles</span>` +
    Object.keys(BAND_COLORS).map((b) =>
      `<span class="chip"><span class="dot" style="background:${BAND_COLORS[b]}"></span>${esc(b)}: ${counts[b] || 0}</span>`).join("");
}

function listView() {
  const cats = DATA.categories;
  const rows = applyFilters();
  const arrow = (col) => state.sort === col ? `<span class="arrow">${state.dir < 0 ? "▾" : "▴"}</span>` : "";
  app.innerHTML = `
  <div class="controls">
    <input type="search" id="search" placeholder="Search 300 roles — try 'nurse', 'welder', 'analyst'…" value="${esc(state.q)}" aria-label="Search roles">
    <select id="f-cat" aria-label="Filter by category">
      <option value="">All categories</option>
      ${cats.map((c) => `<option ${state.category === c ? "selected" : ""}>${esc(c)}</option>`).join("")}
    </select>
    <select id="f-band" aria-label="Filter by risk band">
      <option value="">All risk bands</option>
      ${Object.keys(BAND_COLORS).map((b) => `<option ${state.band === b ? "selected" : ""}>${esc(b)}</option>`).join("")}
    </select>
    <span class="count-note">${rows.length} of ${DATA.roles.length} roles</span>
  </div>
  <section class="panel">
    <h2>Risk vs. pay</h2>
    <p class="sub">Each dot is a role: displacement score (x) against salary midpoint (y). Hover for details, click to open.</p>
    ${scatterSVG(rows)}
    <div class="legend-row">${Object.keys(BAND_COLORS).map((b) =>
      `<span><span class="dot" style="display:inline-block;width:.6em;height:.6em;border-radius:50%;background:${BAND_COLORS[b]}"></span> ${esc(b)}</span>`).join("")}</div>
  </section>
  <section class="panel">
    <table class="roles">
      <thead><tr>
        <th data-sort="title">Role ${arrow("title")}</th>
        <th data-sort="category" class="hide-sm">Category ${arrow("category")}</th>
        <th data-sort="score" class="num">Score ${arrow("score")}</th>
        <th>Band</th>
        <th data-sort="agentic" class="num hide-sm" title="Exposure to autonomous agents">Agentic ${arrow("agentic")}</th>
        <th data-sort="delta" class="num hide-sm" title="Change vs Q2 2026">Δ Q2 ${arrow("delta")}</th>
        <th data-sort="salary" class="num hide-sm">Salary ${arrow("salary")}</th>
        <th class="hide-sm">Trend</th>
      </tr></thead>
      <tbody>
        ${rows.map((r) => {
          const d = delta(r);
          const dHtml = d === null ? `<span class="delta-flat">new</span>`
            : d > 0 ? `<span class="delta-up">+${d}</span>`
            : d < 0 ? `<span class="delta-down">${d}</span>`
            : `<span class="delta-flat">0</span>`;
          return `<tr data-slug="${esc(r.slug)}">
          <td>${esc(r.title)}</td>
          <td class="hide-sm">${esc(r.category)}</td>
          <td class="num"><span class="scorebar"><i style="width:${r.score}%;background:${BAND_COLORS[r.riskLevel]}"></i></span>${r.score}</td>
          <td>${bandChip(r.riskLevel)}</td>
          <td class="num hide-sm">${r.subscores.agenticExposure}</td>
          <td class="num hide-sm">${dHtml}</td>
          <td class="num hide-sm">${fmtSalary(r.salary.low)}–${fmtSalary(r.salary.high)}</td>
          <td class="hide-sm">${sparkline(r)}</td>
        </tr>`;
        }).join("")}
      </tbody>
    </table>
  </section>`;

  $("#search").addEventListener("input", (e) => { state.q = e.target.value; listView(); $("#search").focus(); const v = $("#search").value; $("#search").setSelectionRange(v.length, v.length); });
  $("#f-cat").addEventListener("change", (e) => { state.category = e.target.value; listView(); });
  $("#f-band").addEventListener("change", (e) => { state.band = e.target.value; listView(); });
  app.querySelectorAll("th[data-sort]").forEach((th) =>
    th.addEventListener("click", () => {
      const col = th.dataset.sort;
      if (state.sort === col) state.dir *= -1;
      else { state.sort = col; state.dir = col === "title" || col === "category" ? 1 : -1; }
      listView();
    }));
  app.querySelectorAll("tbody tr").forEach((tr) =>
    tr.addEventListener("click", () => { location.hash = "#/role/" + tr.dataset.slug; }));
  wireScatter();
}

function scatterSVG(rows) {
  const W = 1000, H = 380, m = { t: 16, r: 20, b: 42, l: 64 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const maxSal = Math.max(...DATA.roles.map(midSalary)) * 1.05;
  const x = (v) => m.l + (v / 100) * iw;
  const y = (v) => m.t + ih - (v / maxSal) * ih;
  const gridX = [0, 25, 50, 75, 100];
  const salStep = maxSal > 300000 ? 100000 : 50000;
  const gridY = [];
  for (let v = 0; v <= maxSal; v += salStep) gridY.push(v);
  return `<svg class="scatter" viewBox="0 0 ${W} ${H}" role="img" aria-label="Scatter of risk score versus salary midpoint">
    ${gridY.map((v) => `<line class="grid" x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}"/>
      <text x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end">${fmtSalary(v)}</text>`).join("")}
    ${gridX.map((v) => `<line class="grid" y1="${m.t}" y2="${m.t + ih}" x1="${x(v)}" x2="${x(v)}"/>
      <text x="${x(v)}" y="${H - m.b + 18}" text-anchor="middle">${v}</text>`).join("")}
    <line class="axis" x1="${m.l}" x2="${W - m.r}" y1="${m.t + ih}" y2="${m.t + ih}"/>
    <line class="axis" x1="${m.l}" x2="${m.l}" y1="${m.t}" y2="${m.t + ih}"/>
    <text class="axis-label" x="${m.l + iw / 2}" y="${H - 6}" text-anchor="middle">AI displacement score (higher = more exposed)</text>
    <text class="axis-label" transform="rotate(-90 14 ${m.t + ih / 2})" x="14" y="${m.t + ih / 2}" text-anchor="middle">Salary midpoint (USD)</text>
    ${rows.map((r) => `<circle data-slug="${esc(r.slug)}" cx="${x(r.score).toFixed(1)}" cy="${y(midSalary(r)).toFixed(1)}" r="6" fill="${BAND_COLORS[r.riskLevel]}"/>`).join("")}
  </svg>`;
}

function wireScatter() {
  app.querySelectorAll(".scatter circle").forEach((c) => {
    const r = DATA.roles.find((x) => x.slug === c.dataset.slug);
    c.addEventListener("mousemove", (e) =>
      showTip(`<b>${esc(r.title)}</b><span class="t2">Score ${r.score} · ${esc(r.riskLevel)} · ${fmtSalary(r.salary.low)}–${fmtSalary(r.salary.high)}</span>`, e.clientX, e.clientY));
    c.addEventListener("mouseleave", hideTip);
    c.addEventListener("click", () => { hideTip(); location.hash = "#/role/" + r.slug; });
  });
}

/* ---------- detail view ---------- */
const SUB_LABELS = {
  taskAutomation: "Task automation potential",
  toolMaturity: "AI tool maturity",
  adoption: "Employer adoption",
  agenticExposure: "Agentic exposure",
};

function historyChart(r) {
  const qs = QUARTERS.filter((q) => r.historicalScores[q] !== undefined);
  if (qs.length < 2) return `<p class="sub">New this quarter — history starts ${esc(qs[0] || "Q3 2026")}.</p>`;
  const W = 460, H = 150, m = { t: 12, r: 16, b: 26, l: 30 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const vals = qs.map((q) => r.historicalScores[q]);
  const lo = Math.max(0, Math.min(...vals) - 5), hi = Math.min(100, Math.max(...vals) + 5);
  const x = (i) => m.l + (i / (qs.length - 1)) * iw;
  const y = (v) => m.t + ih - ((v - lo) / (hi - lo)) * ih;
  const d = vals.map((v, i) => (i ? "L" : "M") + x(i).toFixed(1) + " " + y(v).toFixed(1)).join(" ");
  return `<svg class="history-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Quarterly score history">
    <line class="axis" x1="${m.l}" x2="${W - m.r}" y1="${m.t + ih}" y2="${m.t + ih}"/>
    <path d="${d}"/>
    ${vals.map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="4"><title>${esc(qs[i])}: ${v}</title></circle>
      <text x="${x(i)}" y="${H - 8}" text-anchor="middle">${esc(qs[i].replace(" 20", " '"))}</text>
      <text x="${x(i)}" y="${y(v) - 8}" text-anchor="middle">${v}</text>`).join("")}
  </svg>`;
}

function detailView(slug) {
  const r = DATA.roles.find((x) => x.slug === slug);
  if (!r) { app.innerHTML = `<p class="pad">Role not found. <a href="#/">Back to all roles</a></p>`; return; }
  const d = delta(r);
  const dTxt = d === null ? "new this quarter"
    : (d > 0 ? `+${d}` : d) + " vs Q2 2026";
  document.title = `${r.title} — AI Career Threat Index`;
  app.innerHTML = `
  <a class="backlink" href="#/">← All 300 roles</a>
  <section class="panel">
    <div class="detail-head">
      <h2>${esc(r.title)}</h2>
      ${bandChip(r.riskLevel)}
      <span class="chip">${esc(r.category)}</span>
      <span class="chip">SOC ${esc(r.socCode)}</span>
    </div>
    <div class="hero-row">
      <div class="hero-block">
        <div class="score-hero" style="color:${BAND_COLORS[r.riskLevel]}">${r.score}</div>
        <div class="lbl">displacement score · ${esc(dTxt)}</div>
      </div>
      <div class="hero-block">
        <div class="score-hero">${r.subscores.agenticExposure}</div>
        <div class="lbl">agentic exposure · ${esc(r.agenticRisk)} ${bandDotInline(r.agenticRisk)}</div>
      </div>
      <div class="hero-block">
        <div class="score-hero">${fmtSalary(r.salary.low)}–${fmtSalary(r.salary.high)}</div>
        <div class="lbl">${esc(r.salaryTrend)} · ${esc(r.salarySource || "")}</div>
      </div>
    </div>
    <div class="insight-block">${esc(r.insight)}</div>
    ${r.restatement ? `<p class="sub">Restated this quarter: ${esc(r.restatement)}</p>` : ""}
  </section>

  <section class="panel">
    <h2>How the score decomposes</h2>
    <p class="sub">score = taskAutomation × (0.45 + 0.30·toolMaturity/100 + 0.25·adoption/100) + 0.10·agenticExposure —
      <a href="https://github.com/Jott2121/ai-career-threat-index/blob/main/pipeline/RUBRIC.md">full rubric</a></p>
    <div class="subscores">
      ${Object.keys(SUB_LABELS).map((k) => `
      <div class="subscore">
        <div class="lbl"><span>${SUB_LABELS[k]}</span><b>${r.subscores[k]}</b></div>
        <div class="bar"><i style="width:${r.subscores[k]}%"></i></div>
        <div class="why">${esc(r.rationales?.[k] || "")}</div>
      </div>`).join("")}
    </div>
  </section>

  <div class="two-col">
    <section class="panel">
      <h2>Tasks AI handles today</h2>
      <ul class="tasklist">${r.tasksAtRisk.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
    </section>
    <section class="panel">
      <h2>Tasks gaining value</h2>
      <ul class="tasklist">${r.tasksGrowing.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
    </section>
  </div>

  <section class="panel">
    <h2>Score history</h2>
    ${historyChart(r)}
  </section>

  <div class="two-col">
    <section class="panel">
      <h2>Defense skills</h2>
      <p class="sub">The three highest-leverage skills to build for this role right now.</p>
      <div class="skills">${r.defenseSkills.map((s) => {
        const safe = /^https?:\/\//.test(s.link) ? s.link : "https://www.meritforgeai.com" + s.link;
        return `<a class="skill-chip" href="${esc(safe)}">${esc(s.skill)}</a>`;
      }).join("")}</div>
    </section>
    <section class="panel">
      <h2>Details</h2>
      <table class="meta-table">
        <tr><td>Category</td><td>${esc(r.category)}</td></tr>
        <tr><td>SOC code</td><td>${esc(r.socCode)}</td></tr>
        <tr><td>Salary anchor</td><td>${esc(r.salarySource || "—")}</td></tr>
        ${r.industryModifiers ? `<tr><td>Industry modifiers</td><td>${esc(Object.entries(r.industryModifiers).map(([k, v]) => `${k} ${v > 0 ? "+" + v : v}`).join(" · "))}</td></tr>` : ""}
      </table>
      <div class="share-row"><button id="copy-link">Copy share link</button></div>
    </section>
  </div>`;
  $("#copy-link").addEventListener("click", async (e) => {
    await navigator.clipboard.writeText(location.href);
    e.target.textContent = "Copied ✓";
    setTimeout(() => { e.target.textContent = "Copy share link"; }, 1500);
  });
  scrollTo(0, 0);
}

function bandDotInline(band) {
  return `<span style="display:inline-block;width:.55em;height:.55em;border-radius:50%;background:${BAND_COLORS[band]}"></span>`;
}

/* ---------- routing & boot ---------- */
function route() {
  const h = location.hash;
  const m = h.match(/^#\/role\/([a-z0-9-]+)/);
  hideTip();
  if (m) detailView(m[1]);
  else { document.title = "AI Career Threat Index — 300 roles, scored quarterly"; listView(); }
}

async function boot() {
  initTheme();
  try {
    DATA = await fetch("./data/ai-career-threat-index.json").then((r) => r.json());
  } catch (e) {
    app.innerHTML = `<p class="pad">Could not load the dataset. Get it directly from
      <a href="https://github.com/Jott2121/ai-career-threat-index">GitHub</a>.</p>`;
    return;
  }
  renderSummary();
  route();
  addEventListener("hashchange", route);
}
boot();
