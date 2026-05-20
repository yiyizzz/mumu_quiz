"""Parse Word (.docx) question files.

Same logical format as Markdown:
  - Questions identified by leading number `1.` or `1、`
  - Options by `A.` `B.` etc.
  - 答案: / 解析: lines

Each paragraph in the docx is treated as a line.
"""
import re
from pathlib import Path

try:
    import docx
except ImportError:
    docx = None

from .parse_md import _Q_PATTERN, _OPT_PATTERN, _ANS_PATTERN, _EXPLAIN_PATTERN


def parse(filepath: Path) -> list[dict]:
    """Return list of question dicts from a Word file."""
    if docx is None:
        print(f"[WARN] python-docx not installed, skipping {filepath}")
        return []

    doc = docx.Document(filepath)
    # Collect all paragraph text
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # Group into questions - each new question starts with a number pattern
    questions_raw = []
    current = []
    for line in lines:
        if _Q_PATTERN.match(line) and current:
            questions_raw.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        questions_raw.append(current)

    results = []
    for lines_group in questions_raw:
        q_text = ""
        opts = []
        ans = ""
        explain = ""
        q_type = "single"

        for line in lines_group:
            m = _ANS_PATTERN.match(line)
            if m:
                ans = m.group(1).strip().upper()
                if len(ans) > 1 and all(c in "ABCDEFGH" for c in ans):
                    q_type = "multi"
                continue

            m = _EXPLAIN_PATTERN.match(line)
            if m:
                explain = m.group(1).strip()
                continue

            m = _OPT_PATTERN.match(line)
            if m:
                opts.append(f"{m.group(1)}.{m.group(2)}")
                continue

            m = _Q_PATTERN.match(line)
            if m:
                q_text = line
                continue

            if not q_text:
                q_text = line

        if q_text and opts and ans:
            results.append({
                "type": q_type,
                "q": q_text,
                "opts": opts,
                "ans": ans,
                "explain": explain,
            })

    return results
