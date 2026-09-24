"""Evaluation harness — the thing that wins points.

Usage:
    python -m eval.run_eval                 # run everything
    python -m eval.run_eval --limit 5       # quick smoke test
"""
import argparse
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from src.config import TESTSET_PATH, ROOT
from src.pipeline import classify
from src.llm import which_backend

def load_cases():
    with open(TESTSET_PATH, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]

def pct(num, den):
    return 0.0 if den == 0 else 100.0 * num / den

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cases = load_cases()
    if args.limit:
        cases = cases[: args.limit]

    rows, errors = [], []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] {case['id']}: {case['input'][:55]}")
        try:
            out = classify(case["input"])
            rows.append({
                "id": case["id"],
                "language": case["language"],
                "input": case["input"],
                "gold_category": case["gold_category"],
                "gold_subcategory": case["gold_subcategory"],
                "pred_language": out.language,
                "pred_category": out.category,
                "pred_subcategory": out.subcategory,
                "confidence": out.confidence,
                "needs_human": out.needs_human,
                "notes": case.get("notes", ""),
            })
        except Exception as exc:  # keep going; a crash mid-run loses everything
            print(f"    ERROR: {exc}")
            errors.append({"id": case["id"], "error": str(exc)})
        time.sleep(0.4)

    labelled = [r for r in rows if r["gold_subcategory"]]
    vague = [r for r in rows if not r["gold_subcategory"]]

    cat_hit = sum(r["pred_category"] == r["gold_category"] for r in labelled)
    sub_hit = sum(r["pred_subcategory"] == r["gold_subcategory"] for r in labelled)
    lang_hit = sum(r["pred_language"] == r["language"] for r in rows)
    abstain_ok = sum(r["needs_human"] for r in vague)

    print("\n" + "=" * 62)
    print(f"KUBAKA AI — evaluation   (backend: {which_backend()})")
    print("=" * 62)
    print(f"cases run          {len(rows)}   (errors: {len(errors)})")
    print(f"language detect    {pct(lang_hit, len(rows)):5.1f}%   ({lang_hit}/{len(rows)})")
    print(f"category accuracy  {pct(cat_hit, len(labelled)):5.1f}%   ({cat_hit}/{len(labelled)})")
    print(f"subcategory        {pct(sub_hit, len(labelled)):5.1f}%   ({sub_hit}/{len(labelled)})")

    if vague:
        print(f"correct abstention {pct(abstain_ok, len(vague)):5.1f}%   ({abstain_ok}/{len(vague)} vague cases flagged)")

    print("\nper-language subcategory accuracy")
    by_lang = defaultdict(lambda: [0, 0])
    for r in labelled:
        by_lang[r["language"]][1] += 1
        if r["pred_subcategory"] == r["gold_subcategory"]:
            by_lang[r["language"]][0] += 1
    for lang, (hit, tot) in sorted(by_lang.items()):
        print(f"  {lang}  {pct(hit, tot):5.1f}%   ({hit}/{tot})")

    misses = [r for r in labelled if r["pred_subcategory"] != r["gold_subcategory"]]
    if misses:
        print(f"\nfailures ({len(misses)}) — this is the section judges care about")
        for r in misses:
            print(f"  {r['id']} [{r['language']}] {r['input'][:42]}")
            print(f"        gold {r['gold_subcategory']}  ->  pred {r['pred_subcategory']} (conf {r['confidence']:.2f})")
            if r["notes"]:
                print(f"        note: {r['notes']}")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = ROOT / "eval" / "results" / f"eval-{stamp}.json"
    out_path.write_text(json.dumps(
        {"rows": rows, "errors": errors,
         "summary": {
             "n": len(rows), "language": pct(lang_hit, len(rows)),
             "category": pct(cat_hit, len(labelled)),
             "subcategory": pct(sub_hit, len(labelled)),
         }}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved -> {out_path.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
