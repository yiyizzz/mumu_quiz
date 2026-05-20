"""Parse Markdown question files.

Supported format:
  - Questions separated by blank lines or `---`
  - Question line starts with a number like `1.` or `1、`
  - Options start with `A.` `B.` `C.` `D.` (or A、B、etc)
  - Answer line: `答案:` or `答案：` followed by letter(s)
  - Explain line: `解析:` or `解析：` followed by text
"""
import re
from pathlib import Path


_Q_PATTERN = re.compile(r"^\d+[.、]\s*(.+)")
_OPT_PATTERN = re.compile(r"^([A-Z])[.、]\s*(.+)")
_ANS_PATTERN = re.compile(r"^答案[：:]\s*(.+)", re.IGNORECASE)
_EXPLAIN_PATTERN = re.compile(r"^解析[：:]\s*(.+)", re.IGNORECASE)
_SEPARATOR = re.compile(r"^-{3,}$")


def parse(filepath: Path) -> list[dict]:
    """Return list of question dicts from a Markdown file."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into blocks by --- or double newline
    blocks = re.split(r"\n---\n|\n{2,}", content)

    results = []
    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue

        q_text = ""
        opts = []
        ans = ""
        explain = ""
        q_type = "single"

        for line in lines:
            m = _ANS_PATTERN.match(line)
            if m:
                ans = m.group(1).strip().upper()
                # Multi-answer means multi-select
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
                q_text = line  # Keep full line including number prefix
                continue

            # If none matched and no q_text yet, treat as question
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
