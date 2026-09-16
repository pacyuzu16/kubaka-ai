"""Central configuration for KUBAKA AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = ROOT / "data" / "taxonomy.json"
TESTSET_PATH = ROOT / "data" / "testset" / "cases.jsonl"

API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Reasoning-heavy step (cause ranking) vs. the rest of the pipeline.
MODEL_MAIN = "claude-sonnet-5"
MODEL_REASONING = "claude-opus-5"

LANGUAGES = {
    "en": "English",
    "fr": "French",
    "rw": "Kinyarwanda",
    "sw": "Swahili",
}
