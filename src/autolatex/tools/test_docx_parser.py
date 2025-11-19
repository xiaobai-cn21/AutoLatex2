"""DOCX 解析器的端到端测试脚本。"""

from __future__ import annotations

import json
import os
from typing import Dict

from document_tools import DocumentParserTool
from schema_validator import load_document_schema, validate_parsed_document

BASE_TEST_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../..", "test_data", "docx_samples")
)
IMAGES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../../..", "parsed_images")
)


def run_single_test(file_name: str) -> bool:
    file_path = os.path.join(BASE_TEST_DIR, file_name)
    print(f"\n--- Running test for: {file_name} ---")

    if not os.path.exists(file_path):
        print(f"Test file not found: {file_path}. Please create it.")
        return False

    parser_tool = DocumentParserTool()
    try:
        json_output_str = parser_tool._run(file_path)
        parsed_dict = json.loads(json_output_str)

        schema = load_document_schema()
        is_valid = validate_parsed_document(parsed_dict, schema)
        result_preview = json.dumps(parsed_dict, indent=2, ensure_ascii=False)
        max_chars = 1500
        if len(result_preview) > max_chars:
            result_preview = result_preview[:max_chars] + "..."
        print("--- Parsing Successful ---")
        print(result_preview)
        return is_valid
    except (FileNotFoundError, ValueError) as exc:
        print(f"--- Parsing Failed: {exc} ---")
        return False
    except Exception as exc:  # pylint: disable=broad-except
        print(f"--- An unexpected error occurred: {exc} ---")
        return False


def ensure_image_dir() -> None:
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)


def main() -> None:
    print("Starting docx parser tests...")
    ensure_image_dir()

    results: Dict[str, bool] = {}
    results["sample_paper_full.docx"] = run_single_test("sample_paper_full.docx")
    results["sample_paper_min.docx"] = run_single_test("sample_paper_min.docx")
    results["sample_paper_no_bib.docx"] = run_single_test("sample_paper_no_bib.docx")

    print("\n--- Test Summary ---")
    for file_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{file_name}: {status}")

    if all(results.values()):
        print("\nAll tests passed for docx parser!")
    else:
        print("\nSome tests failed for docx parser. Please review the logs above.")


if __name__ == "__main__":
    main()

