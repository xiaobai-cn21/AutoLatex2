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
    if args.case == "all":
        print("All LaTeX compiler tests passed.")


if __name__ == "__main__":
    main()

