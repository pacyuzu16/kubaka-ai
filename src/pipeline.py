"""KUBAKA AI fault-triage pipeline.

Two entry points:

  classify(text)  ONE model call. Language + symptoms + taxonomy mapping.
                  Used by the evaluation harness — cheap enough to run
                  across the whole test set on a free backend.

  triage(text)    Full pipeline: classify, then rank causes and write a
                  reply in the operator's language. Used for the demo.
"""
import json
import re
from dataclasses import dataclass, asdict, field

from .config import LANGUAGES
from . import taxonomy
from .llm import complete


def _json_from(text):
    """Pull a JSON object out of a model reply that may be fenced or prefaced."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError(f"no JSON in reply: {text[:200]}")
        return json.loads(match.group(0))


@dataclass
class Triage:
    input_text: str
    language: str = "en"
    translation_en: str = ""
    symptoms: list = field(default_factory=list)
    category: str = ""
    subcategory: str = ""
    confidence: float = 0.0
    needs_human: bool = False
    reasoning: str = ""
    causes: list = field(default_factory=list)
    parts: list = field(default_factory=list)
    urgency: str = "medium"
    environmental: str = ""
    immediate_action: str = ""
    reply: str = ""

    def to_ticket(self):
        return asdict(self)


CLASSIFY = """You triage faults on construction equipment (excavators, loaders, dozers) \
for operators in East Africa.

The operator's message may be in English, French, Kinyarwanda or Swahili. It may mix \
languages, be very short, and will usually avoid technical terms.

MESSAGE: "{text}"

TAXONOMY OF FAULTS:
{tax}

Do all of this in one pass and return ONLY a JSON object:
{{
  "language": "en|fr|rw|sw",
  "translation_en": "faithful English translation",
  "symptoms": ["short factual symptom phrases in English"],
  "category": "<category id from the taxonomy>",
  "subcategory": "<leaf id from the taxonomy>",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence",
  "needs_human": true/false
}}

Rules:
- Report only what the operator actually said as symptoms. Do not invent detail.
- If the message is too vague to map safely, or describes several unrelated faults, \
set needs_human true and leave category and subcategory as empty strings.
- Be honest with confidence. A low score is more useful than a confident guess.
- Watch for misdirection: operators often blame the wrong component. Classify from \
the symptoms, not from their diagnosis."""


RANK = """This equipment fault has been classified. Rank the likely causes for THIS \
report and say what the operator should do now.

OPERATOR SAID: "{translation}"
SYMPTOMS: {symptoms}
CLASSIFIED AS: {leaf_en} ({leaf_zh})
KNOWN CAUSES: {causes}
TYPICAL PARTS: {parts}
BASELINE URGENCY: {urgency}

Return ONLY JSON:
{{
  "causes": [{{"cause": "...", "likelihood": "high|medium|low", "check": "how to verify on site"}}],
  "parts": ["parts likely needed"],
  "urgency": "critical|high|medium|low",
  "immediate_action": "what the operator should do right now"
}}

Move urgency off the baseline only if this specific report justifies it."""


REPLY = """Write a short reply to a machine operator in {lang_name}.

They reported: "{original}"
Diagnosis: {leaf_en}
Most likely cause: {top_cause}
What to do now: {action}
Urgency: {urgency}

Rules:
- Reply ONLY in {lang_name}. No other language, no translation.
- Plain, respectful, practical. Assume no technical training.
- Three or four short sentences.
- If urgency is critical, tell them clearly to stop using the machine.
Return only the message text."""


def classify(text):
    """One model call: language, symptoms, taxonomy mapping."""
    data = _json_from(complete(CLASSIFY.format(text=text, tax=taxonomy.as_prompt_block())))
    result = Triage(input_text=text)
    result.language = data.get("language", "en")
    result.translation_en = data.get("translation_en", text)
    result.symptoms = data.get("symptoms", []) or []
    result.category = data.get("category", "") or ""
    result.subcategory = data.get("subcategory", "") or ""
    result.confidence = float(data.get("confidence", 0.0) or 0.0)
    result.needs_human = bool(data.get("needs_human", False))
    result.reasoning = data.get("reasoning", "") or ""

    # A leaf id the taxonomy doesn't contain is a hallucination — treat as abstention.
    if result.subcategory and taxonomy.get(result.subcategory) is None:
        result.reasoning += f" [rejected unknown leaf {result.subcategory!r}]"
        result.subcategory = ""
        result.category = ""
        result.needs_human = True
    return result


def triage(text, verbose=False):
    """Full pipeline. Three calls when a fault is identified, one when it abstains."""
    result = classify(text)
    if verbose:
        print(f"[1] {result.language} -> {result.subcategory or 'ABSTAIN'} ({result.confidence:.2f})")

    # Abstain only when there is genuinely no classification. The model
    # also raises needs_human as a soft "have a person check this" flag
    # while still returning its best guess — and in evaluation those
    # guesses were usually correct, so discarding them would both lose
    # useful output and make live behaviour diverge from the measured
    # numbers. A flagged-but-classified ticket is shown, marked for review.
    leaf = taxonomy.get(result.subcategory) if result.subcategory else None
    if leaf is None:
        result.needs_human = True
        result.subcategory = ""
        result.category = ""
        result.reply = "We could not identify this fault from the description. A technician will contact you."
        return result

    ranked = _json_from(complete(RANK.format(
        translation=result.translation_en, symptoms=result.symptoms,
        leaf_en=leaf["en"], leaf_zh=leaf["zh"], causes=leaf["causes"],
        parts=leaf["parts"], urgency=leaf["urgency"])))
    result.causes = ranked.get("causes", []) or []
    result.parts = ranked.get("parts") or leaf["parts"]
    result.urgency = ranked.get("urgency") or leaf["urgency"]
    result.immediate_action = ranked.get("immediate_action", "")
    result.environmental = leaf.get("environmental") or ""
    if verbose:
        print(f"[2] urgency {result.urgency}, {len(result.causes)} causes")

    top = result.causes[0]["cause"] if result.causes else leaf["causes"][0]
    result.reply = complete(REPLY.format(
        lang_name=LANGUAGES.get(result.language, "English"), original=text,
        leaf_en=leaf["en"], top_cause=top, action=result.immediate_action,
        urgency=result.urgency), max_tokens=400).strip()
    if verbose:
        print(f"[3] replied in {result.language}")
    return result


if __name__ == "__main__":
    import sys
    from .llm import health, which_backend
    ok, msg = health()
    print(f"backend: {msg}")
    if not ok:
        raise SystemExit(1)
    msg_text = " ".join(sys.argv[1:]) or "iri kuvuza amavuta kandi ukuboko kugenda buhoro"
    print(json.dumps(triage(msg_text, verbose=True).to_ticket(), ensure_ascii=False, indent=2))
