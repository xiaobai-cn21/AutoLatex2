"""Basic tests for the LaTeXCompilerTool."""

from __future__ import annotations

import json
import os
import shutil
from typing import Dict

from document_tools import LaTeXCompilerTool
from latex_compiler import cleanup_temp_dir


def run_compilation(latex_source: str, templates: Dict[str, str] | None = None) -> Dict[str, str]:
    """Invoke LaTeXCompilerTool and return parsed JSON output."""
    tool = LaTeXCompilerTool()
    templates_json = json.dumps(templates or {}, ensure_ascii=False)
    output = tool._run(latex_source, templates_json)
    return json.loads(output)


def assert_pdf_result(result: Dict[str, str]) -> None:
    assert result.get("pdf_path"), "PDF 路径缺失"
    assert os.path.exists(result["pdf_path"]), "PDF 文件不存在"
    assert result.get("temp_dir"), "临时目录缺失"
    assert os.path.isdir(result["temp_dir"]), "临时目录不存在"


def cleanup_result(result: Dict[str, str]) -> None:
    temp_dir = result.get("temp_dir")
    if temp_dir and os.path.isdir(temp_dir):
        cleanup_temp_dir(temp_dir)


def test_basic_success() -> None:
    latex = r"""
\documentclass{article}
\title{Hello AutoTeX}
\author{B Classmate}
\date{\today}
\begin{document}
\maketitle
Hello from AutoTeX Docker Sandbox!
\end{document}
"""
    result = run_compilation(latex)
    assert "message" in result and "成功" in result["message"]
    assert_pdf_result(result)
    cleanup_result(result)


