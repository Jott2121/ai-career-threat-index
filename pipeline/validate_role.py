#!/usr/bin/env python3
"""Validate a single role source file and print its computed v2 score.

Usage: python3 pipeline/validate_role.py pipeline/roles/<slug>.json [...]
Exits non-zero on the first invalid file. Used by contributors and data agents
for per-file checks before the full `score.py` assembly run.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score as S


def main(paths):
    soc_ref = {}
    with open(S.SOC_REF, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc_ref[row["soc_code"]] = row["title"]
    for p in paths:
        p = Path(p)
        src = json.loads(p.read_text(encoding="utf-8"))
        if src.get("slug") != p.stem:
            S.fail(f"{p.name}: slug != filename")
        S.validate(src, soc_ref)
        sc = S.composite(src["subscores"])
        prev = src.get("historicalScores", {}).get(S.PREV_QUARTER)
        delta = "" if prev is None else f" (Q2 {prev} -> Q3 {sc}, delta {sc - prev:+d})"
        if prev is not None and abs(sc - prev) > S.RESTATEMENT_DELTA and not src.get("restatement", "").strip():
            S.fail(f"{p.name}: delta {sc - prev:+d} exceeds ±{S.RESTATEMENT_DELTA} "
                   f"but no 'restatement' reason given")
        band = S.banded(sc, src.get("prevRiskLevel"))
        print(f"OK {p.name}: score {sc} [{band}]{delta}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    main(sys.argv[1:])
