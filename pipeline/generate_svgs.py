#!/usr/bin/env python3
"""Generate the README charts as static SVGs from the published dataset.

Emits  assets/risk-distribution.svg   — score histogram, colored by risk band
       assets/top-movers.svg          — biggest Q2->Q3 movers, diverging bars
       assets/agentic-heat.svg        — mean agentic exposure by category

Deterministic, stdlib only. Colors are the validated reference palette's status
colors (band identity is always also carried by a text label, never color alone)
and its muted ink #898781, which stays legible on GitHub's light and dark
backgrounds. Run: python3 pipeline/generate_svgs.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
PREV_Q = "Q2 2026"

BAND_COLOR = {"Low": "#0ca30c", "Moderate": "#fab219",
              "High": "#ec835a", "Very High": "#d03b3b"}
INK = "#898781"          # muted ink — legible on light and dark
ACCENT = "#3987e5"       # series blue (dark-mode step; fine on both)
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
FONT = 'font-family="system-ui,-apple-system,Segoe UI,sans-serif"'


def band_of(score):
    for name, hi in (("Low", 35), ("Moderate", 50), ("High", 75)):
        if score <= hi:
            return name
    return "Very High"


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" {FONT}>\n{body}\n</svg>\n')


def text(x, y, s, size=12, anchor="start", color=INK, bold=False):
    weight = ' font-weight="600"' if bold else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}"{weight}>{s}</text>')


def distribution(roles):
    W, H, mb, ml = 720, 240, 40, 36
    bins = [0] * 10
    for r in roles:
        bins[min(r["score"] // 10, 9)] += 1
    top = max(bins)
    iw, ih = W - ml - 16, H - mb - 28
    bw = iw / 10
    parts = [text(ml, 16, f"Score distribution — {len(roles)} roles", 14, bold=True)]
    for i, n in enumerate(bins):
        x = ml + i * bw
        bh = 0 if top == 0 else n / top * ih
        color = BAND_COLOR[band_of(i * 10 + 5)]
        parts.append(f'<rect x="{x + 3:.1f}" y="{28 + ih - bh:.1f}" width="{bw - 6:.1f}" '
                     f'height="{max(bh, 1):.1f}" rx="4" fill="{color}"/>')
        if n:
            parts.append(text(x + bw / 2, 28 + ih - bh - 5, str(n), 11, "middle"))
        parts.append(text(x + bw / 2, H - mb + 16, f"{i * 10}", 10, "middle"))
    parts.append(f'<line x1="{ml}" y1="{28 + ih}" x2="{W - 16}" y2="{28 + ih}" '
                 f'stroke="{INK}" stroke-opacity="0.4"/>')
    y = H - 6
    x = ml
    for band, color in BAND_COLOR.items():
        parts.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{color}"/>')
        parts.append(text(x + 14, y, band, 11))
        x += 24 + 7 * len(band)
    return svg(W, H, "\n".join(parts))


def movers(roles):
    moved = [(r, r["score"] - r["historicalScores"][PREV_Q])
             for r in roles if PREV_Q in r["historicalScores"]]
    moved = [m for m in moved if m[1] != 0]
    up = sorted(moved, key=lambda m: -m[1])[:6]
    down = sorted(moved, key=lambda m: m[1])[:4]
    rows = up + [d for d in down if d[1] < 0]
    W, rh = 720, 26
    H = 40 + len(rows) * rh + 8
    mid = 400
    scale = 18
    parts = [text(24, 20, "Biggest movers, Q2 → Q3 2026", 14, bold=True)]
    for i, (r, d) in enumerate(rows):
        y = 40 + i * rh
        w = abs(d) * scale
        color = "#d03b3b" if d > 0 else "#0ca30c"
        x = mid if d > 0 else mid - w
        parts.append(f'<rect x="{x}" y="{y}" width="{max(w, 2)}" height="16" rx="4" fill="{color}"/>')
        parts.append(text(mid - (8 if d > 0 else w + 8), y + 12, r["title"], 12,
                          "end"))
        parts.append(text(mid + (w + 8 if d > 0 else 8), y + 12,
                          f"{d:+d}", 12, "start", color, bold=True))
    parts.append(f'<line x1="{mid}" y1="34" x2="{mid}" y2="{H - 8}" '
                 f'stroke="{INK}" stroke-opacity="0.4"/>')
    return svg(W, H, "\n".join(parts))


def agentic_heat(doc):
    cats = doc["categories"]
    roles = doc["roles"]
    W, rh, ml = 720, 24, 250
    H = 36 + len(cats) * rh + 30
    iw = W - ml - 70
    means = []
    for c in cats:
        vals = [r["subscores"]["agenticExposure"] for r in roles if r["category"] == c]
        means.append((c, sum(vals) / len(vals) if vals else 0))
    means.sort(key=lambda m: -m[1])
    top = max(m[1] for m in means)
    parts = [text(24, 20, "Exposure to autonomous agents — category average (0–100)", 14, bold=True)]
    for i, (c, v) in enumerate(means):
        y = 36 + i * rh
        w = v / 100 * iw
        color = SEQ[min(int(v / 100 * len(SEQ)), len(SEQ) - 1)]
        parts.append(text(ml - 8, y + 12, c, 12, "end"))
        parts.append(f'<rect x="{ml}" y="{y}" width="{max(w, 2):.1f}" height="14" rx="4" fill="{color}"/>')
        parts.append(text(ml + w + 8, y + 12, f"{v:.0f}", 12, bold=(v == top)))
    parts.append(text(24, H - 8, "agenticExposure sub-score: share of the role an autonomous agent could own today — see pipeline/RUBRIC.md", 10))
    return svg(W, H, "\n".join(parts))


def main():
    doc = json.loads((ROOT / "data" / "ai-career-threat-index.json").read_text(encoding="utf-8"))
    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "risk-distribution.svg").write_text(distribution(doc["roles"]), encoding="utf-8")
    (ASSETS / "top-movers.svg").write_text(movers(doc["roles"]), encoding="utf-8")
    (ASSETS / "agentic-heat.svg").write_text(agentic_heat(doc), encoding="utf-8")
    print("OK: 3 SVGs ->", ASSETS)


if __name__ == "__main__":
    main()
