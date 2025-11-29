"""封装 LaTeX 编译逻辑，支持 Docker 沙盒与本地回退。"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Optional

LATEX_TIMEOUT = int(os.getenv("AUTOTEX_LATEX_TIMEOUT", "120"))
DOCKER_IMAGE = os.getenv("AUTOTEX_LATEX_IMAGE", "autotex-compiler:latest")
USE_DOCKER = os.getenv("AUTOTEX_LATEX_USE_DOCKER", "1") not in {"0", "false", "False"}
LATEX_CMD = os.getenv("AUTOTEX_LATEX_CMD", "xelatex")
BIB_CMD = os.getenv("AUTOTEX_BIB_CMD", "bibtex")


@dataclass
class CompileResult:
    success: bool
    pdf_path: Optional[str] = None
    temp_dir: Optional[str] = None
    error_log: Optional[str] = None


def _command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def _setup_compile_env(latex_content: str, template_dir: str) -> str:
    temp_dir = tempfile.mkdtemp(prefix="autotex_latex_compile_")
    if not template_dir:
        raise ValueError("template_dir 不能为空。")
    if not os.path.isdir(template_dir):
        raise FileNotFoundError(f"模板目录不存在: {template_dir}")
    shutil.copytree(template_dir, temp_dir, dirs_exist_ok=True)

    main_tex_path = os.path.join(temp_dir, "main.tex")
    with open(main_tex_path, "w", encoding="utf-8") as tex_file:
        tex_file.write(latex_content)

    return temp_dir


def _needs_bibliography(latex_content: str) -> bool:
    return any(
        marker in latex_content
        for marker in ["\\bibliography{", "\\addbibresource", "\\printbibliography"]
    )


def _docker_command(host_dir: str, inner_command: List[str]) -> List[str]:
    container_dir = "/home/latexuser/compile_env"
    return [
        "docker",
        "run",
        "--rm",
        "--network=none",
        "--memory=1g",
        "--cpu-shares=512",
        "-v",
        f"{host_dir}:{container_dir}:rw",
        "-w",
        container_dir,
        DOCKER_IMAGE,
        *inner_command,
    ]


def _local_command(command: List[str]) -> List[str]:
    return command


def _run_command(command: List[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=LATEX_TIMEOUT,
        check=False,
    )


def _invoke_latex(command: List[str], temp_dir: str) -> subprocess.CompletedProcess:
    if USE_DOCKER:
        if not _command_exists("docker"):
            raise RuntimeError("Docker 未安装或不可用，无法使用沙盒进行编译。")
        exec_command = _docker_command(temp_dir, command)
    else:
        if not _command_exists(command[0]):
            raise RuntimeError(f"找不到命令 {command[0]}，请安装 TeX Live 或启用 Docker。")
        exec_command = _local_command(command)
    return _run_command(exec_command, temp_dir if not USE_DOCKER else None)


def compile_latex_to_pdf(latex_content: str, template_dir: str) -> CompileResult:
    temp_dir: Optional[str] = None
    try:
        temp_dir = _setup_compile_env(latex_content, template_dir)
        main_basename = "main.tex"
        latex_command = [LATEX_CMD, "-interaction=nonstopmode", "-halt-on-error", main_basename]


        def _read_log_file(temp_dir: str, basename: str = "main") -> str:
            """读取 LaTeX .log 文件中的错误信息。"""
            log_path = os.path.join(temp_dir, f"{basename}.log")
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                        log_content = log_file.read()
                        # 提取关键错误信息（通常以 ! 开头）
                        error_lines = [
                            line.strip()
                            for line in log_content.split("\n")
                            if line.strip().startswith("!")
                            or "Error:" in line
                            or "Fatal error" in line
                        ]
                        if error_lines:
                            return "\n".join(error_lines[-20:])  # 返回最后20行错误
                        return log_content[-5000:]  # 如果没有明显错误标记，返回最后5000字符
                except Exception:  # pylint: disable=broad-except
                    pass
            return ""

        # Run LaTeX up to three times for refs
        for _ in range(2):
            result = _invoke_latex(latex_command, temp_dir)
            if result.returncode != 0:
                return CompileResult(False, error_log=result.stdout + result.stderr)
                log_content = _read_log_file(temp_dir)
                error_msg = result.stdout + result.stderr
                if log_content:
                    error_msg = f"{error_msg}\n\n=== LaTeX Log 文件错误信息 ===\n{log_content}"
                return CompileResult(False, error_log=error_msg)

        if _needs_bibliography(latex_content):
            bib_command = [BIB_CMD, "main"]
            bib_result = _invoke_latex(bib_command, temp_dir)
            if bib_result.returncode != 0:
                return CompileResult(False, error_log=bib_result.stdout + bib_result.stderr)

        final_result = _invoke_latex(latex_command, temp_dir)
        if final_result.returncode != 0:
            return CompileResult(False, error_log=final_result.stdout + final_result.stderr)
            log_content = _read_log_file(temp_dir)
            error_msg = bib_result.stdout + bib_result.stderr
            if log_content:
                error_msg = f"{error_msg}\n\n=== LaTeX Log 文件错误信息 ===\n{log_content}"
            return CompileResult(False, error_log=error_msg)

        final_result = _invoke_latex(latex_command, temp_dir)
        if final_result.returncode != 0:
            log_content = _read_log_file(temp_dir)
            error_msg = final_result.stdout + final_result.stderr
            if log_content:
                error_msg = f"{error_msg}\n\n=== LaTeX Log 文件错误信息 ===\n{log_content}"
            return CompileResult(False, error_log=error_msg)

        pdf_path = os.path.join(temp_dir, "main.pdf")
        if not os.path.exists(pdf_path):
            return CompileResult(False, error_log="LaTeX 编译完成但未生成 PDF。")

        return CompileResult(True, pdf_path=pdf_path, temp_dir=temp_dir)
    except subprocess.TimeoutExpired:
        return CompileResult(False, error_log="LaTeX 编译超时。")
    except Exception as exc:  # pylint: disable=broad-except
        return CompileResult(False, error_log=f"LaTeX 编译失败: {exc}")


def cleanup_temp_dir(temp_dir: str) -> None:
    if temp_dir and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

