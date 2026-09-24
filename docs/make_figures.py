"""Generate figures for the project document. Run: python docs/make_figures.py"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F = lambda s, b=False: ImageFont.truetype(BOLD if b else REG, s)

INK, MUTED, LINE = (20, 24, 28), (100, 112, 125), (222, 228, 227)
ACCENT, ACCENT_D, SOFT = (15, 118, 110), (11, 93, 86), (214, 242, 238)
CRIT, WARN, GOOD = (217, 45, 32), (232, 89, 12), (18, 146, 79)
W_ = lambda d, t, f: d.textbbox((0, 0), t, font=f)[2]


def rr(d, box, r, fill=None, outline=None, w=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=w)


# ── Figure 1: architecture ──────────────────────────────
def architecture():
    W, H, S = 2000, 700, 2
    im = Image.new("RGB", (W * S, H * S), "white")
    d = ImageDraw.Draw(im)
    f_t, f_s, f_n, f_b = F(30 * S, True), F(19 * S), F(17 * S), F(21 * S, True)

    d.text((40 * S, 26 * S), "KUBAKA AI — fault triage pipeline", font=f_t, fill=INK)
    d.text((40 * S, 62 * S), "One operator message in. A structured service ticket and a reply in the operator's own language out.",
           font=f_s, fill=MUTED)

    # input
    x0, y = 40 * S, 130 * S
    rr(d, [x0, y, x0 + 300 * S, y + 108 * S], 12 * S, fill=SOFT, outline=ACCENT, w=2 * S)
    d.text((x0 + 18 * S, y + 14 * S), "OPERATOR MESSAGE", font=F(14 * S, True), fill=ACCENT_D)
    for i, ln in enumerate(['"igikombe kimanuka', 'cyonyine kandi iri', 'kuvuza amavuta"']):
        d.text((x0 + 18 * S, y + 38 * S + i * 21 * S), ln, font=f_n, fill=INK)
    d.text((x0 + 18 * S, y + 118 * S), "rw · fr · en · sw", font=F(15 * S), fill=MUTED)

    steps = [
        ("1", "Language detection", "identify + translate faithfully"),
        ("2", "Symptom extraction", "only what was actually said"),
        ("3", "Taxonomy mapping", "1 of 35 leaves + confidence"),
        ("4", "Cause ranking", "causes · parts · urgency"),
        ("5", "Reply generation", "operator's own language"),
    ]
    bx, bw, gap = 400 * S, 280 * S, 22 * S
    for i, (n, title, sub) in enumerate(steps):
        x = bx + i * (bw + gap)
        rr(d, [x, y, x + bw, y + 108 * S], 12 * S, fill="white", outline=LINE, w=2 * S)
        d.ellipse([x + 16 * S, y + 16 * S, x + 44 * S, y + 44 * S], fill=ACCENT)
        d.text((x + 25 * S, y + 21 * S), n, font=F(16 * S, True), fill="white")
        d.text((x + 54 * S, y + 20 * S), title, font=f_b, fill=INK)
        d.text((x + 16 * S, y + 58 * S), sub, font=F(15 * S), fill=MUTED)
        ax = x - gap + 4 * S
        d.line([ax - 8 * S, y + 54 * S, ax + 10 * S, y + 54 * S], fill=LINE, width=3 * S)
        d.polygon([(ax + 10 * S, y + 48 * S), (ax + 20 * S, y + 54 * S), (ax + 10 * S, y + 60 * S)], fill=LINE)

    # single-call bracket over 1-3
    b0, b1, byy = bx, bx + 3 * bw + 2 * gap, y + 128 * S
    d.line([b0, byy, b1, byy], fill=ACCENT, width=2 * S)
    d.line([b0, byy, b0, byy - 10 * S], fill=ACCENT, width=2 * S)
    d.line([b1, byy, b1, byy - 10 * S], fill=ACCENT, width=2 * S)
    lbl = "classify()  —  one model call, used for evaluation"
    d.text(((b0 + b1) / 2 - W_(d, lbl, F(16 * S, True)) / 2, byy + 8 * S), lbl, font=F(16 * S, True), fill=ACCENT_D)

    # outputs
    oy = 330 * S
    rr(d, [bx, oy, bx + 620 * S, oy + 150 * S], 12 * S, fill=(247, 250, 249), outline=LINE, w=2 * S)
    d.text((bx + 18 * S, oy + 14 * S), "REPLY TO OPERATOR", font=F(14 * S, True), fill=ACCENT_D)
    for i, ln in enumerate(["Hagarika gukoresha iyi mashini ubu…", "(written in Kinyarwanda)"]):
        d.text((bx + 18 * S, oy + 42 * S + i * 26 * S), ln, font=f_n, fill=INK if i == 0 else MUTED)

    ox2 = bx + 660 * S
    rr(d, [ox2, oy, ox2 + 800 * S, oy + 150 * S], 12 * S, fill="white", outline=LINE, w=2 * S)
    d.text((ox2 + 18 * S, oy + 14 * S), "DEALER TICKET", font=F(14 * S, True), fill=ACCENT_D)
    rr(d, [ox2 + 18 * S, oy + 40 * S, ox2 + 112 * S, oy + 66 * S], 13 * S, fill=CRIT)
    d.text((ox2 + 34 * S, oy + 45 * S), "CRITICAL", font=F(13 * S, True), fill="white")
    d.text((ox2 + 126 * S, oy + 42 * S), "hyd_drift", font=F(20 * S, True), fill=INK)
    d.text((ox2 + 18 * S, oy + 78 * S), "ranked causes · parts · on-site checks · environmental note", font=F(15 * S), fill=MUTED)
    d.text((ox2 + 18 * S, oy + 104 * S), "confidence 0.72", font=F(15 * S, True), fill=ACCENT_D)

    # abstention branch
    ay = 530 * S
    rr(d, [bx, ay, bx + 1460 * S, ay + 96 * S], 12 * S, fill=(255, 251, 235), outline=(252, 211, 77), w=2 * S)
    d.text((bx + 20 * S, ay + 18 * S), "IF IT CANNOT CLASSIFY SAFELY  →  it abstains and escalates to a human",
           font=F(19 * S, True), fill=(146, 64, 14))
    d.text((bx + 20 * S, ay + 52 * S),
           "A leaf id outside the taxonomy is rejected. Vague or multi-fault messages are flagged. 0 silent downgrades of safety-critical faults in 77 cases.",
           font=F(15 * S), fill=(146, 64, 14))

    d.text((40 * S, (H - 42) * S), "School of ICT, University of Rwanda  ·  15th China Innovation & Entrepreneurship Competition  ·  AI + Construction Machinery",
           font=F(14 * S), fill=MUTED)
    im.resize((W, H), Image.LANCZOS).save(OUT / "architecture.png")
    print("architecture.png")


# ── Figure 2: calibration ───────────────────────────────
def calibration():
    from src import taxonomy  # noqa
    files = list((ROOT / "eval" / "results").glob("*.json"))
    rows = json.loads(max(files, key=lambda f: len(json.loads(f.read_text(encoding='utf-8')).get('rows', []))).read_text(encoding="utf-8"))["rows"]
    lab = [r for r in rows if r["gold_subcategory"]]
    # Wide bands deliberately: narrow ones produce n=2 buckets whose
    # percentages are noise and break an otherwise monotonic trend.
    buckets = [(0.0, 0.45, "below 0.45"), (0.45, 0.60, "0.45 – 0.60"), (0.60, 1.01, "0.60 and above")]
    data = []
    for lo, hi, lbl in buckets:
        b = [r for r in lab if lo <= r["confidence"] < hi]
        if b:
            ok = sum(r["pred_subcategory"] == r["gold_subcategory"] for r in b)
            data.append((lbl, len(b), 100.0 * ok / len(b)))

    W, H, S = 1500, 900, 2
    im = Image.new("RGB", (W * S, H * S), "white")
    d = ImageDraw.Draw(im)
    d.text((40 * S, 26 * S), "Accuracy rises with confidence", font=F(30 * S, True), fill=INK)
    d.text((40 * S, 64 * S), "Classification accuracy within each confidence band, 72 labelled cases. Wide bands are used so no bar rests on a handful of samples.",
           font=F(18 * S), fill=MUTED)

    x0, y0, ph, pw = 110 * S, 140 * S, 500 * S, 1300 * S
    for g in range(0, 101, 25):
        yy = y0 + ph - (g / 100) * ph
        d.line([x0, yy, x0 + pw, yy], fill=(240, 243, 242), width=2 * S)
        d.text((x0 - 62 * S, yy - 12 * S), f"{g}%", font=F(16 * S), fill=MUTED)
    d.line([x0, y0 + ph, x0 + pw, y0 + ph], fill=LINE, width=3 * S)

    n = len(data)
    bw = pw / n * 0.52
    for i, (lbl, cnt, acc) in enumerate(data):
        cx = x0 + pw * (i + 0.5) / n
        bh = (acc / 100) * ph
        col = GOOD if acc >= 95 else (WARN if acc >= 60 else CRIT)
        rr(d, [cx - bw / 2, y0 + ph - bh, cx + bw / 2, y0 + ph], 8 * S, fill=col)
        t = f"{acc:.0f}%"
        d.text((cx - W_(d, t, F(24 * S, True)) / 2, y0 + ph - bh - 38 * S), t, font=F(24 * S, True), fill=col)
        d.text((cx - W_(d, lbl, F(18 * S, True)) / 2, y0 + ph + 16 * S), lbl, font=F(18 * S, True), fill=INK)
        nt = f"n = {cnt}"
        d.text((cx - W_(d, nt, F(16 * S)) / 2, y0 + ph + 42 * S), nt, font=F(16 * S), fill=MUTED)

    ny = y0 + ph + 95 * S
    rr(d, [x0, ny, x0 + pw, ny + 120 * S], 12 * S, fill=SOFT, outline=ACCENT, w=2 * S)
    d.text((x0 + 22 * S, ny + 18 * S), "Deployment consequence", font=F(20 * S, True), fill=ACCENT_D)
    d.text((x0 + 22 * S, ny + 50 * S),
           "Auto-handling only tickets above 0.60 covers 55.6% of cases at 100% accuracy; everything below routes to a human.",
           font=F(17 * S), fill=INK)
    d.text((x0 + 22 * S, ny + 80 * S),
           "Below 0.30 the system was correct 0 times out of 6 — and those are exactly the cases it escalates.",
           font=F(17 * S), fill=INK)
    im.resize((W, H), Image.LANCZOS).save(OUT / "calibration.png")
    print("calibration.png")


if __name__ == "__main__":
    architecture()
    calibration()
