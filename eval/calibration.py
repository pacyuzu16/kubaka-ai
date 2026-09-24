"""Two further analyses of a saved run. No model calls.

1. Confidence calibration — is the confidence score usable as a routing
   threshold, or is it decoration? A dealer can only act on it if
   accuracy actually rises with confidence.

2. Safety-critical recall — faults whose baseline urgency is CRITICAL
   (structural cracks, brake failure, cylinder drift, thermal runaway,
   HV insulation). Missing one of these is the worst outcome the system
   can produce, so it deserves its own number.
"""
import json
from pathlib import Path

from src.config import ROOT
from src import taxonomy


def pct(n, d):
    return 0.0 if d == 0 else 100.0 * n / d


def latest():
    files = list((ROOT / "eval" / "results").glob("*.json"))
    if not files:
        raise SystemExit("no eval results")
    return max(files, key=lambda f: len(json.loads(f.read_text(encoding="utf-8")).get("rows", [])))


def main():
    path = latest()
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    labelled = [r for r in rows if r["gold_subcategory"]]

    print("=" * 68)
    print(f"Confidence calibration   ({path.name})")
    print("=" * 68)
    buckets = [(0.0, 0.3), (0.3, 0.45), (0.45, 0.6), (0.6, 0.8), (0.8, 1.01)]
    print(f"{'confidence':<14}{'n':>5}{'correct':>10}{'accuracy':>11}")
    print("-" * 42)
    for lo, hi in buckets:
        band = [r for r in labelled if lo <= r["confidence"] < hi]
        if not band:
            continue
        ok = sum(r["pred_subcategory"] == r["gold_subcategory"] for r in band)
        print(f"{lo:.2f}–{hi if hi <= 1 else 1.0:.2f}{'':<4}{len(band):>5}{ok:>10}{pct(ok, len(band)):>10.1f}%")

    # what a routing threshold would actually buy a dealer
    print()
    print("If the dealer auto-acts above a threshold and sends the rest to a human:")
    print(f"{'threshold':<12}{'auto-handled':>14}{'accuracy of those':>20}")
    print("-" * 46)
    for th in (0.0, 0.4, 0.5, 0.6, 0.7):
        auto = [r for r in labelled if r["confidence"] >= th and r["pred_subcategory"]]
        ok = sum(r["pred_subcategory"] == r["gold_subcategory"] for r in auto)
        print(f"≥ {th:.2f}{'':<7}{pct(len(auto), len(labelled)):>13.1f}%{pct(ok, len(auto)):>19.1f}%")

    # ── safety-critical ──
    crit_leaves = {l["id"] for l in taxonomy.leaves() if l["urgency"] == "critical"}
    crit = [r for r in labelled if r["gold_subcategory"] in crit_leaves]
    ok = [r for r in crit if r["pred_subcategory"] == r["gold_subcategory"]]
    abst = [r for r in crit if not r["pred_subcategory"]]
    wrong = [r for r in crit if r["pred_subcategory"] and r["pred_subcategory"] != r["gold_subcategory"]]
    # a miss that stays inside the critical set is far less dangerous
    wrong_still_crit = [r for r in wrong if r["pred_subcategory"] in crit_leaves]

    print()
    print("=" * 68)
    print("Safety-critical faults")
    print("=" * 68)
    print(f"critical leaves in taxonomy      {len(crit_leaves)} of {len(taxonomy.leaves())}")
    print(f"critical cases in the test set   {len(crit)}")
    print(f"  correctly identified           {len(ok)}  ({pct(len(ok), len(crit)):.1f}%)")
    print(f"  escalated to a human           {len(abst)}  ({pct(len(abst), len(crit)):.1f}%)")
    print(f"  misclassified                  {len(wrong)}  ({pct(len(wrong), len(crit)):.1f}%)")
    print(f"    of those, still critical     {len(wrong_still_crit)}")
    silent = len(wrong) - len(wrong_still_crit)
    print()
    print(f"SILENT DOWNGRADES (critical fault classified as non-critical, not escalated): {silent}")
    if silent == 0:
        print("  No safety-critical fault was quietly treated as routine.")
    else:
        for r in wrong:
            if r["pred_subcategory"] not in crit_leaves:
                print(f"  {r['id']} [{r['language']}] {r['input'][:44]}")
                print(f"        gold {r['gold_subcategory']} -> pred {r['pred_subcategory']}")


if __name__ == "__main__":
    main()
