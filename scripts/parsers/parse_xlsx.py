"""Parse Excel (.xlsx) question files.

Expected columns (header row required, name matching is flexible):
  题型 | 题目 | A | B | C | D | 答案 | 解析

Column name matching:
  - 题型/type → type (default: single)
  - 题目/question/题干 → q
  - A/选项A → opts[0], B/选项B → opts[1], etc.
  - 答案/answer → ans
  - 解析/explanation/explain → explain
"""
from pathlib import Path

try:
    import openpyxl
except ImportError:
    openpyxl = None


def _normalize_col(name: str) -> str:
    """Map column header to internal field name."""
    name = name.strip().lower()
    mapping = {
        "题型": "type", "type": "type",
        "题目": "q", "题干": "q", "question": "q",
        "答案": "ans", "answer": "ans",
        "解析": "explain", "explanation": "explain",
    }
    if name in mapping:
        return mapping[name]
    # Single letter A-H → option
    if len(name) == 1 and name.upper() in "ABCDEFGH":
        return f"opt_{name.upper()}"
    # 选项A, 选项B etc.
    if name.startswith("选项") and len(name) == 3:
        return f"opt_{name[2].upper()}"
    return name


def parse(filepath: Path) -> list[dict]:
    """Return list of question dicts from an Excel file."""
    if openpyxl is None:
        print(f"[WARN] openpyxl not installed, skipping {filepath}")
        return []

    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    results = []

    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        # Find header row (first row with content)
        header = None
        data_start = 0
        for i, row in enumerate(rows):
            if row and any(cell is not None for cell in row):
                header = [str(cell or "").strip() for cell in row]
                data_start = i + 1
                break

        if not header:
            continue

        col_map = {i: _normalize_col(h) for i, h in enumerate(header) if h}

        for row in rows[data_start:]:
            if not row or all(cell is None for cell in row):
                continue

            record = {}
            for i, cell in enumerate(row):
                if i in col_map and cell is not None:
                    record[col_map[i]] = str(cell).strip()

            # Build question
            q_text = record.get("q", "")
            if not q_text:
                continue

            opts = []
            for letter in "ABCDEFGH":
                key = f"opt_{letter}"
                if key in record and record[key]:
                    opts.append(f"{letter}.{record[key]}")

            if not opts:
                continue

            ans = record.get("ans", "").upper()
            q_type = record.get("type", "single")
            if q_type not in ("single", "multi", "judge"):
                # Try to infer
                if len(ans) > 1 and all(c in "ABCDEFGH" for c in ans):
                    q_type = "multi"
                else:
                    q_type = "single"

            results.append({
                "type": q_type,
                "q": q_text,
                "opts": opts,
                "ans": ans,
                "explain": record.get("explain", ""),
            })

    wb.close()
    return results
