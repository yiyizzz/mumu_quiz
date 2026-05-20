#!/usr/bin/env python3
"""
sync_questions.py - 扫描 questions/ 目录下所有题库文件，解析合并后输出 questions.js

用法:
    python scripts/sync_questions.py [--input-dir questions] [--output questions.js]

支持格式: .xlsx, .docx, .md, .json
"""
import argparse
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parsers import parse_json, parse_md, parse_xlsx, parse_docx

PARSERS = {
    ".json": parse_json.parse,
    ".md": parse_md.parse,
    ".xlsx": parse_xlsx.parse,
    ".xls": parse_xlsx.parse,
    ".docx": parse_docx.parse,
}


def collect_questions(input_dir: Path) -> list[dict]:
    """Scan input_dir recursively, parse all supported files, return merged list."""
    all_questions = []
    files = sorted(input_dir.rglob("*"))

    for f in files:
        if f.suffix.lower() not in PARSERS:
            continue
        if f.name.startswith("~") or f.name.startswith("."):
            continue

        parser = PARSERS[f.suffix.lower()]
        try:
            questions = parser(f)
            print(f"  [{f.suffix}] {f.relative_to(input_dir)}: {len(questions)} questions")
            all_questions.extend(questions)
        except Exception as e:
            print(f"  [ERROR] {f.relative_to(input_dir)}: {e}", file=sys.stderr)

    return all_questions


def deduplicate(questions: list[dict]) -> list[dict]:
    """Remove duplicates based on question text (after stripping numbers)."""
    import re
    seen = set()
    result = []
    for q in questions:
        # Normalize: strip leading number prefix for comparison
        key = re.sub(r"^\d+[.、]\s*", "", q["q"]).strip()
        if key in seen:
            continue
        seen.add(key)
        result.append(q)
    return result


def assign_ids(questions: list[dict]) -> list[dict]:
    """Assign sequential IDs."""
    for i, q in enumerate(questions, 1):
        q["id"] = i
    return questions


def write_output(questions: list[dict], output_path: Path):
    """Write questions.js file."""
    js_content = "// 题库数据 - 由 sync_questions.py 自动生成，请勿手动编辑\n"
    js_content += "window.QUESTIONS = "
    js_content += json.dumps(questions, ensure_ascii=False, indent=2)
    js_content += ";\n"

    output_path.write_text(js_content, encoding="utf-8")
    print(f"\n✓ 已生成 {output_path} ({len(questions)} 题)")


def main():
    parser = argparse.ArgumentParser(description="Sync question bank files to questions.js")
    parser.add_argument("--input-dir", default="questions", help="题库文件夹路径")
    parser.add_argument("--output", default="questions.js", help="输出文件路径")
    args = parser.parse_args()

    # Resolve paths relative to project root (parent of scripts/)
    project_root = Path(__file__).parent.parent
    input_dir = project_root / args.input_dir
    output_path = project_root / args.output

    if not input_dir.exists():
        print(f"[ERROR] 题库目录不存在: {input_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"扫描题库目录: {input_dir}")
    questions = collect_questions(input_dir)

    if not questions:
        print("[WARN] 未找到任何题目，保留原有 questions.js")
        sys.exit(0)

    questions = deduplicate(questions)
    questions = assign_ids(questions)
    write_output(questions, output_path)


if __name__ == "__main__":
    main()
