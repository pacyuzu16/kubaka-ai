"""Load the fault taxonomy and render it for prompting."""
import json
from functools import lru_cache
from .config import TAXONOMY_PATH


@lru_cache(maxsize=1)
def load():
    with open(TAXONOMY_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def leaves():
    """Flat list of every leaf fault, with its parent category attached."""
    out = []
    for cat in load()["categories"]:
        for sub in cat["subcategories"]:
            out.append({**sub, "category": cat["id"], "category_zh": cat["zh"]})
    return out


def leaf_ids():
    return [leaf["id"] for leaf in leaves()]


def get(leaf_id):
    for leaf in leaves():
        if leaf["id"] == leaf_id:
            return leaf
    return None


def as_prompt_block():
    """Compact taxonomy rendering for the model. Keeps tokens down."""
    lines = []
    for cat in load()["categories"]:
        lines.append(f"{cat['id']} ({cat['en']} / {cat['zh']}):")
        for sub in cat["subcategories"]:
            sym = "; ".join(sub["symptoms"][:3])
            lines.append(f"  - {sub['id']}: {sub['en']} — typical signs: {sym}")
    return "\n".join(lines)
