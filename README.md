# KUBAKA AI

**Multilingual fault triage for construction equipment.**

An operator describes a problem in their own language — *"iri kuvuza amavuta kandi ukuboko kugenda buhoro"* — and KUBAKA AI returns a structured diagnosis: fault category, ranked causes, parts likely needed, urgency, and a service ticket the dealer can act on.

Built for the 15th China Innovation & Entrepreneurship Competition, **"AI + Construction Machinery"** Division — Professional Contest · Team Group · **AI + Operations**.

*Kubaka* means "to build" in Kinyarwanda.

---

## The problem

In emerging markets the bottleneck in equipment operations is not the machinery — it is language and diagnosis. A fault is noticed by an operator working in Kinyarwanda or Swahili, reported through a dealer operating in English or French, and resolved by a technician who needs structured technical information. Between those three, detail is lost. Machines sit idle, the wrong parts get ordered, and hydraulic leaks run for weeks.

## Approach

```
Operator message (rw / sw / fr / en, optionally with a photo)
        │
   [1]  language detection + faithful translation
   [2]  symptom extraction          → factual symptom phrases
   [3]  taxonomy mapping            → 1 of 35 leaf faults, with confidence
   [4]  cause ranking               → ranked causes, parts, urgency
   [5]  reply generation            → operator's own language
        │
        ├─→ reply to operator
        └─→ structured ticket to dealer
```

The pipeline **abstains rather than guesses**: vague or multi-fault messages are flagged `needs_human` instead of being forced into a category.

## Fault taxonomy

7 categories, 35 leaf faults — hydraulic, engine, undercarriage, electrical, transmission, structure & attachments, and **new-energy systems** (battery SOH, charging, thermal management, traction motor, HV safety).

Each leaf carries typical symptoms, known causes, likely parts, a baseline urgency, and — where genuine — an environmental note. Authored independently from general engineering knowledge; contains no manufacturer-proprietary content.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
```

## Run

```bash
# single message
python -m src.pipeline "the boom is leaking oil and moves slowly"

# demo interface
streamlit run app/app.py

# evaluation
python -m eval.run_eval --limit 5     # smoke test
python -m eval.run_eval               # full run
```

## Evaluation

The test set (`data/testset/cases.jsonl`) deliberately includes hard cases: vague input, mixed-language messages, multiple simultaneous faults, misleading descriptions where the operator blames the wrong component, and very short messages.

`run_eval` reports language detection, category and subcategory accuracy, urgency accuracy, correct abstention on vague input, and **per-language accuracy** — then lists every failure. Per-language numbers are reported openly: the gap between English and Kinyarwanda performance is the low-resource-language problem this project exists to address.

## Layout

```
data/taxonomy.json          fault taxonomy
data/testset/cases.jsonl    labelled evaluation cases
src/pipeline.py             the five-step triage pipeline
src/taxonomy.py             taxonomy loading and prompt rendering
eval/run_eval.py            evaluation harness
app/app.py                  demo interface
```

## Team

School of ICT, University of Rwanda, College of Science and Technology.

- **CYUZUZO PACIFIQUE** — pipeline, prompting
- **MBABAZI PATRICK STRATON** — interface, deployment
- **IRUMVA GAD ANACLET** — evaluation, test set

## Licence

All rights reserved by the team members. Submitted for competition evaluation.
