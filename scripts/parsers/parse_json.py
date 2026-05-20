"""Parse JSON question files.

Expected format: array of objects with fields:
  type, q, opts, ans, explain
Same structure as questions.js output.
"""
import json
from pathlib import Path


def parse(filepath: Path) -> list[dict]:
    """Return list of question dicts from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    else:
        return []

    result = []
    for item in questions:
        q = {
            "type": item.get("type", "single"),
            "q": item.get("q", "").strip(),
            "opts": item.get("opts", []),
            "ans": item.get("ans", ""),
            "explain": item.get("explain", ""),
        }
        if q["q"] and q["opts"]:
            result.append(q)
    return result
