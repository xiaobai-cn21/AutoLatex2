"""文档解析器端到端测试：覆盖 DOCX 与 Markdown。"""

from __future__ import annotations

import json
import os
from typing import Dict

import sys
from pathlib import Path

# 添加 src 目录到路径
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from autolatex.tools.document_tools import DocumentParserTool
from autolatex.tools.schema_validator import load_document_schema, validate_parsed_document

BASE_DIR = os.path.dirname(__file__)
DOCX_TEST_DIR = os.path.normpath(os.path.join(BASE_DIR, "../../..", "test_data", "docx_samples"))
MD_TEST_DIR = os.path.normpath(os.path.join(BASE_DIR, "../../..", "test_data", "md_samples"))
TXT_TEST_DIR = os.path.normpath(os.path.join(BASE_DIR, "../../..", "test_data", "txt_samples"))
IMAGES_DIR = os.path.normpath(os.path.join(BASE_DIR, "../../..", "parsed_images"))


def run_file_test(file_path: str) -> bool:
    parser_tool = DocumentParserTool()
    try:
        json_output_str = parser_tool._run(file_path)
        parsed_dict = json.loads(json_output_str)

        schema = load_document_schema()
        is_valid = validate_parsed_document(parsed_dict, schema)
        preview = json.dumps(parsed_dict, indent=2, ensure_ascii=False)
        if len(preview) > 1500:
            preview = preview[:1500] + "..."
        print("--- Parsing Successful ---")
        print(preview)
        return is_valid
    except (FileNotFoundError, ValueError) as exc:
        print(f"--- Parsing Failed: {exc} ---")
        return False
    except Exception as exc:  # pylint: disable=broad-except
        print(f"--- An unexpected error occurred: {exc} ---")
        return False


def run_docx_tests() -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    docx_cases = [
        "sample_paper_full.docx",
        "sample_paper_min.docx",
        "sample_paper_no_bib.docx",
    ]
    for case in docx_cases:
        file_path = os.path.join(DOCX_TEST_DIR, case)
        print(f"\n--- Running DOCX test for: {case} ---")
        if not os.path.exists(file_path):
            print(f"Test file not found: {file_path}")
            results[case] = False
            continue
        results[case] = run_file_test(file_path)
    return results


def run_md_tests() -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    md_cases = ["sample_paper_with_frontmatter.md"]
    for case in md_cases:
        file_path = os.path.join(MD_TEST_DIR, case)
        print(f"\n--- Running MD test for: {case} ---")
        if not os.path.exists(file_path):
            print(f"Test file not found: {file_path}")
            results[case] = False
            continue
        results[case] = run_file_test(file_path)
    return results


def run_txt_tests() -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    txt_cases = ["sample_paper_full.txt", "sample_paper_min.txt"]
    for case in txt_cases:
        file_path = os.path.join(TXT_TEST_DIR, case)
        print(f"\n--- Running TXT test for: {case} ---")
        if not os.path.exists(file_path):
            print(f"Test file not found: {file_path}")
            results[case] = False
            continue
        results[case] = run_file_test(file_path)
    return results


def ensure_dirs() -> None:
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)


def main() -> None:
    print("Starting document parser tests...")
    ensure_dirs()

    docx_results = run_docx_tests()
    md_results = run_md_tests()
    txt_results = run_txt_tests()

    print("\n--- DOCX Test Summary ---")
    for name, passed in docx_results.items():
        print(f"{name}: {'PASSED' if passed else 'FAILED'}")

    print("\n--- Markdown Test Summary ---")
    for name, passed in md_results.items():
        print(f"{name}: {'PASSED' if passed else 'FAILED'}")

    print("\n--- TXT Test Summary ---")
    for name, passed in txt_results.items():
        print(f"{name}: {'PASSED' if passed else 'FAILED'}")

    overall = all(docx_results.values()) and all(md_results.values()) and all(txt_results.values())
    print(f"\nOverall Test Result: {'ALL PASSED' if overall else 'SOME FAILED'}")


if __name__ == "__main__":
    main()

