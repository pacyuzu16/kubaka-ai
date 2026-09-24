"""Re-analyse a saved eval run. No model calls — reads the JSON.

Separates two very different failure modes:
  WRONG    the system committed to a classification and it was incorrect
  ABSTAIN  the system declined to classify and escalated to a human

In a safety-critical domain these are not equivalent, so we report
recall (got it right), precision-when-committed (right when it spoke),
and abstention rate.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

from src.config import ROOT


def pct(n, d):
    return 0.0 if d == 0 else 100.0 * n / d


def analyse(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data["rows"]
    labelled = [r for r in rows if r["gold_subcategory"]]
    vague = [r for r in rows if not r["gold_subcategory"]]

    def bucket(rs):
        correct = [r for r in rs if r["pred_subcategory"] == r["gold_subcategory"]]
        abstain = [r for r in rs if not r["pred_subcategory"]]
        wrong = [r for r in rs if r["pred_subcategory"]
                 and r["pred_subcategory"] != r["gold_subcategory"]]
        return correct, wrong, abstain

    c, w, a = bucket(labelled)
    committed = len(c) + len(w)

    print("=" * 70)
    print(f"KUBAKA AI — evaluation   ({len(rows)} cases, {len(labelled)} labelled)")
    print("=" * 70)
    lang_hit = sum(r["pred_language"] == r["language"] for r in rows)
    print(f"language detection      {pct(lang_hit, len(rows)):5.1f}%  ({lang_hit}/{len(rows)})")
    print()
    print(f"recall (correct)        {pct(len(c), len(labelled)):5.1f}%  ({len(c)}/{len(labelled)})")
    print(f"precision when it answers  {pct(len(c), committed):5.1f}%  ({len(c)}/{committed})")
    print(f"abstained               {pct(len(a), len(labelled)):5.1f}%  ({len(a)}/{len(labelled)})")
    print(f"WRONG (committed+bad)   {pct(len(w), len(labelled)):5.1f}%  ({len(w)}/{len(labelled)})")
    print()
    print(f"correct abstention on vague input  {pct(sum(r['needs_human'] for r in vague), len(vague)):5.1f}%"
          f"  ({sum(r['needs_human'] for r in vague)}/{len(vague)})")

    print()
    print(f"{'lang':<6}{'n':>4}{'recall':>9}{'precision':>11}{'abstain':>9}{'wrong':>8}")
    print("-" * 47)
    by = defaultdict(list)
    for r in labelled:
        by[r["language"]].append(r)
    for lang in sorted(by):
        rs = by[lang]
        c2, w2, a2 = bucket(rs)
        comm = len(c2) + len(w2)
        print(f"{lang:<6}{len(rs):>4}{pct(len(c2),len(rs)):>8.1f}%"
              f"{pct(len(c2),comm):>10.1f}%{pct(len(a2),len(rs)):>8.1f}%{len(w2):>8}")

    print()
    print(f"WRONG answers ({len(w)}) — committed to an incorrect class")
    for r in w:
        print(f"  {r['id']:<8}[{r['language']}] {r['input'][:44]}")
        print(f"           gold {r['gold_subcategory']:<16} pred {r['pred_subcategory']:<16} conf {r['confidence']:.2f}")
    print()
    print(f"ABSTENTIONS on labelled cases ({len(a)}) — escalated instead of guessing")
    for r in a:
        print(f"  {r['id']:<8}[{r['language']}] {r['input'][:44]}")
        print(f"           gold {r['gold_subcategory']:<16} conf {r['confidence']:.2f}")

    conf_c = [r["confidence"] for r in c]
    conf_w = [r["confidence"] for r in w]
    if conf_c and conf_w:
        print()
        print("confidence separation")
        print(f"  mean confidence when correct  {sum(conf_c)/len(conf_c):.2f}")
        print(f"  mean confidence when wrong    {sum(conf_w)/len(conf_w):.2f}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        p = sys.argv[1]
    else:
        results = sorted((ROOT / "eval" / "results").glob("eval-*.json"))
        if not results:
            raise SystemExit("no eval results found")
        p = results[-1]
    analyse(p)
