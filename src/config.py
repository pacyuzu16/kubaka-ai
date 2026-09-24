"""Central configuration for KUBAKA AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

TAXONOMY_PATH = ROOT / "data" / "taxonomy.json"
TESTSET_PATH = ROOT / "data" / "testset" / "cases.jsonl"

# claude_cli (free, default) | gemini (free tier) | anthropic (paid)
BACKEND = os.getenv("KUBAKA_BACKEND", "claude_cli")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

CLAUDE_CLI_MODEL = os.getenv("CLAUDE_CLI_MODEL", "sonnet")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

LANGUAGES = {"en": "English", "fr": "French", "rw": "Kinyarwanda", "sw": "Swahili"}
