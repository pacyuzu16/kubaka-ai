"""KUBAKA AI fault-triage pipeline.

Operator message (any of 4 languages, optional photo)
  -> language detection
  -> symptom extraction
  -> taxonomy mapping
  -> cause ranking + parts + urgency
  -> reply in the operator's language + dealer ticket
"""
import json
import re
from dataclasses import dataclass, asdict, field

import anthropic

from .config import API_KEY, MODEL_MAIN, MODEL_REASONING, LANGUAGES
from . import taxonomy

_client = None


def client():
    global _client
    if _client is None:
        if not API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env.")
        _client = anthropic.Anthropic(api_key=API_KEY)
    return _client


def _json_from(text):
    """Models sometimes wrap JSON in prose or fences. Pull the object out."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _ask(prompt, model=MODEL_MAIN, max_tokens=1200):
    msg = client().messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


@dataclass
class Triage:
    input_text: str
    language: str = "en"
    symptoms: list = field(default_factory=list)
    category: str = ""
    subcategory: str = ""
    confidence: float = 0.0
    causes: list = field(default_factory=list)
    parts: list = field(default_factory=list)
    urgency: str = "medium"
    environmental: str = ""
    reply: str = ""
    needs_human: bool = False

    def to_ticket(self):
        return asdict(self)


DETECT_AND_EXTRACT = """You are a diagnostic assistant for construction equipment \
(excavators, loaders, dozers) used by operators in East Africa.

An operator sent this message. It may be in English, French, Kinyarwanda or Swahili, \
may mix languages, may be very short, and will usually avoid technical terms.

MESSAGE: "{text}"

Return ONLY a JSON object:
{{
  "language": "en|fr|rw|sw",
  "translation_en": "faithful English translation",
  "symptoms": ["short factual symptom phrases in English"],
  "component_hints": ["parts of the machine implied, if any"],
  "vague": true/false
}}

Do not diagnose yet. Extract only what the operator actually said."""


MAP_TO_TAXONOMY = """Map these observed symptoms to exactly one leaf fault in the taxonomy.

SYMPTOMS: {symptoms}
COMPONENT HINTS: {hints}
OPERATOR SAID (English): "{translation}"

TAXONOMY:
{tax}

Return ONLY JSON:
{{
  "category": "<category id>",
  "subcategory": "<leaf id>",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence",
  "needs_human": true/false
}}

Set needs_human true when the message is too vague to map safely, or when several \
unrelated faults are described. Be honest with confidence — a low score is more \
useful than a confident guess."""


RANK_CAUSES = """An equipment fault has been classified. Rank the likely causes for \
THIS specific report and state what the operator should do now.

OPERATOR SAID: "{translation}"
SYMPTOMS: {symptoms}
CLASSIFIED AS: {leaf_en} ({leaf_zh})
KNOWN CAUSES FOR THIS FAULT: {causes}
TYPICAL PARTS: {parts}
BASELINE URGENCY: {urgency}

Return ONLY JSON:
{{
  "causes": [{{"cause": "...", "likelihood": "high|medium|low", "check": "how to verify on site"}}],
  "parts": ["parts likely needed"],
  "urgency": "critical|high|medium|low",
  "immediate_action": "what the operator should do right now"
}}

Adjust urgency up or down from the baseline if this specific report justifies it."""


REPLY = """Write a short reply to a machine operator in {lang_name}.

They reported: "{original}"
Diagnosis: {leaf_en}
Most likely cause: {top_cause}
What to do now: {action}
Urgency: {urgency}

Rules:
- Reply ONLY in {lang_name}. No other language.
- Plain, respectful, practical. Assume no technical training.
- 3-4 short sentences maximum.
- If urgency is critical, tell them clearly to stop using the machine.
Return only the message text."""


def triage(text, verbose=False):
    """Run the full pipeline on one operator message."""
    result = Triage(input_text=text)

    extracted = _json_from(_ask(DETECT_AND_EXTRACT.format(text=text)))
    result.language = extracted.get("language", "en")
    result.symptoms = extracted.get("symptoms", [])
    translation = extracted.get("translation_en", text)
    hints = extracted.get("component_hints", [])
    if verbose:
        print("[1] language:", result.language, "| symptoms:", result.symptoms)

    mapped = _json_from(_ask(MAP_TO_TAXONOMY.format(
        symptoms=result.symptoms, hints=hints, translation=translation,
        tax=taxonomy.as_prompt_block())))
    result.category = mapped.get("category", "")
    result.subcategory = mapped.get("subcategory", "")
    result.confidence = float(mapped.get("confidence", 0.0))
    result.needs_human = bool(mapped.get("needs_human", False))
    if verbose:
        print("[2] ->", result.subcategory, f"({result.confidence:.2f})")

    leaf = taxonomy.get(result.subcategory)
    if leaf is None:
        result.needs_human = True
        result.reply = "We could not identify this fault automatically. A technician will contact you."
        return result

    ranked = _json_from(_ask(RANK_CAUSES.format(
        translation=translation, symptoms=result.symptoms,
        leaf_en=leaf["en"], leaf_zh=leaf["zh"], causes=leaf["causes"],
        parts=leaf["parts"], urgency=leaf["urgency"]), model=MODEL_REASONING))
    result.causes = ranked.get("causes", [])
    result.parts = ranked.get("parts", leaf["parts"])
    result.urgency = ranked.get("urgency", leaf["urgency"])
    result.environmental = leaf.get("environmental") or ""
    action = ranked.get("immediate_action", "")
    if verbose:
        print("[3] urgency:", result.urgency)

    top = result.causes[0]["cause"] if result.causes else leaf["causes"][0]
    result.reply = _ask(REPLY.format(
        lang_name=LANGUAGES.get(result.language, "English"), original=text,
        leaf_en=leaf["en"], top_cause=top, action=action,
        urgency=result.urgency), max_tokens=400).strip()

    return result


if __name__ == "__main__":
    import sys
    msg = " ".join(sys.argv[1:]) or "iri kuvuza amavuta kandi ukuboko kugenda buhoro"
    out = triage(msg, verbose=True)
    print(json.dumps(out.to_ticket(), ensure_ascii=False, indent=2))