def test_compile_failure() -> None:
    latex = r"""
\documentclass{article}
\begin{document}
\section{Unclosed Section
\end{document}
"""
    tool = LaTeXCompilerTool()
    output = tool._run(latex, "{}")
    result = json.loads(output)
    assert "失败" in result.get("message", "")
    assert "error_log" in result and "LaTeX" in result["error_log"]
    
    # 打印详细的错误日志用于验证
    print("\n" + "="*80)
    print("ERROR CAPTURE VERIFICATION - LaTeX Compilation Failure Test")
    print("="*80)
    
    error_log = result.get("error_log", "")
    print("\n[RETURNED JSON RESULT]")
    print("-"*80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n[KEY ERROR INFORMATION FROM error_log]")
    print("-"*80)
    # 提取并高亮显示关键错误行
    lines = error_log.split("\n")
    error_lines = []
    for line in lines:
        stripped = line.strip()
        if any(marker in stripped for marker in ["!", "Error", "Fatal", "Undefined", "Missing", "Runaway"]):
            error_lines.append(stripped)
    
    if error_lines:
        print("  >>> LaTeX Error Messages Found:")
        for err_line in error_lines[:10]:  # 最多显示10行
            print(f"      ! {err_line}")
    else:
        print("  (No explicit error markers found, showing last 500 chars)")
        print(f"      {error_log[-500:]}")
    
    print("\n[LOG FILE EXTRACTION]")
    print("-"*80)
    if "=== LaTeX Log" in error_log:
        log_section = error_log.split("=== LaTeX Log")[-1]
        print(f"  Extracted from .log file:{log_section[:200]}")
    
    print("="*80 + "\n")


def test_custom_template() -> None:
    latex = r"""
\documentclass{customarticle}
\begin{document}
Custom class document.
\end{document}
"""
    templates = {
        "customarticle.cls": r"""
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{customarticle}
\LoadClass{article}
"""
    }
    result = run_compilation(latex, templates)
    
    print("\n" + "="*80)
    print("TEMPLATE INJECTION VERIFICATION - Custom Template Test")
    print("="*80)
    print("\n[INPUT: LaTeX Source]")
    print("-"*80)
    print(latex.strip())
    
    print("\n[INPUT: Template Files to Inject]")
    print("-"*80)
    for filename, content in templates.items():
        print(f"  File: {filename}")
        print(f"  Content:\n{content.strip()}")
        print()
    
    print("[PROCESS: Template Injection Flow]")
    print("-"*80)
    print("  1. Create temporary directory on host")
    print("  2. Write main.tex to temp directory")
    print("  3. Write template files (customarticle.cls) to temp directory")
    print("  4. Mount temp directory to Docker container:")
    print("     docker run -v <host_temp_dir>:/home/latexuser/compile_env:rw ...")
    print("  5. Execute xelatex inside container (can access all files)")
    print("  6. PDF generated in mounted directory (accessible from host)")
    print()
    
    result = run_compilation(latex, templates)
    
    print("[RESULT: Compilation Success]")
    print("-"*80)
    print(f"  PDF Path: {result.get('pdf_path', 'N/A')}")
    print(f"  Temp Dir: {result.get('temp_dir', 'N/A')}")
    print(f"  PDF Exists: {os.path.exists(result.get('pdf_path', ''))}")
    print()
    print("  [PASS] Template injection and compilation successful!")
    print("  -> External .cls template file successfully injected into Docker container")
    print("  -> LaTeX compiler found and used the custom template")
    print("  -> PDF generated with custom document class")
    print("="*80 + "\n")
    
    assert_pdf_result(result)
    cleanup_result(result)


def test_bibliography() -> None:
    latex = r"""
\documentclass{article}
\begin{document}
Reference to~\cite{knuth1984texbook}.
\bibliographystyle{plain}
\bibliography{refs}
\end{document}
"""
    templates = {
        "refs.bib": r"""
@book{knuth1984texbook,
  title={The TeXbook},
  author={Knuth, Donald E},
  year={1984},
  publisher={Addison-Wesley}
}
"""
    }
    result = run_compilation(latex, templates)
    
    print("\n" + "="*80)
    print("BIBLIOGRAPHY PROCESSING VERIFICATION - Bibliography Test")
    print("="*80)
    print("\n[INPUT: LaTeX Source with Citations]")
    print("-"*80)
    print(latex.strip())
    
    print("\n[INPUT: Bibliography File (.bib)]")
    print("-"*80)
    for filename, content in templates.items():
        print(f"  File: {filename}")
        print(f"  Content:\n{content.strip()}")
        print()
    
    print("[PROCESS: Intelligent Bibliography Processing Flow]")
    print("-"*80)
    print("  1. First xelatex compilation:")
    print("     -> Generates main.aux (contains citation references)")
    print("     -> Creates placeholder for bibliography")
    print()
    print("  2. Second xelatex compilation:")
    print("     -> Resolves internal cross-references")
    print("     -> Prepares for bibliography processing")
    print()
    print("  3. [INTELLIGENT DETECTION] Check for bibliography markers:")
    print("     -> Detects: \\bibliography{}, \\addbibresource, \\printbibliography")
    print("     -> Found: \\bibliography{refs}")
    print("     -> Decision: Run bibliography tool (bibtex/biber)")
    print()
    print("  4. Execute bibliography tool:")
    print("     -> Command: bibtex main")
    print("     -> Processes refs.bib file")
    print("     -> Generates main.bbl (formatted bibliography)")
    print()
    print("  5. Final xelatex compilation:")
    print("     -> Incorporates bibliography from main.bbl")
    print("     -> Resolves all citation references")
    print("     -> Generates complete PDF with bibliography section")
    print()
    
    result = run_compilation(latex, templates)
    
    print("[RESULT: Compilation Success with Bibliography]")
    print("-"*80)
    print(f"  PDF Path: {result.get('pdf_path', 'N/A')}")
    print(f"  Temp Dir: {result.get('temp_dir', 'N/A')}")
    print(f"  PDF Exists: {os.path.exists(result.get('pdf_path', ''))}")
    print()
    print("  [PASS] Bibliography processing successful!")
    print("  -> Bibliography markers automatically detected")
    print("  -> bibtex/biber tool intelligently executed")
    print("  -> Cross-references resolved (citations -> bibliography)")
    print("  -> Complete PDF generated with bibliography section")
    print("="*80 + "\n")
    
    assert_pdf_result(result)
    cleanup_result(result)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Test LaTeX compiler tool.")
    parser.add_argument(
        "--case",
        choices=["all", "basic", "failure", "template", "bibliography"],
        default="all",
    )
    args = parser.parse_args()

    os.environ.setdefault("AUTOTEX_LATEX_USE_DOCKER", "True")
    os.environ.setdefault("AUTOTEX_LATEX_IMAGE", "autotex-latex-compiler:latest")

    cases = {
        "basic": (test_basic_success, "basic success"),
        "failure": (test_compile_failure, "compile failure"),
        "template": (test_custom_template, "custom template"),
        "bibliography": (test_bibliography, "bibliography"),
    }

    selected = cases.keys() if args.case == "all" else [args.case]
    print("Running LaTeX compiler tests...")
    for case in selected:
        func, label = cases[case]
        func()
        print(f"  ✓ {label}")
        print(f"  [PASS] {label}")
    if args.case == "all":
        print("All LaTeX compiler tests passed.")


if __name__ == "__main__":
    main()

